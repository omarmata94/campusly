from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from io import BytesIO
from typing import Optional

import pandas as pd
from sqlalchemy import and_, case, func, select

from database.db import get_session
from database.models import Asistencia, Docente
from services.time_utils import today_local


@dataclass
class AttendanceFilters:
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    docente_id: Optional[int] = None
    departamento: Optional[str] = None
    estatus: Optional[str] = None
    anio: Optional[int] = None
    cuatrimestre: Optional[int] = None


class ReportService:
    @staticmethod
    def _base_query():
        return (
            select(
                Asistencia.id.label("id"),
                Asistencia.fecha.label("fecha"),
                Asistencia.anio.label("anio"),
                Asistencia.cuatrimestre.label("cuatrimestre"),
                Asistencia.hora.label("hora"),
                Asistencia.estatus.label("estatus"),
                Asistencia.turno.label("turno"),
                Asistencia.numero_hora.label("numero_hora"),
                Asistencia.salon.label("salon"),
                Asistencia.grupo.label("grupo"),
                Asistencia.usuario_registro.label("usuario_registro"),
                Docente.id.label("docente_id"),
                Docente.numero_empleado.label("numero_empleado"),
                Docente.nombre.label("nombre"),
                Docente.apellidos.label("apellidos"),
                Docente.departamento.label("departamento"),
                Docente.puesto.label("puesto"),
                Docente.horario_entrada.label("horario_entrada"),
                Docente.horario_salida.label("horario_salida"),
            )
            .join(Docente, Asistencia.docente_id == Docente.id)
        )

    @staticmethod
    def fetch_attendances(filters: AttendanceFilters) -> pd.DataFrame:
        query = ReportService._base_query()
        conditions = []

        if filters.fecha_inicio:
            conditions.append(Asistencia.fecha >= filters.fecha_inicio)
        if filters.fecha_fin:
            conditions.append(Asistencia.fecha <= filters.fecha_fin)
        if filters.docente_id:
            conditions.append(Asistencia.docente_id == filters.docente_id)
        if filters.departamento:
            conditions.append(Docente.departamento == filters.departamento)
        if filters.estatus:
            conditions.append(Asistencia.estatus == filters.estatus)
        if filters.anio:
            conditions.append(Asistencia.anio == filters.anio)
        if filters.cuatrimestre:
            conditions.append(Asistencia.cuatrimestre == filters.cuatrimestre)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(Asistencia.fecha.desc(), Asistencia.hora.desc())

        with get_session() as session:
            rows = session.execute(query).mappings().all()

        df = pd.DataFrame(rows)
        if not df.empty:
            df["docente"] = df["nombre"].astype(str) + " " + df["apellidos"].astype(str)
            df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
            df["hora"] = df["hora"].astype(str)
        return df

    @staticmethod
    def available_years() -> list[int]:
        with get_session() as session:
            rows = session.execute(
                select(Asistencia.anio).where(Asistencia.anio.is_not(None)).distinct().order_by(Asistencia.anio.desc())
            ).scalars().all()
        return [int(y) for y in rows if y is not None]

    @staticmethod
    def latest_records(limit: int = 8) -> pd.DataFrame:
        with get_session() as session:
            query = (
                select(
                    Asistencia.fecha.label("fecha"),
                    Asistencia.hora.label("hora"),
                    Asistencia.estatus.label("estatus"),
                    Docente.numero_empleado.label("numero_empleado"),
                    Docente.nombre.label("nombre"),
                    Docente.apellidos.label("apellidos"),
                    Docente.departamento.label("departamento"),
                )
                .join(Docente, Asistencia.docente_id == Docente.id)
                .order_by(Asistencia.fecha.desc(), Asistencia.hora.desc())
                .limit(limit)
            )
            rows = session.execute(query).mappings().all()

        df = pd.DataFrame(rows)
        if not df.empty:
            df["docente"] = df["nombre"].astype(str) + " " + df["apellidos"].astype(str)
            df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
            df["hora"] = df["hora"].astype(str)
        return df

    @staticmethod
    def summary_totals(reference_date: Optional[date] = None) -> dict[str, int]:
        reference_date = reference_date or today_local()
        with get_session() as session:
            total_docentes = session.scalar(select(func.count(Docente.id)).where(Docente.activo.is_(True))) or 0
            presentes = session.scalar(
                select(func.count(Asistencia.id))
                .join(Docente, Asistencia.docente_id == Docente.id)
                .where(Asistencia.fecha == reference_date, Asistencia.estatus.in_(["Puntual", "Retardo"]))
            ) or 0
            retardos = session.scalar(
                select(func.count(Asistencia.id))
                .where(Asistencia.fecha == reference_date, Asistencia.estatus == "Retardo")
            ) or 0
            ausentes = max(total_docentes - presentes, 0)

        return {
            "total_docentes": int(total_docentes),
            "presentes": int(presentes),
            "retardos": int(retardos),
            "ausentes": int(ausentes),
        }

    @staticmethod
    def daily_summary(start: date, end: date) -> pd.DataFrame:
        with get_session() as session:
            query = (
                select(
                    Asistencia.fecha.label("fecha"),
                    func.count(Asistencia.id).label("total"),
                    func.sum(case((Asistencia.estatus == "Puntual", 1), else_=0)).label("puntual"),
                    func.sum(case((Asistencia.estatus == "Retardo", 1), else_=0)).label("retardo"),
                    func.sum(case((Asistencia.estatus == "Falta", 1), else_=0)).label("falta"),
                )
                .where(Asistencia.fecha.between(start, end))
                .group_by(Asistencia.fecha)
                .order_by(Asistencia.fecha)
            )
            rows = session.execute(query).mappings().all()

        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame(columns=["fecha", "total", "puntual", "retardo", "falta"])
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
        return df

    @staticmethod
    def department_summary(start: date, end: date) -> pd.DataFrame:
        with get_session() as session:
            query = (
                select(
                    Docente.departamento.label("departamento"),
                    func.count(Asistencia.id).label("total"),
                )
                .join(Docente, Asistencia.docente_id == Docente.id)
                .where(Asistencia.fecha.between(start, end))
                .group_by(Docente.departamento)
                .order_by(func.count(Asistencia.id).desc())
            )
            rows = session.execute(query).mappings().all()

        return pd.DataFrame(rows)

    @staticmethod
    def monthly_trend(year: int) -> pd.DataFrame:
        with get_session() as session:
            query = (
                select(
                    func.strftime("%m", Asistencia.fecha).label("mes"),
                    func.count(Asistencia.id).label("total"),
                )
                .where(func.strftime("%Y", Asistencia.fecha) == str(year))
                .group_by(func.strftime("%m", Asistencia.fecha))
                .order_by(func.strftime("%m", Asistencia.fecha))
            )
            rows = session.execute(query).mappings().all()

        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame(columns=["mes", "total"])
        df["mes"] = df["mes"].astype(int)
        return df

    @staticmethod
    def export_csv(df: pd.DataFrame) -> bytes:
        return df.to_csv(index=False).encode("utf-8")

    @staticmethod
    def export_excel(df: pd.DataFrame) -> bytes:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Asistencias")
        return buffer.getvalue()

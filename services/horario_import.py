from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from typing import Optional

import pandas as pd
from sqlalchemy import select

from database.db import get_session
from database.models import Docente, DocenteHoraClase, HoraClase, Turno


@dataclass
class ImportResult:
    success: bool
    message: str
    imported_count: int = 0
    skipped_count: int = 0
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class HorarioImportService:
    """Servicio para importar horarios de docentes desde archivos."""

    @staticmethod
    def _has_schedule_conflict(
        session, docente_id: int, turno_id: int, numero_hora: int, dia_semana: int
    ) -> bool:
        """Verifica si el docente ya tiene una clase en ese horario/día."""
        existing = session.scalar(
            select(DocenteHoraClase).where(
                DocenteHoraClase.docente_id == docente_id,
                DocenteHoraClase.turno_id == turno_id,
                DocenteHoraClase.numero_hora == numero_hora,
                DocenteHoraClase.dia_semana == dia_semana,
            )
        )
        return existing is not None

    @staticmethod
    def validate_file(file_content: bytes) -> tuple[bool, str]:
        """Valida que el archivo sea CSV válido."""
        try:
            df = pd.read_csv(StringIO(file_content.decode("utf-8")))
            required_cols = {
                "numero_empleado",
                "turno",
                "dia_semana",
                "numero_hora",
                "salon",
                "grupo",
            }
            if not required_cols.issubset(set(df.columns)):
                missing = required_cols - set(df.columns)
                return False, f"Faltan columnas: {', '.join(missing)}"
            return True, "Archivo válido"
        except Exception as e:
            return False, f"Error al leer archivo: {str(e)}"

    @staticmethod
    def parse_csv(file_content: bytes) -> pd.DataFrame:
        """Parsea un archivo CSV de horarios."""
        return pd.read_csv(StringIO(file_content.decode("utf-8")))

    @staticmethod
    def import_horarios(df: pd.DataFrame) -> ImportResult:
        """Importa horarios desde DataFrame y los guarda en la BD."""
        imported_count = 0
        skipped_count = 0
        errors = []

        with get_session() as session:
            # Mapear día de semana a número
            dia_map = {
                "lunes": 0,
                "martes": 1,
                "miércoles": 2,
                "miercoles": 2,
                "jueves": 3,
                "viernes": 4,
            }

            for _, row in df.iterrows():
                try:
                    numero_empleado = str(row["numero_empleado"]).strip()
                    turno_nombre = str(row["turno"]).strip()
                    dia_semana_str = str(row["dia_semana"]).lower().strip()
                    numero_hora = int(row["numero_hora"])
                    salon = str(row["salon"]).strip()
                    grupo = str(row["grupo"]).strip()

                    # Validar docente
                    docente = session.scalar(
                        select(Docente).where(Docente.numero_empleado == numero_empleado)
                    )
                    if not docente:
                        errors.append(f"Docente {numero_empleado} no encontrado")
                        skipped_count += 1
                        continue

                    # Validar turno
                    turno = session.scalar(select(Turno).where(Turno.nombre == turno_nombre))
                    if not turno:
                        errors.append(f"Turno {turno_nombre} no encontrado")
                        skipped_count += 1
                        continue

                    # Validar día de semana
                    if dia_semana_str not in dia_map:
                        errors.append(f"Día de semana inválido: {dia_semana_str}")
                        skipped_count += 1
                        continue

                    dia_numero = dia_map[dia_semana_str]

                    # Obtener hora clase
                    hora_clase = session.scalar(
                        select(HoraClase).where(
                            HoraClase.turno_id == turno.id,
                            HoraClase.numero == numero_hora,
                        )
                    )
                    if not hora_clase:
                        errors.append(
                            f"Hora clase {numero_hora} no encontrada para turno {turno_nombre}"
                        )
                        skipped_count += 1
                        continue

                    # Verificar si ya existe exactamente
                    existing = session.scalar(
                        select(DocenteHoraClase).where(
                            DocenteHoraClase.docente_id == docente.id,
                            DocenteHoraClase.turno_id == turno.id,
                            DocenteHoraClase.hora_clase_id == hora_clase.id,
                            DocenteHoraClase.dia_semana == dia_numero,
                            DocenteHoraClase.salon == salon,
                        )
                    )

                    if existing:
                        skipped_count += 1
                        continue

                    # Verificar conflictos horarios (misma hora/día)
                    if HorarioImportService._has_schedule_conflict(
                        session, docente.id, turno.id, numero_hora, dia_numero
                    ):
                        errors.append(
                            f"Conflicto: {docente.nombre} ya tiene clase en Hora {numero_hora} "
                            f"el {['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'][dia_numero]}"
                        )
                        skipped_count += 1
                        continue

                    # Crear asignación
                    assignment = DocenteHoraClase(
                        docente_id=docente.id,
                        turno_id=turno.id,
                        hora_clase_id=hora_clase.id,
                        numero_hora=numero_hora,
                        dia_semana=dia_numero,
                        salon=salon,
                        grupo=grupo,
                    )
                    session.add(assignment)
                    imported_count += 1

                except Exception as e:
                    errors.append(f"Error en fila: {str(e)}")
                    skipped_count += 1

            session.commit()

        return ImportResult(
            success=imported_count > 0,
            message=f"Importación completada: {imported_count} registros importados",
            imported_count=imported_count,
            skipped_count=skipped_count,
            errors=errors,
        )

    @staticmethod
    def clear_docente_horarios(numero_empleado: str) -> bool:
        """Limpia todos los horarios de un docente (para reimportar)."""
        from sqlalchemy import delete

        with get_session() as session:
            docente = session.scalar(
                select(Docente).where(Docente.numero_empleado == numero_empleado)
            )
            if not docente:
                return False

            session.execute(delete(DocenteHoraClase).where(DocenteHoraClase.docente_id == docente.id))
            session.commit()
            return True

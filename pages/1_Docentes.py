from __future__ import annotations

from datetime import datetime, time
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database.db import get_session, init_db
from database.models import Docente
from services.qr_generator import BadgeGenerator, QRGenerator
from services.ui import APP_NAME, configure_page, logout_button, page_hero, require_login, render_sidebar, styled_attendance_table


ROOT_DIR = Path(__file__).resolve().parents[1]
UPLOADS_DIR = ROOT_DIR / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

DEPARTAMENTO_FIJO = "Academia"
PUESTOS_OPCIONES = [
    "Profesor de Tiempo Completo",
    "Profesor por Asignatura",
    "Profesor por Honorarios",
]


def _parse_time(value: str, fallback: time) -> time:
    try:
        return datetime.strptime(value, "%H:%M").time()
    except Exception:
        return fallback


def _join_apellidos(apellido_paterno: str, apellido_materno: str) -> str:
    return " ".join([part for part in [apellido_paterno.strip(), apellido_materno.strip()] if part]).strip()


def _docentes_dataframe() -> pd.DataFrame:
    sort_apellido_paterno = getattr(Docente, "apellido_paterno", None)
    sort_apellido_materno = getattr(Docente, "apellido_materno", None)
    order_columns = [Docente.nombre]
    if sort_apellido_paterno is not None:
        order_columns.insert(0, sort_apellido_paterno)
    if sort_apellido_materno is not None:
        order_columns.insert(1 if sort_apellido_paterno is not None else 0, sort_apellido_materno)

    with get_session() as session:
        rows = session.execute(select(Docente).order_by(*order_columns)).scalars().all()
        records = [
            {
                "id": docente.id,
                "numero_empleado": docente.numero_empleado,
                "nombre": docente.nombre,
                "apellido_paterno": getattr(docente, "apellido_paterno", ""),
                "apellido_materno": getattr(docente, "apellido_materno", ""),
                "apellidos": _join_apellidos(
                    getattr(docente, "apellido_paterno", ""),
                    getattr(docente, "apellido_materno", ""),
                )
                or docente.apellidos,
                "departamento": docente.departamento or DEPARTAMENTO_FIJO,
                "puesto": docente.puesto,
                "horario_entrada": docente.horario_entrada,
                "horario_salida": docente.horario_salida,
                "qr_uuid": docente.qr_uuid,
                "activo": docente.activo,
            }
            for docente in rows
        ]
    df = pd.DataFrame(records)
    if not df.empty:
        df["nombre_completo"] = df["nombre"] + " " + df["apellidos"]
    return df


def _load_docente(docente_id: int) -> dict | None:
    with get_session() as session:
        docente = session.get(Docente, docente_id)
        if docente is None:
            return None
        apellido_paterno = getattr(docente, "apellido_paterno", "")
        apellido_materno = getattr(docente, "apellido_materno", "")
        return {
            "id": docente.id,
            "numero_empleado": docente.numero_empleado,
            "nombre": docente.nombre,
            "apellido_paterno": apellido_paterno,
            "apellido_materno": apellido_materno,
            "apellidos": _join_apellidos(apellido_paterno, apellido_materno) or docente.apellidos,
            "departamento": docente.departamento or DEPARTAMENTO_FIJO,
            "puesto": docente.puesto,
            "horario_entrada": docente.horario_entrada,
            "horario_salida": docente.horario_salida,
            "qr_uuid": docente.qr_uuid,
            "activo": bool(docente.activo),
        }


def _save_docente(data: dict, docente_id: int | None = None) -> None:
    with get_session() as session:
        numero_empleado = data.get("numero_empleado", "").strip()
        puesto = data.get("puesto", "").strip()

        if puesto not in PUESTOS_OPCIONES:
            raise ValueError("Selecciona un puesto válido.")

        existing = session.scalar(select(Docente).where(Docente.numero_empleado == numero_empleado))
        if existing and (docente_id is None or existing.id != docente_id):
            raise ValueError("Ya existe un docente con ese número de empleado.")

        apellido_paterno = data.get("apellido_paterno", "").strip()
        apellido_materno = data.get("apellido_materno", "").strip()
        apellidos = _join_apellidos(apellido_paterno, apellido_materno)

        if not apellido_paterno or not apellido_materno:
            raise ValueError("Debes capturar apellido paterno y apellido materno.")

        payload = dict(data)
        payload["numero_empleado"] = numero_empleado
        payload["departamento"] = DEPARTAMENTO_FIJO
        payload["puesto"] = puesto
        payload.pop("apellido_paterno", None)
        payload.pop("apellido_materno", None)
        payload["apellidos"] = apellidos

        if hasattr(Docente, "apellido_paterno"):
            payload["apellido_paterno"] = apellido_paterno
        if hasattr(Docente, "apellido_materno"):
            payload["apellido_materno"] = apellido_materno

        if docente_id is None:
            qr_uuid = QRGenerator.generate_uuid()
            activo = bool(payload.pop("activo", True))
            docente = Docente(qr_uuid=qr_uuid, activo=activo, **payload)
            session.add(docente)
            session.flush()
            QRGenerator.save_qr(docente.qr_uuid, docente.qr_uuid)
        else:
            docente = session.get(Docente, docente_id)
            if docente is None:
                raise ValueError("El docente no existe")
            for key, value in payload.items():
                setattr(docente, key, value)
            docente.activo = bool(data.get("activo", docente.activo))
            session.flush()
            if not (ROOT_DIR / "assets" / "qrs" / f"{docente.qr_uuid}.png").exists():
                QRGenerator.save_qr(docente.qr_uuid, docente.qr_uuid)


def _delete_docente(docente_id: int) -> None:
    with get_session() as session:
        docente = session.get(Docente, docente_id)
        if docente is None:
            raise ValueError("El docente no existe")
        docente.activo = False
        session.flush()


def main() -> None:
    init_db()
    configure_page(f"{APP_NAME} | Docentes")
    user = require_login(["Administrador"])

    render_sidebar(user)
    logout_button()

    page_hero("Docentes", "CRUD completo, búsqueda y generación de gafetes institucionales.")

    tabs = st.tabs(["Registrar", "Editar", "Eliminar", "Buscar", "Listado", "Gafete PDF"])

    with tabs[0]:
        st.subheader("Agregar docente")
        with st.form("form_create_docente", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            numero_empleado = c1.text_input("Número de empleado")
            nombre = c2.text_input("Nombre")
            apellido_paterno = c3.text_input("Apellido paterno")
            apellido_materno = c4.text_input("Apellido materno")
            d1, d2, d3 = st.columns(3)
            d1.text_input("Departamento", value=DEPARTAMENTO_FIJO, disabled=True)
            puesto = d2.selectbox("Puesto", PUESTOS_OPCIONES, index=0)
            horario_entrada_time = d3.time_input("Horario de entrada (24h)", value=time(7, 0), step=60)
            s1, s2 = st.columns(2)
            horario_salida_time = s1.time_input("Horario de salida (24h)", value=time(14, 0), step=60)
            activo = s2.checkbox("Activo", value=True)
            submitted = st.form_submit_button("Guardar docente", use_container_width=True)
        if submitted:
            if not all([numero_empleado, nombre, apellido_paterno, apellido_materno, puesto]):
                st.error("Completa todos los campos.")
            else:
                try:
                    _save_docente(
                        {
                            "numero_empleado": numero_empleado.strip(),
                            "nombre": nombre.strip(),
                            "apellido_paterno": apellido_paterno.strip(),
                            "apellido_materno": apellido_materno.strip(),
                            "puesto": puesto,
                            "horario_entrada": horario_entrada_time.strftime("%H:%M"),
                            "horario_salida": horario_salida_time.strftime("%H:%M"),
                            "activo": activo,
                        }
                    )
                    st.success("Docente registrado y QR generado.")
                    st.rerun()
                except Exception as exc:
                    if isinstance(exc, IntegrityError):
                        st.error("El número de empleado ya está registrado.")
                    else:
                        st.error(str(exc))

    with tabs[1]:
        st.subheader("Editar docente")
        df = _docentes_dataframe()
        if df.empty:
            st.info("No hay docentes registrados.")
        else:
            options = {f"{row.numero_empleado} - {row.nombre_completo}": int(row.id) for _, row in df.iterrows()}
            selected = st.selectbox("Selecciona un docente", list(options.keys()), key="edit_docente_select")
            docente = _load_docente(options[selected])
            if docente:
                with st.form("form_edit_docente"):
                    c1, c2, c3, c4 = st.columns(4)
                    numero_empleado = c1.text_input("Número de empleado", value=docente["numero_empleado"])
                    nombre = c2.text_input("Nombre", value=docente["nombre"])
                    apellido_paterno = c3.text_input("Apellido paterno", value=docente["apellido_paterno"])
                    apellido_materno = c4.text_input("Apellido materno", value=docente["apellido_materno"])
                    d1, d2, d3 = st.columns(3)
                    d1.text_input("Departamento", value=DEPARTAMENTO_FIJO, disabled=True)
                    puesto_index = PUESTOS_OPCIONES.index(docente["puesto"]) if docente["puesto"] in PUESTOS_OPCIONES else 0
                    puesto = d2.selectbox("Puesto", PUESTOS_OPCIONES, index=puesto_index)
                    horario_entrada_time = d3.time_input(
                        "Horario de entrada (24h)",
                        value=_parse_time(docente["horario_entrada"], time(7, 0)),
                        step=60,
                    )
                    s1, s2 = st.columns(2)
                    horario_salida_time = s1.time_input(
                        "Horario de salida (24h)",
                        value=_parse_time(docente["horario_salida"], time(14, 0)),
                        step=60,
                    )
                    activo = s2.checkbox("Activo", value=bool(docente["activo"]))
                    submitted = st.form_submit_button("Actualizar docente", use_container_width=True)
                if submitted:
                    try:
                        _save_docente(
                            {
                                "numero_empleado": numero_empleado.strip(),
                                "nombre": nombre.strip(),
                                "apellido_paterno": apellido_paterno.strip(),
                                "apellido_materno": apellido_materno.strip(),
                                "puesto": puesto,
                                "horario_entrada": horario_entrada_time.strftime("%H:%M"),
                                "horario_salida": horario_salida_time.strftime("%H:%M"),
                                "activo": activo,
                            },
                            docente_id=docente["id"],
                        )
                        st.success("Docente actualizado.")
                        st.rerun()
                    except Exception as exc:
                        if isinstance(exc, IntegrityError):
                            st.error("El número de empleado ya está registrado.")
                        else:
                            st.error(str(exc))

    with tabs[2]:
        st.subheader("Eliminar docente")
        df = _docentes_dataframe()
        if df.empty:
            st.info("No hay docentes registrados.")
        else:
            options = {f"{row.numero_empleado} - {row.nombre_completo}": int(row.id) for _, row in df.iterrows()}
            selected = st.selectbox("Docente a eliminar", list(options.keys()), key="delete_docente_select")
            docente = _load_docente(options[selected])
            if docente:
                st.warning("Esta acción desactiva al docente para conservar el historial de asistencias.")
                if st.button("Eliminar / desactivar", type="primary"):
                    try:
                        _delete_docente(docente["id"])
                        st.success("Docente desactivado.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

    with tabs[3]:
        st.subheader("Buscar docente")
        query = st.text_input("Buscar por nombre, apellidos, número o puesto")
        df = _docentes_dataframe()
        if not df.empty and query:
            mask = (
                df["numero_empleado"].astype(str).str.contains(query, case=False, na=False)
                | df["nombre"].astype(str).str.contains(query, case=False, na=False)
                | df["apellido_paterno"].astype(str).str.contains(query, case=False, na=False)
                | df["apellido_materno"].astype(str).str.contains(query, case=False, na=False)
                | df["puesto"].astype(str).str.contains(query, case=False, na=False)
            )
            st.dataframe(styled_attendance_table(df.loc[mask].drop(columns=["id"])), use_container_width=True)
        elif query:
            st.info("Sin coincidencias.")

    with tabs[4]:
        st.subheader("Listado de docentes")
        df = _docentes_dataframe()
        if df.empty:
            st.info("No hay docentes registrados.")
        else:
            st.dataframe(df.drop(columns=["id"]).style.hide(axis="index"), use_container_width=True)

    with tabs[5]:
        st.subheader("Generación de gafete institucional")
        df = _docentes_dataframe()
        if df.empty:
            st.info("Registra docentes antes de generar gafetes.")
        else:
            options = {f"{row.numero_empleado} - {row.nombre_completo}": int(row.id) for _, row in df.iterrows()}
            selected = st.selectbox("Selecciona un docente", list(options.keys()), key="badge_docente_select")
            docente = _load_docente(options[selected])
            if docente:
                photo_file = st.file_uploader("Fotografía del docente", type=["png", "jpg", "jpeg"], key="photo_upload")
                logo_file = st.file_uploader("Logo institucional", type=["png", "jpg", "jpeg"], key="logo_upload")
                if st.button("Generar gafete en PDF", use_container_width=True):
                    photo_path = None
                    logo_path = None
                    if photo_file is not None:
                        photo_path = UPLOADS_DIR / f"photo_{docente['qr_uuid']}_{photo_file.name}"
                        photo_path.write_bytes(photo_file.getbuffer())
                    if logo_file is not None:
                        logo_path = UPLOADS_DIR / f"logo_{docente['qr_uuid']}_{logo_file.name}"
                        logo_path.write_bytes(logo_file.getbuffer())
                    try:
                        asset = BadgeGenerator.generate_badge_pdf(
                            full_name=f"{docente['nombre']} {docente['apellido_paterno']} {docente['apellido_materno']}",
                            employee_number=docente["numero_empleado"],
                            department=docente["departamento"],
                            qr_uuid=docente["qr_uuid"],
                            photo_path=photo_path,
                            logo_path=logo_path,
                        )
                        st.success("Gafete generado correctamente.")
                        st.download_button(
                            "Descargar PDF",
                            data=asset.pdf_path.read_bytes(),
                            file_name=f"gafete_{docente['numero_empleado']}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception as exc:
                        st.error(str(exc))


if __name__ == "__main__":
    main()

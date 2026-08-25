from __future__ import annotations

import io
from datetime import datetime, time
from pathlib import Path
import re
import zipfile

import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database.db import get_session, init_db
from database.models import Docente, DocenteHoraClase, Turno
from services.time_utils import current_academic_period
from services.qr_generator import BadgeGenerator, QRGenerator
from services.ui import APP_NAME, configure_page, logout_button, page_hero, require_login, render_sidebar, styled_attendance_table


ROOT_DIR = Path(__file__).resolve().parents[1]
UPLOADS_DIR = ROOT_DIR / "data" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

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


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())


def _load_print_logo() -> Image.Image | None:
    """Carga el logo institucional para la tarjeta imprimible si existe."""
    candidates = [
        ROOT_DIR / "assets" / "logo_utc.png",
        ROOT_DIR / "assets" / "logo_utc.jpg",
    ]
    for path in candidates:
        if path.exists():
            try:
                return Image.open(path).convert("RGBA")
            except Exception:
                continue
    return None


def _build_identified_qr_png(qr_path: Path, numero_empleado: str, nombre_completo: str, turno_nombre: str) -> bytes:
    """Genera una imagen QR lista para impresión con identificación textual."""
    qr_img = Image.open(qr_path).convert("RGB")
    qr_size = 400
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.NEAREST)

    card_w = 620
    card_h = 720
    canvas = Image.new("RGB", (card_w, card_h), "#fff7ed")

    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    title = "ASISTENCIA DOCENTE"
    subtitle = "Codigo QR"

    # Tarjeta principal.
    draw.rounded_rectangle((20, 20, card_w - 20, card_h - 20), radius=24, fill="white", outline="#f97316", width=3)

    # Encabezado.
    draw.rectangle((40, 42, card_w - 40, 112), fill="#f97316")
    title_w = draw.textlength(title, font=font)
    subtitle_w = draw.textlength(subtitle, font=font)
    draw.text(((card_w - title_w) / 2, 58), title, fill="white", font=font)
    draw.text(((card_w - subtitle_w) / 2, 82), subtitle, fill="#ffedd5", font=font)

    logo_img = _load_print_logo()
    if logo_img is not None:
        logo_max_w = 130
        logo_ratio = logo_img.height / max(logo_img.width, 1)
        logo_w = min(logo_max_w, logo_img.width)
        logo_h = int(logo_w * logo_ratio)
        logo_resized = logo_img.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
        logo_x = card_w - 46 - logo_w
        logo_y = 122
        canvas.paste(logo_resized, (logo_x, logo_y), logo_resized)

    # Marco de QR.
    qr_frame_x1 = (card_w - qr_size) // 2 - 14
    qr_frame_y1 = 154
    qr_frame_x2 = qr_frame_x1 + qr_size + 28
    qr_frame_y2 = qr_frame_y1 + qr_size + 28
    draw.rounded_rectangle((qr_frame_x1, qr_frame_y1, qr_frame_x2, qr_frame_y2), radius=18, outline="#14b8a6", width=3)
    canvas.paste(qr_img, (qr_frame_x1 + 14, qr_frame_y1 + 14))

    # Nombre centrado con corte en 2 lineas.
    label = " ".join((nombre_completo or "").split())
    words = label.split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= card_w - 100:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
        if len(lines) == 1 and current and draw.textlength(current, font=font) > card_w - 100:
            lines.append(current)
            current = ""
            break
    if current:
        lines.append(current)
    lines = lines[:2] or ["Docente"]

    text_y = qr_frame_y2 + 34
    for line in lines:
        line_w = draw.textlength(line, font=font)
        draw.text(((card_w - line_w) / 2, text_y), line, fill="#0f172a", font=font)
        text_y += 24

    # Pie de corte.
    draw.line((56, card_h - 74, card_w - 56, card_h - 74), fill="#fde68a", width=1)
    foot = "Imprimir y colocar en gafete"
    foot_w = draw.textlength(foot, font=font)
    draw.text(((card_w - foot_w) / 2, card_h - 58), foot, fill="#0f766e", font=font)

    output = io.BytesIO()
    canvas.save(output, format="PNG")
    return output.getvalue()


def _build_turno_qr_zip(turno_nombre: str) -> dict:
    """Genera un ZIP con los QRs de docentes activos asignados a un turno."""
    anio, cuatrimestre = current_academic_period()
    with get_session() as session:
        docentes = session.execute(
            select(Docente)
            .join(DocenteHoraClase, DocenteHoraClase.docente_id == Docente.id)
            .join(Turno, Turno.id == DocenteHoraClase.turno_id)
            .where(
                Turno.nombre == turno_nombre,
                Docente.activo.is_(True),
                DocenteHoraClase.anio == anio,
                DocenteHoraClase.cuatrimestre == cuatrimestre,
            )
            .distinct()
            .order_by(Docente.nombre, Docente.apellidos)
        ).scalars().all()

    if not docentes:
        return {"zip_bytes": b"", "included": 0, "detected": 0, "errors": ["No hay docentes activos en este turno."]}

    buffer = io.BytesIO()
    errors: list[str] = []
    included = 0

    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for docente in docentes:
            qr_path = ROOT_DIR / "assets" / "qrs" / f"{docente.qr_uuid}.png"
            if not qr_path.exists():
                try:
                    QRGenerator.save_qr(docente.qr_uuid, docente.qr_uuid)
                except Exception as exc:
                    errors.append(f"{docente.numero_empleado}: no se pudo generar QR ({exc})")

            if not qr_path.exists():
                errors.append(f"{docente.numero_empleado}: QR no encontrado")
                continue

            full_name = f"{docente.nombre} {docente.apellidos}".strip()
            file_name = _safe_filename(f"QR_{docente.numero_empleado}_{full_name}_{turno_nombre}.png")
            try:
                printable_png = _build_identified_qr_png(
                    qr_path=qr_path,
                    numero_empleado=docente.numero_empleado,
                    nombre_completo=full_name,
                    turno_nombre=turno_nombre,
                )
                archive.writestr(file_name, printable_png)
                included += 1
            except Exception as exc:
                errors.append(f"{docente.numero_empleado}: no se pudo etiquetar QR ({exc})")

    return {
        "zip_bytes": buffer.getvalue(),
        "included": included,
        "detected": len(docentes),
        "errors": errors,
    }


def main() -> None:
    init_db()
    configure_page(f"{APP_NAME} | Docentes")
    user = require_login(["Administrador"])

    render_sidebar(user)
    logout_button()

    page_hero("Docentes", "CRUD completo, búsqueda y generación de gafetes institucionales.")

    tabs = st.tabs(["Registrar", "Editar", "Eliminar", "Buscar", "Listado", "Gafete PDF", "QRs por Turno"])

    with tabs[0]:
        st.subheader("Agregar docente")
        with st.form("form_create_docente", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            numero_empleado = c1.text_input("Número de empleado")
            nombre = c2.text_input("Nombre")
            apellido_paterno = c3.text_input("Apellido paterno")
            apellido_materno = c4.text_input("Apellido materno")
            d1, d2 = st.columns(2)
            puesto = d1.selectbox("Puesto", PUESTOS_OPCIONES, index=0)
            horario_entrada_time = d2.time_input("Horario de entrada (24h)", value=time(7, 0), step=60)
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
                    d1, d2 = st.columns(2)
                    puesto_index = PUESTOS_OPCIONES.index(docente["puesto"]) if docente["puesto"] in PUESTOS_OPCIONES else 0
                    puesto = d1.selectbox("Puesto", PUESTOS_OPCIONES, index=puesto_index)
                    horario_entrada_time = d2.time_input(
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

    with tabs[6]:
        st.subheader("Descarga masiva de QR por turno")
        st.caption("Genera archivos ZIP con todos los QR de docentes activos para cada turno.")

        for turno_nombre in ["Matutino", "Nocturno"]:
            block = st.container(border=True)
            with block:
                st.markdown(f"### {turno_nombre}")
                state_key = f"qr_zip_{turno_nombre.lower()}"
                if st.button(f"Preparar ZIP {turno_nombre}", key=f"prepare_zip_{turno_nombre.lower()}", use_container_width=True):
                    with st.spinner(f"Generando ZIP de QRs para {turno_nombre}..."):
                        st.session_state[state_key] = _build_turno_qr_zip(turno_nombre)

                payload = st.session_state.get(state_key)
                if payload:
                    if payload["included"] == 0:
                        st.warning("No se encontraron QRs para descargar en este turno.")
                    else:
                        st.success(
                            f"QRs incluidos: {payload['included']} de {payload['detected']} docentes detectados en {turno_nombre}."
                        )
                        zip_name = f"qrs_{turno_nombre.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                        st.download_button(
                            f"Descargar ZIP {turno_nombre}",
                            data=payload["zip_bytes"],
                            file_name=zip_name,
                            mime="application/zip",
                            use_container_width=True,
                            key=f"download_zip_{turno_nombre.lower()}",
                        )

                    if payload.get("errors"):
                        with st.expander(f"Detalles ({len(payload['errors'])} incidencias)"):
                            for err in payload["errors"][:100]:
                                st.error(err)


if __name__ == "__main__":
    main()

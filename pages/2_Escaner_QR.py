from __future__ import annotations

import streamlit as st
from PIL import Image
from sqlalchemy import select

from database.db import get_session, init_db
from database.models import Docente, DocenteHoraClase, HoraClase, Turno
from services.scanner import ScannerService
from services.scanner_camera import rear_camera_input
from services.ui import APP_NAME, configure_page, logout_button, page_hero, require_login, render_sidebar


def _get_turnos() -> dict[str, int]:
    """Obtiene disponibles turnos."""
    with get_session() as session:
        turnos = session.execute(select(Turno).order_by(Turno.nombre)).scalars().all()
        return {t.nombre: t.id for t in turnos}


def _get_horas_clase(turno_id: int) -> dict[str, int]:
    """Obtiene horas clase disponibles para un turno."""
    with get_session() as session:
        horas = session.execute(
            select(HoraClase)
            .where(HoraClase.turno_id == turno_id)
            .order_by(HoraClase.numero)
        ).scalars().all()
        return {f"Hora {h.numero} ({h.hora_inicio.strftime('%H:%M')}-{h.hora_fin.strftime('%H:%M')})": h.numero for h in horas}


def _get_salones_for_turno_hora(turno_id: int, numero_hora: int) -> set[str]:
    """Obtiene salones disponibles para un turno y hora específicos."""
    import datetime

    with get_session() as session:
        today = datetime.date.today()
        day_of_week = today.weekday()

        salones = session.execute(
            select(DocenteHoraClase.salon)
            .where(
                DocenteHoraClase.turno_id == turno_id,
                DocenteHoraClase.numero_hora == numero_hora,
                DocenteHoraClase.dia_semana == day_of_week,
            )
            .distinct()
        ).scalars().all()
        return set(salones)


def main() -> None:
    init_db()
    configure_page(f"{APP_NAME} | Escáner QR")
    user = require_login(["Administrador", "Prefecto"])

    render_sidebar(user)
    logout_button()

    page_hero("Escáner QR", "Selecciona turno, hora clase y salón, luego escanea el QR del docente.")

    # Sección de selección
    st.markdown("### Configuración de Asistencia")

    turnos = _get_turnos()
    if not turnos:
        st.error("No hay turnos configurados en el sistema.")
        st.stop()

    turno_nombre = st.selectbox("Turno", list(turnos.keys()), key="turno_select")
    turno_id = turnos[turno_nombre]

    horas_clase = _get_horas_clase(turno_id)
    if not horas_clase:
        st.error(f"No hay horas clase configuradas para {turno_nombre}.")
        st.stop()

    hora_label = st.selectbox("Hora Clase", list(horas_clase.keys()), key="hora_select")
    numero_hora = horas_clase[hora_label]

    salones = _get_salones_for_turno_hora(turno_id, numero_hora)
    if not salones:
        st.warning(f"No hay docentes asignados a {turno_nombre} - {hora_label} en esta fecha.")
        st.stop()

    # Solo administradores seleccionan salón, los prefectos no lo especifican
    if user["rol"] == "Administrador":
        salon = st.selectbox("Salón", sorted(salones), key="salon_select")
        st.info(f"Escaneando QR para: **{turno_nombre}** - **{hora_label}** - **Salón {salon}**")
    else:
        # Prefectos: no especifican salón
        salon = None
        st.info(f"Escaneando QR para: **{turno_nombre}** - **{hora_label}** (sin validación de salón)")

    if "scanner_camera_enabled" not in st.session_state:
        st.session_state["scanner_camera_enabled"] = False

    # Activación explícita de cámara para forzar el prompt de permisos por interacción del usuario
    activate_col, reset_col = st.columns([1, 1])
    with activate_col:
        if st.button("Activar cámara", use_container_width=True):
            st.session_state["scanner_camera_enabled"] = True
    with reset_col:
        if st.session_state["scanner_camera_enabled"] and st.button("Desactivar cámara", use_container_width=True):
            st.session_state["scanner_camera_enabled"] = False
            st.rerun()

    if not st.session_state["scanner_camera_enabled"]:
        st.info("Presiona 'Activar cámara' para solicitar permisos y comenzar el escaneo.")
        st.stop()

    # Componente personalizado con cámara trasera nativa
    image = rear_camera_input(key="escaner_qr")

    if image is None:
        st.stop()

    payload = ScannerService.decode_qr_from_image(image)

    if not payload:
        st.error("No se detectó ningún QR en la imagen capturada.")
        st.stop()

    detected_docente = ScannerService.identify_docente(payload)
    if not detected_docente:
        st.error("El QR detectado no pertenece a ningún docente registrado.")
        st.stop()

    detected_name = f"{detected_docente.nombre} {detected_docente.apellidos}".strip()
    st.success(f"QR detectado de: **{detected_name}**")

    if st.button("Registrar asistencia", use_container_width=True):
        result = ScannerService.register_attendance(
            qr_payload=payload,
            turno=turno_nombre,
            numero_hora=numero_hora,
            salon=salon,
            usuario_registro=user["usuario"],
        )

        if result.success:
            st.success("✅ Asistencia registrada correctamente")
            display_data = {
                "docente": result.docente.nombre if result.docente else None,
                "turno": result.asistencia.turno if result.asistencia else None,
                "hora": result.asistencia.numero_hora if result.asistencia else None,
                "estatus": result.asistencia.estatus if result.asistencia else None,
                "hora_registro": str(result.asistencia.hora) if result.asistencia else None,
            }
            # Solo mostrar salón y grupo si el usuario es administrador
            if user["rol"] == "Administrador":
                display_data["salón"] = result.asistencia.salon if result.asistencia else None
                display_data["grupo"] = result.asistencia.grupo if result.asistencia else None
            st.write(display_data)
        else:
            st.error(f"❌ {result.message}")


if __name__ == "__main__":
    main()

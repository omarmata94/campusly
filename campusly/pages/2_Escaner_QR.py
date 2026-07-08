from __future__ import annotations

import streamlit as st
from PIL import Image
from sqlalchemy import select

from database.db import get_session, init_db
from database.models import Docente, DocenteHoraClase, HoraClase, Turno
from services.scanner import ScannerService
from services.time_utils import current_time_local, today_local
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
    with get_session() as session:
        today = today_local()
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


def _detect_hora_clase_automatica(turno_nombre: str, hora_referencia):
    """Detecta hora clase con fallback local para evitar fallas por caché de módulos."""
    if hasattr(ScannerService, "detect_hora_clase_by_time"):
        return ScannerService.detect_hora_clase_by_time(turno_nombre, hora_referencia)

    with get_session() as session:
        horas = session.execute(
            select(HoraClase)
            .where(HoraClase.turno.has(nombre=turno_nombre))
            .order_by(HoraClase.numero)
        ).scalars().all()
        for hora_clase in horas:
            if hora_clase.hora_inicio <= hora_referencia < hora_clase.hora_fin:
                return hora_clase
    return None


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

    modo_hora = st.radio(
        "Modo de selección de hora clase",
        ["Automático", "Manual"],
        horizontal=True,
        help="Automático detecta la hora clase por la hora actual. Manual permite seleccionar la hora clase.",
    )

    hora_label = ""
    numero_hora: int | None = None
    hora_referencia = current_time_local()

    if modo_hora == "Automático":
        fuente_hora = st.radio(
            "Fuente de hora",
            ["Servidor", "Dispositivo (manual)"],
            horizontal=True,
            help="Servidor usa la hora del backend. Dispositivo permite capturar la hora visible en tu celular.",
        )

        if fuente_hora == "Dispositivo (manual)":
            hora_referencia = st.time_input(
                "Hora del dispositivo",
                value=current_time_local(),
                step=60,
                help="Ajusta esta hora para que coincida con la del dispositivo desde donde escaneas.",
            )
        else:
            st.caption(f"Hora servidor: {hora_referencia.strftime('%H:%M:%S')}")

        hora_detectada = _detect_hora_clase_automatica(turno_nombre, hora_referencia)
        if hora_detectada is None:
            st.warning("No hay una hora clase activa para la hora indicada. Cambia a modo manual para continuar.")
        else:
            numero_hora = hora_detectada.numero
            hora_label = (
                f"Hora {hora_detectada.numero} "
                f"({hora_detectada.hora_inicio.strftime('%H:%M')}-{hora_detectada.hora_fin.strftime('%H:%M')})"
            )
            st.success(f"Hora clase detectada automáticamente: {hora_label}")

    if modo_hora == "Manual" or numero_hora is None:
        hora_label = st.selectbox("Hora Clase", list(horas_clase.keys()), key="hora_select")
        numero_hora = horas_clase[hora_label]
        # En modo manual, el registro usa la hora del servidor.
        hora_referencia = current_time_local()

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

    # Forzar cámara trasera sobreescribiendo la restricción de getUserMedia
    st.markdown(
        """
        <script>
        (function() {
            const _gum = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
            navigator.mediaDevices.getUserMedia = function(constraints) {
                if (constraints && constraints.video) {
                    const v = typeof constraints.video === 'object' ? constraints.video : {};
                    v.facingMode = { ideal: 'environment' };
                    constraints.video = v;
                }
                return _gum(constraints);
            };
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )

    # Captura de cámara
    camera = st.camera_input("Activar cámara", label_visibility="visible")

    if camera is None:
        st.stop()

    image = Image.open(camera)
    st.image(image, caption="Imagen capturada", use_container_width=True)

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
            hora_registro=hora_referencia,
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

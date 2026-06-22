from __future__ import annotations

import streamlit as st
from PIL import Image
from sqlalchemy import select

from database.db import get_session
from database.db import init_db
from database.models import Docente
from services.scanner import ScannerService
from services.ui import APP_NAME, configure_page, logout_button, page_hero, require_login, render_sidebar


def _active_docentes() -> list[dict]:
    with get_session() as session:
        rows = session.execute(
            select(Docente)
            .where(Docente.activo.is_(True))
            .order_by(Docente.apellido_paterno, Docente.apellido_materno, Docente.nombre)
        ).scalars().all()
    return [
        {
            "id": docente.id,
            "nombre": docente.nombre,
            "apellidos": docente.apellidos,
            "numero_empleado": docente.numero_empleado,
            "nombre_completo": f"{docente.nombre} {docente.apellidos}".strip(),
        }
        for docente in rows
    ]


def main() -> None:
    init_db()
    configure_page(f"{APP_NAME} | Escáner QR")
    user = require_login(["Administrador", "Prefecto"])

    render_sidebar(user)
    logout_button()

    page_hero("Escáner QR", "Usa la cámara del celular o computadora para leer el QR del gafete.")

    docentes = _active_docentes()
    if not docentes:
        st.warning("No hay docentes activos para validar asistencia.")
        st.stop()

    options = {f"{d['numero_empleado']} - {d['nombre_completo']}": d["id"] for d in docentes}
    selected_label = st.selectbox("Docente esperado", list(options.keys()))
    selected_docente_id = options[selected_label]
    selected_docente = next((doc for doc in docentes if doc["id"] == selected_docente_id), None)

    st.info("Activa la cámara y captura el QR. Se identificará automáticamente al docente para verificar que sea el correcto.")
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
    expected_name = selected_docente["nombre_completo"] if selected_docente else "Docente seleccionado"

    st.success(f"QR detectado de: {detected_name}")
    is_expected_docente = detected_docente.id == selected_docente_id
    if is_expected_docente:
        st.info("Validación correcta: el QR coincide con el docente esperado.")
    else:
        st.error(f"Validación fallida: se esperaba a {expected_name}, pero el QR es de {detected_name}.")

    if st.button("Registrar asistencia", use_container_width=True, disabled=not is_expected_docente):
        result = ScannerService.register_attendance(
            payload,
            usuario_registro=user["usuario"],
            expected_docente_id=selected_docente_id,
        )
        if result.success:
            st.success("Asistencia registrada correctamente")
            st.write(
                {
                    "docente": f"{result.docente.nombre} {result.docente.apellidos}" if result.docente else None,
                    "estatus": result.asistencia.estatus if result.asistencia else None,
                    "hora": str(result.asistencia.hora) if result.asistencia else None,
                }
            )
        elif result.message == "El docente ya registró asistencia hoy":
            st.warning("El docente ya registró asistencia hoy")
        else:
            st.error(result.message)


if __name__ == "__main__":
    main()

from __future__ import annotations

import streamlit as st
from PIL import Image

from database.db import init_db
from services.scanner import ScannerService
from services.ui import APP_NAME, configure_page, logout_button, page_hero, require_login, render_sidebar


def main() -> None:
    init_db()
    configure_page(f"{APP_NAME} | Escáner QR")
    user = require_login(["Administrador", "Prefecto"])

    render_sidebar(user)
    logout_button()

    page_hero("Escáner QR", "Usa la cámara del celular o computadora para leer el QR del gafete.")

    st.info("Activa la cámara y captura el QR. El sistema identificará al docente y registrará la asistencia automáticamente.")
    camera = st.camera_input("Activar cámara", label_visibility="visible")

    if camera is None:
        st.stop()

    image = Image.open(camera)
    st.image(image, caption="Imagen capturada", use_container_width=True)
    payload = ScannerService.decode_qr_from_image(image)

    if not payload:
        st.error("No se detectó ningún QR en la imagen capturada.")
        st.stop()

    if st.button("Registrar asistencia", use_container_width=True):
        result = ScannerService.register_attendance(payload, usuario_registro=user["usuario"])
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

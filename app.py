from __future__ import annotations

import streamlit as st

from database.db import has_users, init_db
from services.auth import AuthService
from services.ui import APP_NAME, configure_page, page_hero, render_sidebar


def _set_auth(user) -> None:
    st.session_state["auth_user"] = {
        "id": user.id,
        "nombre": user.nombre,
        "usuario": user.usuario,
        "rol": user.rol,
    }


def render_bootstrap() -> None:
    page_hero(
        "Sistema de Asistencia Docente mediante QR",
        "Plataforma SaaS ligera para control de asistencia, QR institucional y analítica operativa.",
    )
    st.info("No existen usuarios registrados. Crea el primer administrador para comenzar.")
    with st.form("bootstrap_admin"):
        nombre = st.text_input("Nombre completo", placeholder="Administración General")
        usuario = st.text_input("Usuario", placeholder="admin")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Crear primer administrador", use_container_width=True)
    if submit:
        if not nombre or not usuario or not password:
            st.error("Todos los campos son obligatorios.")
            return
        try:
            admin = AuthService.bootstrap_first_admin(nombre=nombre, usuario=usuario, password=password)
            _set_auth(admin)
            st.success("Administrador inicial creado correctamente.")
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))


def render_login() -> None:
    page_hero(
        "Sistema de Asistencia Docente mediante QR",
        "Plataforma SaaS ligera para control de asistencia, QR institucional y analítica operativa.",
    )
    col_left, col_right = st.columns([1.15, 0.85], gap="large")
    with col_left:
        st.markdown(
            """
            <div class="hero-card">
                <h1>Sistema de Asistencia Docente mediante QR</h1>
                <p class="soft-note">Control de asistencia con QR institucional, SQLite local, reportes y tablero en tiempo real.</p>
                <div style="margin-top: 1rem;">
                    <span class="badge-pill">Seguridad</span>
                    <span class="badge-pill">QR único</span>
                    <span class="badge-pill">Puntualidad</span>
                    <span class="badge-pill">Exportación</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("Usa la barra lateral para navegar entre docentes, escáner, asistencias, reportes y tablero.")
    with col_right:
        st.markdown("### Inicio de sesión")
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Entrar", use_container_width=True)
        if submit:
            authenticated = AuthService.authenticate(usuario=usuario, password=password)
            if authenticated is None:
                st.error("Credenciales inválidas.")
            else:
                _set_auth(authenticated)
                st.success(f"Bienvenido, {authenticated.nombre}.")
                st.rerun()


def main() -> None:
    init_db()
    configure_page(APP_NAME)

    render_sidebar(st.session_state.get("auth_user"))

    user = st.session_state.get("auth_user")
    if user:
        if st.sidebar.button("Cerrar sesión", use_container_width=True):
            st.session_state.pop("auth_user", None)
            st.rerun()
        page_hero("Panel principal", "Accede a los módulos desde la navegación lateral. El sistema conserva el historial en SQLite local.")
        return

    if not has_users():
        render_bootstrap()
    else:
        render_login()


if __name__ == "__main__":
    main()

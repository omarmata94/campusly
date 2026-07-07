from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import func, select

from database.db import get_session, has_users, init_db
from database.models import Asistencia, Docente, DocenteHoraClase
from services.auth import AuthService
from services.time_utils import today_local
from services.ui import APP_NAME, configure_page, logout_button, metric_card, page_hero, render_sidebar, styled_attendance_table


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
    left, center, right = st.columns([0.75, 1.5, 0.75], gap="large")
    with center:
        st.markdown(
            """
            <div class="content-card reveal-card login-intro-card">
                <div class="login-icon">🔐</div>
                <h3 style="margin:0;">Inicio de sesión</h3>
                <p class="soft-note" style="margin-top:0.35rem;">Ingresa tus credenciales para continuar</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            usuario = st.text_input("Usuario", placeholder="Ej. omar.mata")
            password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
            submit = st.form_submit_button("Entrar", use_container_width=True)
        if submit:
            authenticated = AuthService.authenticate(usuario=usuario, password=password)
            if authenticated is None:
                st.error("Credenciales inválidas.")
            else:
                _set_auth(authenticated)
                st.success(f"Bienvenido, {authenticated.nombre}.")
                st.rerun()


def _home_totals() -> dict[str, int | str]:
    today = today_local()
    with get_session() as session:
        docentes_activos = session.scalar(
            select(func.count(Docente.id)).where(Docente.activo.is_(True))
        ) or 0
        horarios_asignados = session.scalar(select(func.count(DocenteHoraClase.id))) or 0
        asistencias_hoy = session.scalar(
            select(func.count(Asistencia.id)).where(Asistencia.fecha == today)
        ) or 0
        retardos_hoy = session.scalar(
            select(func.count(Asistencia.id)).where(
                Asistencia.fecha == today,
                Asistencia.estatus == "Retardo",
            )
        ) or 0
        docentes_con_horario = session.scalar(
            select(func.count(func.distinct(DocenteHoraClase.docente_id)))
        ) or 0
        ultimo_registro = session.execute(
            select(
                Asistencia.fecha,
                Asistencia.hora,
                Docente.nombre,
                Docente.apellidos,
                Asistencia.turno,
            )
            .join(Docente, Asistencia.docente_id == Docente.id)
            .order_by(Asistencia.fecha.desc(), Asistencia.hora.desc())
            .limit(1)
        ).mappings().first()

    ultimo_texto = "Sin escaneos aún"
    if ultimo_registro:
        docente_nombre = f"{ultimo_registro['nombre']} {ultimo_registro['apellidos']}".strip()
        ultimo_texto = (
            f"{docente_nombre} · {ultimo_registro['turno']} · "
            f"{ultimo_registro['fecha'].isoformat()} {str(ultimo_registro['hora'])[:5]}"
        )

    return {
        "fecha": today.isoformat(),
        "docentes_activos": int(docentes_activos),
        "horarios_asignados": int(horarios_asignados),
        "asistencias_hoy": int(asistencias_hoy),
        "retardos_hoy": int(retardos_hoy),
        "docentes_sin_horario": max(int(docentes_activos) - int(docentes_con_horario), 0),
        "ultimo_registro": ultimo_texto,
    }


def _home_recent_activity(limit: int = 10) -> pd.DataFrame:
    with get_session() as session:
        rows = session.execute(
            select(
                Asistencia.fecha.label("fecha"),
                Asistencia.hora.label("hora"),
                Asistencia.turno.label("turno"),
                Asistencia.estatus.label("estatus"),
                Docente.nombre.label("nombre"),
                Docente.apellidos.label("apellidos"),
            )
            .join(Docente, Asistencia.docente_id == Docente.id)
            .order_by(Asistencia.fecha.desc(), Asistencia.hora.desc())
            .limit(limit)
        ).mappings().all()

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["fecha", "hora", "docente", "turno", "estatus"])

    df["docente"] = (df["nombre"].astype(str) + " " + df["apellidos"].astype(str)).str.strip()
    df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
    df["hora"] = df["hora"].astype(str).str.slice(0, 5)
    return df[["fecha", "hora", "docente", "turno", "estatus"]]


def _render_quick_action_cards(actions: list[tuple[str, str, str, str, str]]) -> None:
    col_left, col_right = st.columns(2, gap="small")
    for index, (href, icon, title, subtitle, category) in enumerate(actions):
        with col_left if index % 2 == 0 else col_right:
            st.markdown(
                f"""
                <a class="quick-action-link reveal-card" data-category="{category}" href="{href}" target="_self">
                    <div class="quick-action-icon">{icon}</div>
                    <div class="quick-action-content">
                        <div class="quick-action-title">{title}</div>
                        <div class="quick-action-subtitle">{subtitle}</div>
                    </div>
                    <div class="quick-action-arrow">→</div>
                </a>
                """,
                unsafe_allow_html=True,
            )


def render_home_dashboard(user: dict) -> None:
    totals = _home_totals()

    page_hero(
        f"Panel principal · {user['rol']}",
        "Resumen operativo del día, accesos rápidos y actividad reciente del sistema.",
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(metric_card("Asistencias hoy", totals["asistencias_hoy"], f"Fecha {totals['fecha']}"), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("Retardos hoy", totals["retardos_hoy"], "Monitoreo en tiempo real", "warning"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("Docentes activos", totals["docentes_activos"], "Plantilla vigente", "success"), unsafe_allow_html=True)
    with c4:
        st.markdown(metric_card("Horarios asignados", totals["horarios_asignados"], "Carga académica", "primary"), unsafe_allow_html=True)

    left, right = st.columns([1.05, 1.4], gap="large")

    with left:
        st.markdown(
            """
            <div class="content-card reveal-card">
                <h3 style="margin:0;">Acciones rápidas</h3>
                <p class="soft-note" style="margin-top:0.35rem;">Navega a los módulos más usados sin pasar por el menú lateral.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if user.get("rol") == "Administrador":
            quick_actions = [
                ("/Escaner_QR", "📷", "Escáner QR", "Registrar asistencia en tiempo real", "operacion"),
                ("/Cargar_Horarios", "📅", "Cargar Horarios", "Importación PDF individual o masiva", "operacion"),
                ("/Asignar_Horarios", "🗂️", "Asignar Horarios", "Vincular docentes y bloques", "operacion"),
                ("/Reportes", "📊", "Reportes", "Indicadores por periodo y estatus", "analisis"),
                ("/Tablero", "📈", "Tablero", "Vista global de desempeño", "analisis"),
                ("/Usuarios", "👥", "Usuarios", "Gestión de accesos y roles", "administracion"),
            ]
        else:
            quick_actions = [
                ("/Escaner_QR", "📷", "Escáner QR", "Registrar asistencia en tiempo real", "operacion"),
                ("/Cargar_Horarios", "📅", "Cargar Horarios", "Importación PDF individual o masiva", "operacion"),
                ("/Asistencias", "✅", "Asistencias", "Consulta y seguimiento diario", "operacion"),
                ("/Reportes", "📊", "Reportes", "Métricas y exportables", "analisis"),
            ]

        _render_quick_action_cards(quick_actions)

        st.markdown(
            f"""
            <div class="content-card reveal-card" style="margin-top:0.4rem;">
                <h3 style="margin:0;">Estado del sistema</h3>
                <p class="soft-note" style="margin-top:0.45rem;">Último escaneo: {totals['ultimo_registro']}</p>
                <p class="soft-note" style="margin:0.2rem 0 0 0;">Docentes sin horario asignado: <strong>{totals['docentes_sin_horario']}</strong></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            """
            <div class="content-card reveal-card">
                <h3 style="margin:0;">Actividad reciente</h3>
                <p class="soft-note" style="margin-top:0.35rem;">Últimos escaneos registrados en el sistema.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        recent_df = _home_recent_activity(limit=10)
        if recent_df.empty:
            st.info("Aún no hay asistencias registradas. Usa Escáner QR para comenzar.")
        else:
            st.dataframe(styled_attendance_table(recent_df), use_container_width=True, hide_index=True)

    if totals["docentes_sin_horario"] > 0 and user.get("rol") == "Administrador":
        st.warning(
            f"Hay {totals['docentes_sin_horario']} docente(s) activo(s) sin horario asignado. "
            "Te conviene revisarlo en Asignar Horarios."
        )
    elif totals["asistencias_hoy"] == 0:
        st.info("Todavía no hay escaneos del día. El flujo está listo para iniciar asistencia.")
    else:
        st.success("Inicio actualizado correctamente con actividad operativa del día.")


def main() -> None:
    init_db()
    configure_page(APP_NAME)

    render_sidebar(st.session_state.get("auth_user"))

    user = st.session_state.get("auth_user")
    if user:
        logout_button()
        render_home_dashboard(user)
        return

    if not has_users():
        render_bootstrap()
    else:
        render_login()


if __name__ == "__main__":
    main()

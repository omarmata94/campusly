from __future__ import annotations

import pandas as pd
import streamlit as st


APP_NAME = "Sistema de Asistencia Docente mediante QR"
APP_AUTHOR = "Ing. Omar Mata"


def _allowed_sidebar_pages(role: str) -> list[tuple[str, str, str]]:
    all_pages = [
        ("app.py", "Inicio", "🏠"),
        ("pages/0_Cargar_Horarios.py", "Cargar Horarios", "📅"),
        ("pages/1_Docentes.py", "Docentes", "👨‍🏫"),
        ("pages/2_Escaner_QR.py", "Escáner QR", "📷"),
        ("pages/3_Asignar_Horarios.py", "Asignar Horarios", "🗂️"),
        ("pages/4_Asistencias.py", "Asistencias", "✅"),
        ("pages/5_Reportes.py", "Reportes", "📊"),
        ("pages/6_Tablero.py", "Tablero", "📈"),
        ("pages/7_Usuarios.py", "Usuarios", "👥"),
    ]
    if role == "Administrador":
        return all_pages
    if role == "Prefecto":
        return [
            ("app.py", "Inicio", "🏠"),
            ("pages/0_Cargar_Horarios.py", "Cargar Horarios", "📅"),
            ("pages/2_Escaner_QR.py", "Escáner QR", "📷"),
            ("pages/4_Asistencias.py", "Asistencias", "✅"),
            ("pages/5_Reportes.py", "Reportes", "📊"),
            ("pages/6_Tablero.py", "Tablero", "📈"),
        ]
    return [("app.py", "Inicio", "🏠")]


def configure_page(title: str) -> None:
    st.set_page_config(page_title=title, page_icon="🎓", layout="wide", initial_sidebar_state="expanded")
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #F8FAFC;
                --surface: #FFFFFF;
                --surface-2: #F1F5F9;
                --text: #0F172A;
                --muted: #64748B;
                --border: #E2E8F0;
                --primary: #2563EB;
                --primary-strong: #1D4ED8;
                --success: #10B981;
                --warning: #F59E0B;
                --error: #EF4444;
                --shadow: 0 10px 30px rgba(15, 23, 42, 0.07);
                --shadow-soft: 0 6px 18px rgba(15, 23, 42, 0.05);
                --radius-lg: 22px;
                --radius-md: 16px;
                --radius-sm: 12px;
            }

            html, body, [class*="css"] {
                font-family: "Inter", sans-serif;
            }

            .stApp {
                background: var(--bg);
                color: var(--text);
            }

            .block-container {
                padding-top: 1.2rem;
                padding-bottom: 2rem;
            }

            [data-testid="stSidebar"] {
                background: #ffffff;
                border-right: 1px solid var(--border);
                width: 270px;
            }

            [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
                gap: 0.35rem;
            }

            [data-testid="stSidebar"] .sidebar-shell {
                padding: 0.95rem;
            }

            [data-testid="stSidebar"] .brand-card {
                background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 0.95rem 1rem;
                box-shadow: var(--shadow-soft);
            }

            [data-testid="stSidebar"] .brand-mark {
                display: inline-flex;
                width: 42px;
                height: 42px;
                align-items: center;
                justify-content: center;
                border-radius: 14px;
                background: linear-gradient(135deg, var(--primary) 0%, #60A5FA 100%);
                color: #fff;
                font-weight: 800;
                font-size: 1rem;
                box-shadow: 0 10px 20px rgba(37, 99, 235, 0.25);
            }

            [data-testid="stSidebar"] .brand-title {
                color: var(--text);
                font-size: 1.05rem;
                font-weight: 800;
                line-height: 1.1;
                margin-top: 0.15rem;
            }

            [data-testid="stSidebar"] .brand-subtitle {
                color: var(--muted);
                font-size: 0.78rem;
                margin-top: 0.15rem;
            }

            [data-testid="stSidebar"] a {
                color: var(--text) !important;
            }

            [data-testid="stSidebarNav"] {
                display: none;
            }

            [data-testid="stSidebarNav"] ul {
                gap: 0.25rem;
            }

            [data-testid="stSidebarNav"] li a {
                border-radius: 14px;
                padding: 0.72rem 0.9rem;
                transition: all 0.2s ease;
                border: 1px solid transparent;
                background: transparent;
            }

            [data-testid="stSidebarNav"] li a:hover {
                background: #f8fafc;
                border-color: var(--border);
            }

            [data-testid="stSidebarNav"] li a[aria-current="page"] {
                background: rgba(37, 99, 235, 0.10);
                border-color: rgba(37, 99, 235, 0.20);
                box-shadow: inset 3px 0 0 var(--primary);
            }

            h1, h2, h3, h4 {
                letter-spacing: -0.025em;
            }

            h1 {
                font-size: 32px !important;
                font-weight: 800 !important;
                color: var(--text) !important;
            }

            h2 {
                font-size: 20px !important;
                font-weight: 700 !important;
                color: var(--text) !important;
            }

            h3 {
                font-size: 18px !important;
                font-weight: 700 !important;
            }

            p, div, span, label, input, textarea {
                color: var(--text);
            }

            .soft-note, .stCaption {
                color: var(--muted) !important;
                font-size: 14px;
            }

            .page-hero {
                background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
                border: 1px solid var(--border);
                border-radius: 24px;
                padding: 1.2rem 1.3rem;
                box-shadow: var(--shadow);
                margin-bottom: 1rem;
            }

            .page-hero .eyebrow {
                display: inline-flex;
                align-items: center;
                gap: 0.45rem;
                color: var(--primary);
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                margin-bottom: 0.35rem;
            }

            .page-hero .title {
                font-size: 32px;
                line-height: 1.1;
                font-weight: 800;
                color: var(--text);
                margin: 0;
            }

            .page-hero .subtitle {
                color: var(--muted);
                font-size: 14px;
                margin-top: 0.35rem;
            }

            .hero-card, .metric-card, .content-card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                padding: 1.1rem 1.2rem;
                box-shadow: var(--shadow-soft);
                transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
            }

            .hero-card:hover, .metric-card:hover, .content-card:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow);
            }

            .badge-pill, .status-chip {
                display: inline-block;
                padding: 0.35rem 0.7rem;
                border-radius: 999px;
                background: #EFF6FF;
                color: var(--primary);
                font-weight: 700;
                margin-right: 0.35rem;
                font-size: 12px;
                border: 1px solid rgba(37, 99, 235, 0.12);
            }

            .status-chip.success { background: rgba(16, 185, 129, 0.10); color: var(--success); border-color: rgba(16, 185, 129, 0.16); }
            .status-chip.warning { background: rgba(245, 158, 11, 0.12); color: var(--warning); border-color: rgba(245, 158, 11, 0.18); }
            .status-chip.error { background: rgba(239, 68, 68, 0.10); color: var(--error); border-color: rgba(239, 68, 68, 0.16); }

            .metric-card {
                min-height: 132px;
            }

            .metric-card .metric-label {
                color: var(--muted);
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-weight: 700;
            }

            .metric-card .metric-value {
                color: var(--text);
                font-size: 32px;
                line-height: 1.1;
                font-weight: 800;
                margin-top: 0.35rem;
            }

            .metric-card .metric-delta {
                color: var(--muted);
                font-size: 12px;
                margin-top: 0.2rem;
            }

            .metric-card.primary { border-left: 4px solid var(--primary); }
            .metric-card.success { border-left: 4px solid var(--success); }
            .metric-card.warning { border-left: 4px solid var(--warning); }
            .metric-card.error { border-left: 4px solid var(--error); }

            .stTextInput input, .stTextArea textarea, .stDateInput input, .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] {
                background: #ffffff !important;
                color: var(--text) !important;
                border: 1px solid var(--border) !important;
                border-radius: 14px !important;
                min-height: 46px !important;
                box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03) !important;
            }

            .stTextInput input::placeholder, .stTextArea textarea::placeholder {
                color: #94A3B8 !important;
            }

            .stTextInput input:focus, .stTextArea textarea:focus {
                border-color: var(--primary) !important;
                box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12) !important;
            }

            .stButton > button {
                border-radius: 14px;
                border: 1px solid transparent;
                min-height: 44px;
                font-weight: 700;
                transition: all 0.2s ease;
            }

            .stButton > button:hover {
                transform: translateY(-1px);
                box-shadow: 0 8px 20px rgba(37, 99, 235, 0.16);
            }

            .stButton > button[kind="primary"], .stDownloadButton > button {
                background: var(--primary);
                color: white;
                border-color: var(--primary);
            }

            .stButton > button[kind="secondary"] {
                background: #ffffff;
                color: var(--text);
                border-color: var(--border);
            }

            .stDataFrame, .stDataEditor {
                border-radius: 18px;
                overflow: hidden;
                border: 1px solid var(--border);
                box-shadow: var(--shadow-soft);
            }

            [data-testid="stDataFrame"] [role="gridcell"], [data-testid="stDataFrame"] [role="columnheader"] {
                font-size: 14px;
            }

            [data-testid="stDataFrame"] [role="columnheader"] {
                background: #F8FAFC !important;
                color: var(--text) !important;
                border-bottom: 1px solid var(--border) !important;
            }

            [data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"] {
                background: #F8FAFC !important;
            }

            .table-shell {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 20px;
                box-shadow: var(--shadow-soft);
                overflow: hidden;
            }

            .reveal-card {
                animation: fadeUp 0.35s ease both;
            }

            @keyframes fadeUp {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            @media (max-width: 768px) {
                .block-container {
                    padding-left: 1rem;
                    padding-right: 1rem;
                }
                [data-testid="stSidebar"] {
                    width: 100%;
                }
                h1, .page-hero .title { font-size: 26px !important; }
                .metric-card .metric-value { font-size: 26px; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(user: dict | None = None) -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-shell">
              <div class="brand-card">
                <div style="display:flex; align-items:center; gap:0.8rem;">
                  <div class="brand-mark">C</div>
                  <div>
                    <div class="brand-title">Campusly</div>
                    <div class="brand-subtitle">Asistencia docente QR</div>
                  </div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if user:
            st.markdown(
                f"""
                <div class="content-card reveal-card" style="margin-top:0.75rem;">
                  <div style="font-size:12px; color: var(--muted); text-transform:uppercase; letter-spacing:0.08em; font-weight:700;">Sesión activa</div>
                  <div style="margin-top:0.35rem; font-weight:700; color: var(--text);">{user['nombre']}</div>
                  <div style="color: var(--muted); font-size:12px; margin-top:0.15rem;">{user['rol']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("### Navegación")
            for page_path, label, icon in _allowed_sidebar_pages(user.get("rol", "")):
                st.page_link(page_path, label=label, icon=icon, use_container_width=True)

        st.markdown(
            f"""
            <div style="margin-top:1rem; padding:0.7rem 0.8rem; border:1px solid var(--border); border-radius:12px; background:#f8fafc; color:var(--muted); font-size:12px;">
                Hecho por <strong>{APP_AUTHOR}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )


def page_hero(title: str, subtitle: str, eyebrow: str = "Campusly") -> None:
    st.markdown(
        f"""
        <div class="page-hero reveal-card">
            <div class="eyebrow">{eyebrow}</div>
            <div class="title">{title}</div>
            <div class="subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str | int | float, delta: str, variant: str = "primary") -> str:
    return f"""
    <div class="metric-card {variant} reveal-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-delta">{delta}</div>
    </div>
    """


def styled_attendance_table(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    if df.empty:
        return df.style

    def status_style(value: str) -> str:
        color_map = {
            "Puntual": "background-color: rgba(16, 185, 129, 0.12); color: #047857; font-weight: 700;",
            "Retardo": "background-color: rgba(245, 158, 11, 0.14); color: #92400E; font-weight: 700;",
            "Falta": "background-color: rgba(239, 68, 68, 0.12); color: #B91C1C; font-weight: 700;",
        }
        return color_map.get(str(value), "")

    styler = (
        df.style.hide(axis="index")
        .set_table_styles(
            [
                {"selector": "table", "props": [("border-collapse", "separate"), ("border-spacing", "0"), ("width", "100%")]},
                {"selector": "thead th", "props": [("background-color", "#F8FAFC"), ("color", "#0F172A"), ("font-weight", "700"), ("border-bottom", "1px solid #E2E8F0"), ("padding", "12px 14px")]},
                {"selector": "tbody td", "props": [("padding", "12px 14px"), ("border-bottom", "1px solid #E2E8F0"), ("background-color", "#FFFFFF"), ("font-size", "14px")]},
                {"selector": "tbody tr:hover td", "props": [("background-color", "#F8FAFC")]},
            ]
        )
    )

    if "estatus" in df.columns:
        styler = styler.map(status_style, subset=["estatus"])
    return styler


def require_login(roles: list[str] | None = None):
    user = st.session_state.get("auth_user")
    if not user:
        st.warning("Debes iniciar sesión para continuar.")
        st.stop()
    if roles and user["rol"] not in roles:
        st.error("No tienes permisos para acceder a esta sección.")
        st.stop()
    return user


def logout_button() -> None:
    if st.sidebar.button("Cerrar sesión", use_container_width=True):
        st.session_state.pop("auth_user", None)
        st.session_state.pop("auth_token", None)
        st.rerun()

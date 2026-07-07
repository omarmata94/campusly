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
                background: linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(248, 251, 255, 0.92) 100%);
                backdrop-filter: blur(8px);
                border-right: 1px solid rgba(219, 230, 245, 0.6);
                width: 282px;
            }

            [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
                padding-top: 0.2rem;
            }

            [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
                gap: 0.55rem;
            }

            [data-testid="stSidebar"] .sidebar-shell {
                padding: 0.35rem 0.9rem 0.6rem 0.9rem;
            }

            [data-testid="stSidebar"] .brand-card {
                background: radial-gradient(circle at 12% 12%, #e9f3ff 0%, #ffffff 45%);
                border: 1px solid #d8e4f4;
                border-radius: 20px;
                padding: 0.75rem 0.95rem;
                box-shadow: 0 10px 24px rgba(37, 99, 235, 0.08);
            }

            [data-testid="stSidebar"] .brand-card > div {
                display: flex;
                align-items: center;
                gap: 0.85rem;
            }

            [data-testid="stSidebar"] .brand-mark {
                display: flex;
                width: 70px;
                height: 70px;
                align-items: center;
                justify-content: center;
                border-radius: 16px;
                background: linear-gradient(165deg, #1d4ed8 0%, #60a5fa 100%);
                color: #fff;
                font-weight: 800;
                font-size: 1.4rem;
                box-shadow: 0 12px 20px rgba(37, 99, 235, 0.24);
                overflow: hidden;
                flex-shrink: 0;
            }

            [data-testid="stSidebar"] .brand-mark img {
                width: 85%;
                height: 85%;
                object-fit: contain;
                object-position: center;
            }

            [data-testid="stSidebar"] .brand-title {
                color: #12223d;
                font-size: 1.55rem;
                font-weight: 800;
                line-height: 1.05;
                margin-top: 0;
            }

            [data-testid="stSidebar"] .brand-subtitle {
                color: #5d708e;
                font-size: 0.75rem;
                margin-top: 0.08rem;
                font-weight: 600;
                letter-spacing: 0.01em;
            }

            [data-testid="stSidebar"] .session-card {
                border-radius: 20px;
                border: 1px solid #d8e4f4;
                background: #ffffff;
                box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
                padding: 0.75rem 1rem;
                margin-top: 0.15rem;
                margin-bottom: 0.4rem;
            }

            [data-testid="stSidebar"] .session-label {
                color: #5d708e;
                font-size: 0.73rem;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 0.12em;
            }

            [data-testid="stSidebar"] .session-name {
                margin-top: 0.45rem;
                color: #0f1f3f;
                font-weight: 800;
                font-size: 1.02rem;
            }

            [data-testid="stSidebar"] .session-role {
                color: #5d708e;
                font-size: 0.85rem;
                margin-top: 0.18rem;
                font-weight: 600;
            }

            [data-testid="stSidebar"] .nav-title {
                color: #102446;
                font-size: 1.95rem;
                font-weight: 800;
                letter-spacing: -0.02em;
                margin: 0.1rem 0 0.2rem 0;
            }

            [data-testid="stSidebar"] a {
                color: #102446 !important;
                text-decoration: none !important;
            }

            [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"],
            [data-testid="stSidebar"] .stPageLink > a {
                display: flex;
                align-items: center;
                border-radius: 14px;
                padding: 0.5rem 0.7rem;
                border: 1px solid transparent;
                transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
                font-weight: 700;
                min-height: 44px;
            }

            [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover,
            [data-testid="stSidebar"] .stPageLink > a:hover {
                background: linear-gradient(135deg, #edf4ff 0%, #f0f7ff 100%);
                border-color: #d5e3f8;
                transform: translateX(3px);
                box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08);
            }

            [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"],
            [data-testid="stSidebar"] .stPageLink > a[aria-current="page"] {
                background: linear-gradient(135deg, #eaf2ff 0%, #dce7f5 100%);
                border-color: #bfd9f9;
                box-shadow: inset 4px 0 0 #1d4ed8, 0 4px 12px rgba(37, 99, 235, 0.12);
            }

            [data-testid="stSidebar"] .sidebar-credit {
                margin-top: 0.8rem;
                padding: 0.35rem 0.5rem;
                border: none;
                border-radius: 8px;
                background: transparent;
                color: #94a3b8;
                font-size: 0.7rem;
                text-align: center;
                font-weight: 400;
                line-height: 1.4;
                transition: color 0.3s ease;
            }

            [data-testid="stSidebar"] .sidebar-credit:hover {
                color: #64748b;
            }

            [data-testid="stSidebar"] .stButton > button {
                border-radius: 16px;
                border: 1px solid #d8e4f4;
                background: #ffffff;
                color: #11274a;
                min-height: 52px;
                font-size: 1.02rem;
                font-weight: 700;
                box-shadow: 0 6px 14px rgba(15, 23, 42, 0.05);
            }

            [data-testid="stSidebar"] .stButton > button:hover {
                background: #f5f9ff;
                border-color: #c8d8f3;
                box-shadow: 0 10px 18px rgba(15, 23, 42, 0.08);
                transform: translateY(-1px);
            }

            [data-testid="stSidebarNav"] {
                display: none;
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
                background: linear-gradient(135deg, #ffffff 0%, #fafbff 100%);
                border: 1.5px solid var(--border);
                border-radius: var(--radius-lg);
                padding: 1.1rem 1.2rem;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04), 0 1px 3px rgba(15, 23, 42, 0.08);
                transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease, border-color 0.3s ease;
            }

            .hero-card:hover, .metric-card:hover, .content-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 16px 40px rgba(37, 99, 235, 0.12), 0 2px 8px rgba(15, 23, 42, 0.1);
                border-color: #bfd9f9;
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

            .quick-action-link {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                padding: 0.82rem 0.95rem;
                margin-bottom: 0.55rem;
                text-decoration: none !important;
                color: #0f1f3f !important;
                border-radius: 16px;
                border: 1.5px solid #d9e5f6;
                background: linear-gradient(140deg, #ffffff 0%, #f5f9ff 100%);
                box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
                transition: transform 0.28s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.3s ease, border-color 0.3s ease;
            }

            .quick-action-link[data-category="operacion"] {
                border-color: #c9e2ff;
                background: linear-gradient(140deg, #ffffff 0%, #eef6ff 100%);
            }

            .quick-action-link[data-category="analisis"] {
                border-color: #cdecd6;
                background: linear-gradient(140deg, #ffffff 0%, #edf9f1 100%);
            }

            .quick-action-link[data-category="administracion"] {
                border-color: #f3dfbd;
                background: linear-gradient(140deg, #ffffff 0%, #fff7eb 100%);
            }

            .quick-action-link:hover {
                transform: translateY(-3px);
                border-color: #b9d5f8;
                box-shadow: 0 14px 30px rgba(37, 99, 235, 0.16);
            }

            .quick-action-icon {
                width: 42px;
                height: 42px;
                border-radius: 12px;
                background: linear-gradient(165deg, #e8f1ff 0%, #f7fbff 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.25rem;
                flex-shrink: 0;
                border: 1px solid #d4e2f6;
            }

            .quick-action-link[data-category="operacion"] .quick-action-icon {
                background: linear-gradient(165deg, #e6f2ff 0%, #f5faff 100%);
                border-color: #c9ddf9;
            }

            .quick-action-link[data-category="analisis"] .quick-action-icon {
                background: linear-gradient(165deg, #e7f8ee 0%, #f4fcf7 100%);
                border-color: #c7e8d3;
            }

            .quick-action-link[data-category="administracion"] .quick-action-icon {
                background: linear-gradient(165deg, #fff1dd 0%, #fff8ef 100%);
                border-color: #f2d7ad;
            }

            .quick-action-content {
                flex: 1;
                min-width: 0;
            }

            .quick-action-title {
                font-size: 0.98rem;
                font-weight: 800;
                color: #0f1f3f;
                line-height: 1.1;
            }

            .quick-action-subtitle {
                margin-top: 0.2rem;
                font-size: 0.74rem;
                color: #64748b;
                line-height: 1.25;
            }

            .quick-action-arrow {
                color: #2563eb;
                font-weight: 800;
                font-size: 1rem;
                opacity: 0.6;
                transition: transform 0.28s ease, opacity 0.28s ease;
            }

            .quick-action-link[data-category="analisis"] .quick-action-arrow {
                color: #0f9f59;
            }

            .quick-action-link[data-category="administracion"] .quick-action-arrow {
                color: #c77a17;
            }

            .quick-action-link:hover .quick-action-arrow {
                transform: translateX(3px);
                opacity: 1;
            }

            .stTextInput input, .stTextArea textarea, .stDateInput input, .stSelectbox div[data-baseweb="select"], .stMultiSelect div[data-baseweb="select"] {
                background: linear-gradient(135deg, #ffffff 0%, #fafbff 100%) !important;
                color: var(--text) !important;
                border: 1.5px solid var(--border) !important;
                border-radius: 14px !important;
                min-height: 46px !important;
                box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04) !important;
                transition: all 0.3s ease !important;
            }

            .stTextInput input::placeholder, .stTextArea textarea::placeholder {
                color: #cbd5e1 !important;
                font-weight: 500;
            }

            .stTextInput input:focus, .stTextArea textarea:focus {
                border-color: var(--primary) !important;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1), 0 0 0 1.5px var(--primary) !important;
                background: linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%) !important;
            }

            .stSelectbox div[data-baseweb="select"]:focus-within,
            .stMultiSelect div[data-baseweb="select"]:focus-within {
                border-color: var(--primary) !important;
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1), 0 0 0 1.5px var(--primary) !important;
            }

            .stButton > button {
                border-radius: 16px;
                border: 1px solid transparent;
                min-height: 48px;
                font-weight: 700;
                transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
                padding: 0.6rem 1.4rem !important;
                letter-spacing: 0.3px;
            }

            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 12px 32px rgba(37, 99, 235, 0.24);
            }

            .stButton > button:active {
                transform: translateY(0px);
            }

            .stButton > button[kind="primary"], .stDownloadButton > button {
                background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
                color: white;
                border-color: transparent;
                box-shadow: 0 8px 16px rgba(37, 99, 235, 0.2);
            }

            .stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover {
                background: linear-gradient(135deg, #1D4ED8 0%, #1e40af 100%);
            }

            .stButton > button[kind="secondary"] {
                background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
                color: var(--text);
                border-color: #e2e8f0;
                box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
            }

            .stButton > button[kind="secondary"]:hover {
                background: linear-gradient(135deg, #f8fbff 0%, #f1f5f9 100%);
                border-color: #cbd5e1;
            }

            .login-intro-card {
                text-align: center;
                margin-bottom: 0.5rem;
                padding: 0.7rem 0.8rem 0.35rem 0.8rem;
            }

            .login-icon {
                width: 52px;
                height: 52px;
                border-radius: 14px;
                margin: 0 auto 0.45rem auto;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.35rem;
                background: linear-gradient(160deg, #dbeafe 0%, #eff6ff 100%);
                border: 1px solid #bfdbfe;
                color: #1d4ed8;
            }

            [data-testid="stForm"] {
                background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
                border: 1px solid #d8e4f4;
                border-radius: 22px;
                padding: 1.05rem 1rem 0.85rem 1rem;
                box-shadow: 0 16px 34px rgba(15, 23, 42, 0.08);
            }

            [data-testid="stForm"] [data-testid="stFormSubmitButton"] {
                margin-top: 0.2rem;
            }

            [data-testid="stFileUploaderDropzoneInstructions"] {
                position: relative;
            }

            [data-testid="stFileUploaderDropzoneInstructions"] * {
                color: transparent !important;
                font-size: 0 !important;
            }

            [data-testid="stFileUploaderDropzoneInstructions"]::before {
                content: "Arrastra y suelta el archivo aqui";
                display: block;
                font-size: 2rem;
                font-weight: 700;
                color: var(--text);
                line-height: 1.2;
            }

            [data-testid="stFileUploaderDropzoneInstructions"]::after {
                content: "Limite 200 MB por archivo";
                display: block;
                margin-top: 0.35rem;
                font-size: 1.05rem;
                color: var(--muted);
                font-weight: 500;
            }

            [data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"] p {
                color: transparent !important;
                font-size: 0 !important;
            }

            [data-testid="stFileUploaderDropzone"] button {
                font-size: 0 !important;
            }

            [data-testid="stFileUploaderDropzone"] button::after {
                content: "Buscar archivos";
                font-size: 1.05rem;
                font-weight: 600;
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
                animation: fadeUp 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both;
            }

            @keyframes fadeUp {
                from { opacity: 0; transform: translateY(16px); }
                to { opacity: 1; transform: translateY(0); }
            }

            @keyframes slideInLeft {
                from { opacity: 0; transform: translateX(-20px); }
                to { opacity: 1; transform: translateX(0); }
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }

            [data-testid="stForm"] {
                animation: fadeUp 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) 0.1s both;
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


def get_logo_embed() -> str:
    """Return logo as embedded base64 data URI."""
    import base64
    import os
    try:
        # Usa ruta absoluta basada en el directorio del archivo actual
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(os.path.dirname(current_dir), 'assets', 'logo.png')
        with open(logo_path, 'rb') as f:
            logo_b64 = base64.b64encode(f.read()).decode()
            return f'data:image/png;base64,{logo_b64}'
    except Exception as e:
        print(f'Error al cargar logo: {e}')
        return ''


def render_sidebar(user: dict | None = None) -> None:
    with st.sidebar:
        # Mostrar logo y marca
        try:
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(os.path.dirname(current_dir), 'assets', 'logo.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    import base64
                    logo_b64 = base64.b64encode(f.read()).decode()
                    logo_uri = f'data:image/png;base64,{logo_b64}'
                    st.markdown(
                        f"""
                        <div class="sidebar-shell" style="display:flex; align-items:center; gap:0.8rem; margin-bottom:0.5rem;">
                          <img src="{logo_uri}" alt="Campusly" style="width:70px; height:70px; object-fit:contain; flex-shrink:0;">
                          <div>
                            <div class="brand-title" style="font-size: 1.4rem; margin:0;">Campusly</div>
                            <div class="brand-subtitle">Asistencia docente</div>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    """
                    <div class="sidebar-shell">
                      <div class="brand-card">
                        <div style="display:flex; align-items:center; gap:0.8rem;">
                          <div class="brand-mark">C</div>
                          <div>
                            <div class="brand-title">Campusly</div>
                            <div class="brand-subtitle">Asistencia docente</div>
                          </div>
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        except Exception as e:
            st.markdown(
                """
                <div class="sidebar-shell">
                  <div class="brand-card">
                    <div style="display:flex; align-items:center; gap:0.8rem;">
                      <div class="brand-mark">C</div>
                      <div>
                        <div class="brand-title">Campusly</div>
                        <div class="brand-subtitle">Asistencia docente</div>
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
                <div class="session-card reveal-card">
                  <div class="session-label">Sesión activa</div>
                  <div class="session-name">{user['nombre']}</div>
                  <div class="session-role">{user['rol']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown('<div class="nav-title">Navegación</div>', unsafe_allow_html=True)
            for page_path, label, icon in _allowed_sidebar_pages(user.get("rol", "")):
                st.page_link(page_path, label=label, icon=icon, use_container_width=True)

        st.markdown(
            f"""
            <div class="sidebar-credit">
                Desarrollado por {APP_AUTHOR}
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
        try:
            st.switch_page("app.py")
        except Exception:
            st.warning("Debes iniciar sesión para continuar.")
        st.stop()
    if roles and user["rol"] not in roles:
        st.error("No tienes permisos para acceder a esta sección.")
        st.stop()
    return user


def logout_and_redirect() -> None:
    st.session_state.pop("auth_user", None)
    st.session_state.pop("auth_token", None)
    try:
        st.switch_page("app.py")
    except Exception:
        st.rerun()


def logout_button() -> None:
    if st.sidebar.button("Cerrar sesión", use_container_width=True):
        logout_and_redirect()

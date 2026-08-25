from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from database.db import get_session
from database.models import Asistencia, Docente
from services.reports import AttendanceFilters, ReportService
from services.time_utils import today_local
from services.ui import APP_NAME, configure_page, logout_button, page_hero, require_login, render_sidebar, styled_attendance_table


def _period_dates(periodo: str) -> tuple[date, date]:
    today = today_local()
    if periodo == "Diario":
        return today, today
    if periodo == "Semanal":
        return today - timedelta(days=6), today
    return today.replace(day=1), today


def _filter_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    docente_options = ["Todos"] + sorted(df["docente"].dropna().astype(str).unique().tolist()) if "docente" in df.columns else ["Todos"]
    departamento_options = ["Todos"] + sorted(df["departamento"].dropna().astype(str).unique().tolist()) if "departamento" in df.columns else ["Todos"]
    estatus_options = ["Todos"] + sorted(df["estatus"].dropna().astype(str).unique().tolist()) if "estatus" in df.columns else ["Todos"]

    col1, col2, col3 = st.columns(3)
    docente = col1.selectbox("Docente", docente_options, key="report_docente_filter")
    departamento = col2.selectbox("Departamento", departamento_options, key="report_departamento_filter")
    estatus = col3.selectbox("Estatus", estatus_options, key="report_estatus_filter")

    filtered = df.copy()
    if docente != "Todos" and "docente" in filtered.columns:
        filtered = filtered[filtered["docente"].astype(str) == docente]
    if departamento != "Todos" and "departamento" in filtered.columns:
        filtered = filtered[filtered["departamento"].astype(str) == departamento]
    if estatus != "Todos" and "estatus" in filtered.columns:
        filtered = filtered[filtered["estatus"].astype(str) == estatus]
    return filtered


def _load_custom_options() -> tuple[list[tuple[str, int]], list[str], list[str], list[int]]:
    with get_session() as session:
        docentes = session.query(Docente).order_by(Docente.apellido_paterno, Docente.apellido_materno, Docente.nombre).all()
        turnos = [row[0] for row in session.query(Asistencia.turno).distinct().order_by(Asistencia.turno).all()]
        departamentos = [row[0] for row in session.query(Docente.departamento).distinct().order_by(Docente.departamento).all()]
        years = [row[0] for row in session.query(Asistencia.anio).distinct().order_by(Asistencia.anio).all()]

    docente_options = [(f"{docente.numero_empleado} - {docente.nombre} {docente.apellidos}".strip(), docente.id) for docente in docentes]
    return docente_options, [turno for turno in turnos if turno], [departamento for departamento in departamentos if departamento], [int(year) for year in years if year is not None]


def main() -> None:
    configure_page(f"{APP_NAME} | Reportes")
    user = require_login(["Administrador", "Prefecto"])

    render_sidebar(user)
    logout_button()

    page_hero("Reportes", "Genera reportes diarios, semanales y mensuales con exportación a Excel o CSV.")

    modo_consulta = st.radio("Modo de consulta", ["Rápida", "Personalizada"], horizontal=True)
    export_suffix = "custom"

    if modo_consulta == "Rápida":
        periodo = st.radio("Tipo de reporte", ["Diario", "Semanal", "Mensual"], horizontal=True)
        fecha_inicio, fecha_fin = _period_dates(periodo)
        export_suffix = periodo.lower()

        filters = AttendanceFilters(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
        df = ReportService.fetch_attendances(filters)

        st.markdown(f"**Periodo:** {fecha_inicio.isoformat()} a {fecha_fin.isoformat()}")
    else:
        docente_options, turno_options, departamento_options, year_options = _load_custom_options()
        year_options = year_options or [today_local().year]
        with st.form("custom_report_form"):
            st.markdown("### Consulta personalizada")
            c1, c2 = st.columns(2)
            fecha_inicio = c1.date_input("Fecha inicial", value=today_local() - timedelta(days=30))
            fecha_fin = c2.date_input("Fecha final", value=today_local())

            c3, c4 = st.columns(2)
            docente_label = c3.selectbox("Docente", ["Todos"] + [label for label, _ in docente_options], index=0)
            turno = c4.selectbox("Turno", ["Todos"] + turno_options, index=0)

            c5, c6 = st.columns(2)
            departamento = c5.selectbox("Departamento", ["Todos"] + departamento_options, index=0)
            estatus = c6.selectbox("Estatus", ["Todos", "Puntual", "Retardo", "Falta"], index=0)

            c7, c8 = st.columns(2)
            anio = c7.selectbox("Año académico", ["Todos"] + year_options, index=0)
            cuatrimestre = c8.selectbox("Cuatrimestre", ["Todos", 1, 2, 3], index=0)

            submit = st.form_submit_button("Buscar", use_container_width=True, type="primary")

        if not submit:
            st.info("Completa los filtros y pulsa Buscar para ejecutar la consulta.")
            st.stop()

        if fecha_inicio > fecha_fin:
            st.error("La fecha inicial no puede ser mayor que la final.")
            st.stop()

        docente_id = None
        if docente_label != "Todos":
            docente_id = next((docente_id for label, docente_id in docente_options if label == docente_label), None)
        filters = AttendanceFilters(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            docente_id=docente_id,
            departamento=None if departamento == "Todos" else departamento,
            estatus=None if estatus == "Todos" else estatus,
            turno=None if turno == "Todos" else turno,
            anio=None if anio == "Todos" else int(anio),
            cuatrimestre=None if cuatrimestre == "Todos" else int(cuatrimestre),
        )
        df = ReportService.fetch_attendances(filters)
        df = _filter_frame(df)
        st.markdown(f"**Consulta:** {fecha_inicio.isoformat()} a {fecha_fin.isoformat()}")

    if df.empty:
        st.info("No se encontraron registros con los filtros seleccionados.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Registros", len(df))
        c2.metric("Docentes únicos", df["docente"].nunique() if "docente" in df.columns else 0)
        c3.metric("Días con registros", df["fecha"].nunique() if "fecha" in df.columns else 0)
        st.dataframe(styled_attendance_table(df), use_container_width=True)

    c1, c2 = st.columns(2)
    csv_data = ReportService.export_csv(df)
    excel_data = ReportService.export_excel(df)
    c1.download_button(
        "Exportar CSV",
        data=csv_data,
        file_name=f"reporte_{export_suffix}.csv",
        mime="text/csv",
        use_container_width=True,
        disabled=df.empty,
    )
    c2.download_button(
        "Exportar Excel",
        data=excel_data,
        file_name=f"reporte_{export_suffix}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        disabled=df.empty,
    )


if __name__ == "__main__":
    main()

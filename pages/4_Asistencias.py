from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from database.db import init_db
from database.models import Docente
from services.reports import AttendanceFilters, ReportService
from services.time_utils import today_local
from services.ui import APP_NAME, configure_page, logout_button, page_hero, require_login, render_sidebar, styled_attendance_table


def main() -> None:
    init_db()
    configure_page(f"{APP_NAME} | Asistencias")
    user = require_login(["Administrador", "Prefecto"])

    render_sidebar(user)
    logout_button()

    page_hero("Consulta de asistencias", "Filtra por fecha, docente, departamento y estatus con una vista moderna y legible.")

    with st.form("filters_form"):
        c1, c2 = st.columns(2)
        default_date = today_local()
        fecha_inicio = c1.date_input("Fecha inicial", value=default_date)
        fecha_fin = c2.date_input("Fecha final", value=default_date)

        anios = ReportService.available_years()
        if default_date.year not in anios:
            anios = [default_date.year] + anios
        anio_options = ["Todos"] + [str(a) for a in sorted(set(anios), reverse=True)]
        cuatrimestre_options = [
            "Todos",
            "1 - Enero-Abril",
            "2 - Mayo-Agosto",
            "3 - Septiembre-Diciembre",
        ]

        docentes_df = pd.DataFrame()
        with st.spinner("Cargando docentes..."):
            from database.db import get_session
            from sqlalchemy import select

            with get_session() as session:
                docentes = session.execute(select(Docente).order_by(Docente.apellidos, Docente.nombre)).scalars().all()
                docentes_records = [
                    {"id": d.id, "nombre": f"{d.nombre} {d.apellidos}", "departamento": d.departamento} for d in docentes
                ]
            docentes_df = pd.DataFrame(docentes_records)

        docente_options = ["Todos"] + (docentes_df["nombre"].tolist() if not docentes_df.empty else [])
        departamento_options = ["Todos"] + sorted(docentes_df["departamento"].dropna().unique().tolist()) if not docentes_df.empty else ["Todos"]
        estatus_options = ["Todos", "Asistencia"]

        c3, c4 = st.columns(2)
        docente_label = c3.selectbox("Docente", docente_options)
        departamento = c4.selectbox("Departamento", departamento_options)
        c5, c6 = st.columns(2)
        anio_label = c5.selectbox("Año", anio_options)
        cuatrimestre_label = c6.selectbox("Cuatrimestre", cuatrimestre_options)
        estatus = st.selectbox("Estatus", estatus_options)
        submit = st.form_submit_button("Aplicar filtros", use_container_width=True)

    if submit:
        docente_id = None
        if docente_label != "Todos" and not docentes_df.empty:
            docente_id = int(docentes_df.loc[docentes_df["nombre"] == docente_label, "id"].iloc[0])

        filters = AttendanceFilters(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            docente_id=docente_id,
            departamento=None if departamento == "Todos" else departamento,
            estatus=None if estatus == "Todos" else estatus,
            anio=None if anio_label == "Todos" else int(anio_label),
            cuatrimestre=None if cuatrimestre_label == "Todos" else int(cuatrimestre_label.split(" - ")[0]),
        )
        df = ReportService.fetch_attendances(filters)
        if df.empty:
            st.info("No se encontraron registros con los filtros aplicados.")
        else:
            st.dataframe(styled_attendance_table(df), use_container_width=True)


if __name__ == "__main__":
    main()

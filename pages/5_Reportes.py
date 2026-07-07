from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

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


def main() -> None:
    from database.db import init_db
    init_db()
    configure_page(f"{APP_NAME} | Reportes")
    user = require_login(["Administrador", "Prefecto"])

    render_sidebar(user)
    logout_button()

    page_hero("Reportes", "Genera reportes diarios, semanales y mensuales con exportación a Excel o CSV.")

    periodo = st.radio("Tipo de reporte", ["Diario", "Semanal", "Mensual"], horizontal=True)
    fecha_inicio, fecha_fin = _period_dates(periodo)

    filters = AttendanceFilters(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)
    df = ReportService.fetch_attendances(filters)

    st.markdown(f"**Periodo:** {fecha_inicio.isoformat()} a {fecha_fin.isoformat()}")

    if df.empty:
        st.info("No hay registros de asistencia en el periodo seleccionado.")
    else:
        st.dataframe(styled_attendance_table(df), use_container_width=True)
        c1, c2 = st.columns(2)
        csv_data = ReportService.export_csv(df)
        excel_data = ReportService.export_excel(df)
        c1.download_button(
            "Exportar CSV",
            data=csv_data,
            file_name=f"reporte_{periodo.lower()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        c2.download_button(
            "Exportar Excel",
            data=excel_data,
            file_name=f"reporte_{periodo.lower()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()

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


def _cuatrimestre_dates(anio: int, cuatrimestre: int) -> tuple[date, date]:
    if cuatrimestre == 1:
        return date(anio, 1, 1), date(anio, 4, 30)
    if cuatrimestre == 2:
        return date(anio, 5, 1), date(anio, 8, 31)
    return date(anio, 9, 1), date(anio, 12, 31)


@st.cache_data(ttl=300)
def _get_attendance_data(
    fecha_inicio: date,
    fecha_fin: date,
    anio: int | None,
    cuatrimestre: int | None,
) -> pd.DataFrame:
    """Obtiene datos de asistencia con caché de 5 minutos."""
    filters = AttendanceFilters(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        anio=anio,
        cuatrimestre=cuatrimestre,
    )
    return ReportService.fetch_attendances(filters)


def main() -> None:
    from database.db import init_db
    init_db()
    configure_page(f"{APP_NAME} | Reportes")
    user = require_login(["Administrador", "Prefecto"])

    render_sidebar(user)
    logout_button()

    page_hero("Reportes", "Genera reportes diarios, semanales y mensuales con exportación a Excel o CSV.")

    periodo = st.radio("Tipo de reporte", ["Diario", "Semanal", "Mensual", "Cuatrimestral"], horizontal=True)

    anio_filtro: int | None = None
    cuatrimestre_filtro: int | None = None
    if periodo == "Cuatrimestral":
        anios = ReportService.available_years()
        current_year = today_local().year
        if current_year not in anios:
            anios = [current_year] + anios
        c1, c2 = st.columns(2)
        anio_filtro = c1.selectbox("Año", sorted(set(anios), reverse=True))
        cuatrimestre_filtro = c2.selectbox(
            "Cuatrimestre",
            [1, 2, 3],
            format_func=lambda x: {
                1: "1 - Enero-Abril",
                2: "2 - Mayo-Agosto",
                3: "3 - Septiembre-Diciembre",
            }[x],
        )
        fecha_inicio, fecha_fin = _cuatrimestre_dates(anio_filtro, cuatrimestre_filtro)
    else:
        fecha_inicio, fecha_fin = _period_dates(periodo)

    df = _get_attendance_data(fecha_inicio, fecha_fin, anio_filtro, cuatrimestre_filtro)

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

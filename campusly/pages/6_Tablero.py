from __future__ import annotations

from datetime import date, timedelta

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from services.reports import ReportService
from services.time_utils import today_local
from services.ui import APP_NAME, configure_page, logout_button, metric_card, page_hero, render_sidebar, require_login, styled_attendance_table


def _metrics_to_columns(metrics: dict[str, int]) -> None:
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    c1.markdown(metric_card("Total docentes", metrics["total_docentes"], "Base operativa", "primary"), unsafe_allow_html=True)
    c2.markdown(metric_card("Presentes", metrics["presentes"], "+ hoy", "success"), unsafe_allow_html=True)
    c3.markdown(metric_card("Retardos", metrics["retardos"], "Monitoreo puntual", "warning"), unsafe_allow_html=True)
    c4.markdown(metric_card("Ausentes", metrics["ausentes"], "Pendientes del día", "error"), unsafe_allow_html=True)


def main() -> None:
    from database.db import init_db
    init_db()
    configure_page(f"{APP_NAME} | Tablero")
    user = require_login(["Administrador", "Prefecto"])

    render_sidebar(user)
    logout_button()

    page_hero("Tablero", "Resumen ejecutivo de asistencia docente con métricas, tendencias y últimos registros.")

    metrics = ReportService.summary_totals()
    _metrics_to_columns(metrics)

    end_date = today_local()
    start_date = end_date - timedelta(days=6)
    daily_df = ReportService.daily_summary(start_date, end_date)
    department_df = ReportService.department_summary(start_date, end_date)
    monthly_df = ReportService.monthly_trend(end_date.year)
    latest_df = ReportService.latest_records(limit=8)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Tendencia semanal")
        if daily_df.empty:
            st.info("No hay datos para el periodo seleccionado.")
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=daily_df["fecha"], y=daily_df["total"], mode="lines+markers", name="Total", line=dict(color="#2563EB", width=3)))
            fig.add_trace(go.Scatter(x=daily_df["fecha"], y=daily_df["puntual"], mode="lines+markers", name="Puntual", line=dict(color="#10B981", width=3)))
            fig.add_trace(go.Scatter(x=daily_df["fecha"], y=daily_df["retardo"], mode="lines+markers", name="Retardo", line=dict(color="#F59E0B", width=3)))
            fig.update_layout(
                template="plotly_white",
                height=380,
                margin=dict(l=12, r=12, t=24, b=12),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#FFFFFF",
                font=dict(family="Inter, sans-serif", color="#0F172A"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            )
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(gridcolor="#E2E8F0", zeroline=False)
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Asistencia por departamento")
        if department_df.empty:
            st.info("No hay datos para el periodo seleccionado.")
        else:
            fig = px.bar(
                department_df,
                x="departamento",
                y="total",
                color="total",
                color_continuous_scale=["#DBEAFE", "#2563EB"],
                template="plotly_white",
            )
            fig.update_layout(
                height=380,
                showlegend=False,
                margin=dict(l=12, r=12, t=24, b=12),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#FFFFFF",
                font=dict(family="Inter, sans-serif", color="#0F172A"),
            )
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(gridcolor="#E2E8F0", zeroline=False)
            st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns([1.2, 0.8], gap="medium")
    with c3:
        st.subheader("Tendencia mensual")
        if monthly_df.empty:
            st.info("Sin información mensual todavía.")
        else:
            fig = px.line(monthly_df, x="mes", y="total", markers=True, template="plotly_white")
            fig.update_traces(line=dict(color="#2563EB", width=3), marker=dict(size=9, color="#2563EB"))
            fig.update_xaxes(dtick=1, showgrid=False)
            fig.update_yaxes(gridcolor="#E2E8F0", zeroline=False)
            fig.update_layout(
                height=360,
                margin=dict(l=12, r=12, t=24, b=12),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#FFFFFF",
                font=dict(family="Inter, sans-serif", color="#0F172A"),
            )
            st.plotly_chart(fig, use_container_width=True)
    with c4:
        st.subheader("Últimos registros")
        if latest_df.empty:
            st.info("Sin registros recientes.")
        else:
            st.dataframe(styled_attendance_table(latest_df), use_container_width=True, height=360)


if __name__ == "__main__":
    main()

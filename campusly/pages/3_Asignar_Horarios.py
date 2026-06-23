from __future__ import annotations

import streamlit as st
from datetime import datetime
from sqlalchemy import select

from database.db import get_session, init_db
from database.models import Docente, Turno, HoraClase, DocenteHoraClase
from services.ui import APP_NAME, configure_page, logout_button, page_hero, require_login, render_sidebar


def _get_docentes() -> dict[str, int]:
    """Obtiene docentes activos."""
    with get_session() as session:
        docentes = session.execute(
            select(Docente)
            .where(Docente.activo.is_(True))
            .order_by(Docente.apellido_paterno, Docente.apellido_materno, Docente.nombre)
        ).scalars().all()
        return {f"{d.numero_empleado} - {d.nombre} {d.apellidos}".strip(): d.id for d in docentes}


def _get_turnos() -> dict[str, int]:
    """Obtiene turnos disponibles."""
    with get_session() as session:
        turnos = session.execute(select(Turno).order_by(Turno.nombre)).scalars().all()
        return {t.nombre: t.id for t in turnos}


def _get_horas_clase(turno_id: int) -> dict[str, int]:
    """Obtiene horas clase para un turno."""
    with get_session() as session:
        horas = session.execute(
            select(HoraClase)
            .where(HoraClase.turno_id == turno_id)
            .order_by(HoraClase.numero)
        ).scalars().all()
        return {f"Hora {h.numero} ({h.hora_inicio.strftime('%H:%M')}-{h.hora_fin.strftime('%H:%M')})": h.id for h in horas}


def _get_existing_assignments(docente_id: int) -> list[dict]:
    """Obtiene asignaciones existentes de un docente."""
    with get_session() as session:
        assignments = session.execute(
            select(DocenteHoraClase)
            .where(DocenteHoraClase.docente_id == docente_id)
            .order_by(DocenteHoraClase.turno_id, DocenteHoraClase.numero_hora)
        ).scalars().all()
        
        result = []
        for a in assignments:
            with get_session() as s2:
                turno = s2.get(Turno, a.turno_id)
                dia_semana_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
                result.append({
                    "id": a.id,
                    "turno": turno.nombre if turno else "N/A",
                    "hora": a.numero_hora,
                    "salon": a.salon,
                    "grupo": a.grupo,
                    "dia_semana": dia_semana_names[a.dia_semana] if a.dia_semana < 5 else "Sábado",
                })
        return result


def _delete_assignment(assignment_id: int) -> bool:
    """Elimina una asignación."""
    with get_session() as session:
        assignment = session.get(DocenteHoraClase, assignment_id)
        if assignment:
            session.delete(assignment)
            session.commit()
            return True
        return False


def main() -> None:
    init_db()
    configure_page(f"{APP_NAME} | Asignar Horarios")
    user = require_login(["Administrador", "Prefecto"])

    render_sidebar(user)
    logout_button()

    page_hero("Asignar Horarios", "Gestiona la asignación de docentes a turnos, horas y salones.")

    docentes = _get_docentes()
    if not docentes:
        st.error("No hay docentes activos en el sistema.")
        st.stop()

    # Seleccionar docente
    docente_label = st.selectbox("Seleccionar Docente", list(docentes.keys()))
    docente_id = docentes[docente_label]

    # Mostrar asignaciones existentes
    existing = _get_existing_assignments(docente_id)
    if existing:
        st.markdown("### Asignaciones Actuales")
        for i, assignment in enumerate(existing):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{assignment['turno']}** - Hora {assignment['hora']} - Salón {assignment['salon']} - Grupo {assignment['grupo']} - {assignment['dia_semana']}")
            with col2:
                if st.button("❌ Eliminar", key=f"delete_{assignment['id']}", use_container_width=True):
                    if _delete_assignment(assignment['id']):
                        st.success("Asignación eliminada")
                        st.rerun()

    # Nueva asignación
    st.markdown("### Nueva Asignación")

    turnos = _get_turnos()
    if not turnos:
        st.error("No hay turnos configurados.")
        st.stop()

    turno_label = st.selectbox("Turno", list(turnos.keys()), key="turno_new")
    turno_id = turnos[turno_label]

    horas = _get_horas_clase(turno_id)
    if not horas:
        st.error(f"No hay horas clase para {turno_label}.")
        st.stop()

    hora_label = st.selectbox("Hora Clase", list(horas.keys()), key="hora_new")
    hora_clase_id = horas[hora_label]

    col1, col2 = st.columns(2)
    with col1:
        salon = st.text_input("Salón", placeholder="Ej: A-101")
    with col2:
        grupo = st.text_input("Grupo", placeholder="Ej: TSU-101")

    dias_semana = st.multiselect(
        "Días de la Semana",
        options=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
        default=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
    )

    if st.button("Guardar Asignación", use_container_width=True, type="primary"):
        if not salon or not grupo or not dias_semana:
            st.error("Completa todos los campos.")
            st.stop()

        with get_session() as session:
            dia_map = {"Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4}
            success_count = 0
            for dia_nombre in dias_semana:
                dia_numero = dia_map[dia_nombre]
                existing_check = session.scalar(
                    select(DocenteHoraClase).where(
                        DocenteHoraClase.docente_id == docente_id,
                        DocenteHoraClase.turno_id == turno_id,
                        DocenteHoraClase.hora_clase_id == hora_clase_id,
                        DocenteHoraClase.dia_semana == dia_numero,
                        DocenteHoraClase.salon == salon,
                    )
                )
                if not existing_check:
                    new_assignment = DocenteHoraClase(
                        docente_id=docente_id,
                        turno_id=turno_id,
                        hora_clase_id=hora_clase_id,
                        numero_hora=int(hora_label.split()[1]),
                        dia_semana=dia_numero,
                        salon=salon,
                        grupo=grupo,
                    )
                    session.add(new_assignment)
                    success_count += 1
            
            if success_count > 0:
                session.commit()
                st.success(f"✅ {success_count} asignación(es) guardada(s)")
                st.rerun()
            else:
                st.info("Las asignaciones ya existen.")


if __name__ == "__main__":
    main()

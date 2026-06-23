"""
Página de carga de horarios desde PDF
Los docentes reciben sus horarios en formato PDF (aSc Horarios) y pueden
cargarlos directamente en el sistema.
"""

from __future__ import annotations

import tempfile
import os
import streamlit as st

from database.db import init_db, get_session
from database.models import Docente, DocenteHoraClase, HoraClase, Turno
from services.pdf_horario_import import PDFHorarioImportService
from services.ui import APP_NAME, configure_page, logout_button, page_hero, require_login, render_sidebar


def main() -> None:
    init_db()
    configure_page(f"{APP_NAME} | Cargar Horarios")
    user = require_login(["Administrador", "Docente"])

    render_sidebar(user)
    logout_button()

    page_hero(
        "📅 Cargar Horarios desde PDF",
        "Carga tu archivo PDF de horario (formato aSc Horarios)"
    )

    # Sección de información
    with st.expander("ℹ️ Instrucciones", expanded=True):
        st.markdown("""
        ### 📋 Cómo funciona
        
        1. **Descarga tu horario en PDF** desde el sistema de la universidad
        2. **Carga el archivo PDF** en esta página
        3. El sistema extrae automáticamente:
           - Tu nombre
           - Turno (Matutino/Nocturno)
           - Todas tus clases, salones y grupos
        4. **Revisa la vista previa** y confirma la importación
        
        ### ✅ Requisitos del PDF
        
        - Debe ser un PDF generado por **aSc Horarios**
        - Debe incluir tu nombre y turno
        - Debe contener la tabla con tus clases
        
        ### 📝 Notas importantes
        
        - Si trabajas en **ambos turnos**, carga primero el Matutino y luego el Nocturno
        - Cada turno se importará por separado
        - Puedes cargar nuevamente para actualizar tus horarios
        """)

    # Sección de carga de archivo
    st.markdown("### Seleccionar Archivo")
    
    uploaded_file = st.file_uploader(
        "Carga tu horario en PDF (formato aSc Horarios)",
        type=["pdf"],
        help="Selecciona el PDF de tu horario generado por aSc Horarios"
    )

    if uploaded_file is None:
        st.info("👈 Carga un archivo PDF para comenzar")
        return

    # Guardar archivo temporalmente
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        tmp_path = tmp_file.name

    try:
        # Procesar PDF
        with st.spinner("🔍 Analizando PDF..."):
            service = PDFHorarioImportService()
            result = service.import_from_pdf(tmp_path)

        # Mostrar resultado
        if result.success:
            st.success("✅ PDF procesado correctamente")

            # Mostrar información extraída
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("👨‍🏫 Docente", result.docente_nombre or "N/A")
            with col2:
                st.metric("⏰ Turno", result.turno or "N/A")
            with col3:
                st.metric("📚 Registros", result.entries_count or 0)

            # Mostrar número de empleado
            if result.numero_empleado:
                st.info(f"**Clave de empleado:** `{result.numero_empleado}`")

            # Mostrar tabla de preview
            st.subheader("📋 Vista previa de tu horario")

            # Extraer datos para preview
            service_preview = PDFHorarioImportService()
            success, entries, _ = service_preview.extractor.extract_from_pdf(tmp_path)

            if entries:
                # Organizar por día
                by_day = {}
                for entry in entries:
                    if entry.dia_semana not in by_day:
                        by_day[entry.dia_semana] = []
                    by_day[entry.dia_semana].append(entry)

                # Mostrar tabla por día
                tabs = st.tabs(list(by_day.keys()))
                for tab, dia in zip(tabs, by_day.keys()):
                    with tab:
                        day_entries = sorted(by_day[dia], key=lambda x: x.numero_hora)
                        data = [
                            {
                                "Hora": f"Hora {e.numero_hora}",
                                "Código": e.grupo_codigo,
                                "Materia": e.materia_nombre,
                                "Salón": e.salon,
                            }
                            for e in day_entries
                        ]
                        st.dataframe(data, use_container_width=True, hide_index=True)

            # Opciones de importación
            st.subheader("⚙️ Opciones de importación")
            clear_existing = st.checkbox(
                "🗑️ Limpiar horarios anteriores",
                help="Marca esto si quieres reemplazar tu horario anterior"
            )

            if st.button("✅ Importar Horario", type="primary", use_container_width=True):
                with st.spinner("⏳ Importando a la base de datos..."):
                    import_result = _import_to_db(result, entries, clear_existing)

                if import_result["success"]:
                    st.success(import_result["message"])
                    st.balloons()

                    # Mostrar estadísticas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("✅ Importados", import_result["imported_count"])
                    with col2:
                        st.metric("⏭️ Duplicados", import_result.get("skipped_count", 0))
                    with col3:
                        st.metric("❌ Errores", len(import_result.get("errors", [])))

                    # Mostrar errores si hay
                    if import_result.get("errors"):
                        with st.expander("📋 Detalles"):
                            for error in import_result["errors"][:10]:
                                st.error(f"  • {error}")
                else:
                    st.error(f"❌ Error: {import_result['message']}")
                    if import_result.get("errors"):
                        with st.expander("📋 Detalles del error"):
                            for error in import_result["errors"]:
                                st.error(f"  • {error}")

        else:
            st.error("❌ Error al procesar PDF")
            st.error(f"**Mensaje:** {result.message}")

            if result.errors:
                with st.expander("📋 Errores detallados"):
                    for error in result.errors:
                        st.error(f"  • {error}")

            st.info(
                """
                **Posibles causas:**
                - El PDF no está en formato aSc Horarios
                - El PDF está corrupto o protegido
                - Falta el nombre del docente o turno
                - La tabla de horario no se puede leer
                
                **Recomendación:** Descarga nuevamente tu horario desde el sistema de la universidad
                """
            )

    finally:
        # Limpiar archivo temporal
        try:
            os.unlink(tmp_path)
        except:
            pass


def _import_to_db(result, entries, clear_existing: bool) -> dict:
    """
    Importa los datos extraídos a la base de datos
    """
    try:
        with get_session() as session:
            # 1. Buscar o crear docente
            numero_empleado = result.numero_empleado
            docente = session.query(Docente).filter_by(
                numero_empleado=numero_empleado
            ).first()

            if not docente:
                docente = Docente(
                    numero_empleado=numero_empleado,
                    nombre=result.docente_nombre,
                    email="",
                    qr_uuid="",
                    tipo_usuario="Docente",
                )
                session.add(docente)
                session.flush()

            # 2. Obtener turno
            turno = session.query(Turno).filter_by(nombre=result.turno).first()
            if not turno:
                return {
                    "success": False,
                    "message": f"Turno '{result.turno}' no encontrado",
                    "errors": [f"El turno '{result.turno}' no está configurado en el sistema"],
                }

            # 3. Limpiar horarios previos si es necesario
            if clear_existing:
                old_assignments = (
                    session.query(DocenteHoraClase)
                    .filter_by(docente_id=docente.id, turno_id=turno.id)
                    .all()
                )
                for assignment in old_assignments:
                    session.delete(assignment)
                session.flush()

            # 4. Importar nuevos registros
            imported_count = 0
            skipped_count = 0
            errors = []

            for entry in entries:
                try:
                    # Validar que la hora clase existe
                    hora_clase = (
                        session.query(HoraClase)
                        .filter_by(turno_id=turno.id, numero=entry.numero_hora)
                        .first()
                    )

                    if not hora_clase:
                        errors.append(
                            f"Hora {entry.numero_hora} no existe en {result.turno}"
                        )
                        skipped_count += 1
                        continue

                    # Verificar duplicado
                    existing = (
                        session.query(DocenteHoraClase)
                        .filter_by(
                            docente_id=docente.id,
                            turno_id=turno.id,
                            numero_hora=entry.numero_hora,
                            dia_semana=entry.dia_semana,
                        )
                        .first()
                    )

                    if existing:
                        skipped_count += 1
                        continue

                    # Crear nuevo registro
                    assignment = DocenteHoraClase(
                        docente_id=docente.id,
                        turno_id=turno.id,
                        hora_clase_id=hora_clase.id,
                        numero_hora=entry.numero_hora,
                        dia_semana=entry.dia_semana,
                        salon=entry.salon,
                        grupo=entry.grupo_codigo,
                    )
                    session.add(assignment)
                    imported_count += 1

                except Exception as e:
                    errors.append(f"Error en {entry.dia_semana} hora {entry.numero_hora}: {str(e)}")
                    skipped_count += 1

            session.commit()

            return {
                "success": True,
                "message": f"✅ {imported_count} registros importados correctamente",
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "errors": errors,
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "imported_count": 0,
            "errors": [str(e)],
        }


if __name__ == "__main__":
    main()

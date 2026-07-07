"""
Página de carga de horarios desde PDF
Los docentes reciben sus horarios en formato PDF (aSc Horarios) y pueden
cargarlos directamente en el sistema.
"""

from __future__ import annotations

import tempfile
import os
import uuid
import sqlite3
import shutil
from datetime import datetime
from collections import defaultdict
import streamlit as st

from database.db import DB_PATH, init_db, get_session
from database.models import Docente, DocenteHoraClase, HoraClase, Turno
from services.pdf_horario_import import PDFHorarioImportService
from services.ui import APP_NAME, configure_page, logout_button, page_hero, require_login, render_sidebar


def main() -> None:
    init_db()
    configure_page(f"{APP_NAME} | Cargar Horarios")
    user = require_login(["Administrador", "Prefecto"])

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
        
        1. **Carga el archivo PDF** en esta página
        2. El sistema extrae automáticamente:
           - Tu nombre
           - Turno (Matutino/Nocturno)
           - Todas tus clases, salones y grupos
        3. **Revisa la vista previa** y confirma la importación
        
        ### ✅ Requisitos del PDF
        
        - Debe ser un PDF generado por **aSc Horarios**
        - Debe incluir nombre y turno
        - Debe contener la tabla con las clases
        
        ### 📝 Notas importantes
        
        - Si se trabaja en **ambos turnos**, carga primero el Matutino y luego el Nocturno
        - Cada turno se importará por separado
        - Puedes cargar nuevamente para actualizar tus horarios
        """)

    _render_admin_reset_section(user)

    _render_bulk_upload_section()

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


def _render_bulk_upload_section() -> None:
    """Sección para importar múltiples PDFs en una sola operación."""
    st.markdown("### 🚀 Carga masiva de horarios")
    st.caption("Importa en un solo paso los PDFs de maestros matutinos y nocturnos.")

    bulk_files = st.file_uploader(
        "Selecciona todos los PDFs de horarios",
        type=["pdf"],
        accept_multiple_files=True,
        key="bulk_pdf_upload",
        help="Puedes seleccionar varios archivos PDF al mismo tiempo",
    )

    clear_existing_bulk = st.checkbox(
        "🗑️ Limpiar horarios previos por docente y turno antes de importar",
        key="bulk_clear_existing",
        help="Recomendado cuando se trata de una actualización general de horarios",
    )

    if not bulk_files:
        st.info("Carga varios PDFs para habilitar la importación masiva.")
        st.divider()
        return

    st.info(f"Se detectaron {len(bulk_files)} archivos listos para importar.")
    if st.button("✅ Ejecutar carga masiva", type="primary", use_container_width=True, key="run_bulk_import"):
        with st.spinner("⏳ Procesando carga masiva..."):
            summary = _process_bulk_pdf_upload(bulk_files, clear_existing_bulk)

        if summary["processed_files"] == 0:
            st.error("No se pudo procesar ningún archivo.")
            st.divider()
            return

        if summary["failed_files"] == 0:
            st.success("✅ Carga masiva completada sin errores")
            st.balloons()
        else:
            st.warning("⚠️ Carga masiva completada con algunos errores")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 PDFs procesados", summary["processed_files"])
        with col2:
            st.metric("✅ PDFs importados", summary["successful_files"])
        with col3:
            st.metric("❌ PDFs con error", summary["failed_files"])

        col4, col5, col6 = st.columns(3)
        with col4:
            st.metric("📚 Registros importados", summary["imported_records"])
        with col5:
            st.metric("⏭️ Registros omitidos", summary["skipped_records"])
        with col6:
            st.metric("🌅 Matutino / 🌙 Nocturno", f"{summary['matutino_files']} / {summary['nocturno_files']}")

        if summary["errors"]:
            with st.expander("📋 Ver errores de la carga masiva"):
                for error in summary["errors"][:200]:
                    st.error(f"  • {error}")

    st.divider()


def _process_bulk_pdf_upload(files, clear_existing: bool) -> dict:
    """Procesa múltiples PDFs y devuelve métricas consolidadas de importación."""
    processed_files = 0
    successful_files = 0
    failed_files = 0
    imported_records = 0
    skipped_records = 0
    turno_counter = defaultdict(int)
    errors: list[str] = []

    progress = st.progress(0.0)
    total_files = len(files)

    for index, uploaded_file in enumerate(files, start=1):
        tmp_path = ""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                tmp_path = tmp_file.name

            service = PDFHorarioImportService()
            result = service.import_from_pdf(tmp_path)

            if not result.success:
                failed_files += 1
                errors.append(f"{uploaded_file.name}: {result.message}")
                for detail in result.errors or []:
                    errors.append(f"{uploaded_file.name}: {detail}")
                continue

            success_entries, entries, extraction_errors = service.extractor.extract_from_pdf(tmp_path)
            if not success_entries or not entries:
                failed_files += 1
                errors.append(f"{uploaded_file.name}: No se pudieron extraer entradas para importar")
                for detail in extraction_errors or []:
                    errors.append(f"{uploaded_file.name}: {detail}")
                continue

            import_result = _import_to_db(result, entries, clear_existing)
            if not import_result.get("success"):
                failed_files += 1
                errors.append(f"{uploaded_file.name}: {import_result.get('message', 'Error de importación')}")
                for detail in import_result.get("errors", []):
                    errors.append(f"{uploaded_file.name}: {detail}")
                continue

            successful_files += 1
            imported_records += import_result.get("imported_count", 0)
            skipped_records += import_result.get("skipped_count", 0)

            turno = (result.turno or "").strip().lower()
            if "matutino" in turno:
                turno_counter["matutino"] += 1
            elif "nocturno" in turno:
                turno_counter["nocturno"] += 1

            for detail in import_result.get("errors", []):
                errors.append(f"{uploaded_file.name}: {detail}")

        except Exception as exc:
            failed_files += 1
            errors.append(f"{uploaded_file.name}: {exc}")
        finally:
            processed_files += 1
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

            progress.progress(index / total_files)

    return {
        "processed_files": processed_files,
        "successful_files": successful_files,
        "failed_files": failed_files,
        "imported_records": imported_records,
        "skipped_records": skipped_records,
        "matutino_files": turno_counter["matutino"],
        "nocturno_files": turno_counter["nocturno"],
        "errors": errors,
    }


def _render_admin_reset_section(user: dict) -> None:
    """Muestra acciones de mantenimiento solo para administradores."""
    if user.get("rol") != "Administrador":
        return

    with st.expander("🧹 Mantenimiento del sistema (Admin)"):
        st.warning(
            "Esta acción elimina docentes, asignaciones de horario y asistencias. "
            "No borra usuarios ni catálogos (turnos/horas)."
        )
        confirm_reset = st.checkbox(
            "Confirmo que quiero limpiar los datos operativos",
            key="confirm_reset_operational_data",
        )

        if st.button(
            "🧨 Limpiar datos operativos ahora",
            type="secondary",
            use_container_width=True,
            disabled=not confirm_reset,
        ):
            result = _reset_operational_data()
            if result["success"]:
                st.success(result["message"])
                st.info(f"Respaldo creado en: {result['backup_path']}")
                st.rerun()
            else:
                st.error(result["message"])
                for error in result.get("errors", []):
                    st.error(f"  • {error}")


def _reset_operational_data() -> dict:
    """Limpia datos operativos y crea un respaldo de la base SQLite."""
    try:
        db_path = DB_PATH
        if not db_path.exists():
            return {
                "success": False,
                "message": "No se encontró la base de datos para limpiar.",
                "errors": [str(db_path)],
            }

        backup_dir = db_path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{db_path.stem}_preclean_manual_{ts}.db"
        shutil.copy2(db_path, backup_path)

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")

        for table in ["asistencias", "docente_horas_clase", "docentes"]:
            exists = cur.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            if exists:
                cur.execute(f"DELETE FROM {table}")

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Datos operativos limpiados correctamente.",
            "backup_path": str(backup_path),
        }
    except Exception as e:
        return {
            "success": False,
            "message": "No se pudieron limpiar los datos operativos.",
            "errors": [str(e)],
        }


def _import_to_db(result, entries, clear_existing: bool) -> dict:
    """
    Importa los datos extraídos a la base de datos
    """
    try:
        with get_session() as session:
            dia_map = {
                "lunes": 0,
                "martes": 1,
                "miércoles": 2,
                "miercoles": 2,
                "jueves": 3,
                "viernes": 4,
                "sábado": 5,
                "sabado": 5,
            }

            # 1. Buscar o crear docente
            numero_empleado = result.numero_empleado
            docente = session.query(Docente).filter_by(
                numero_empleado=numero_empleado
            ).first()

            if not docente:
                nombre_completo = (result.docente_nombre or "").strip()
                partes = [p for p in nombre_completo.split() if p]
                nombre = partes[0] if partes else "Docente"
                apellidos_tokens = partes[1:]
                apellido_paterno = apellidos_tokens[0] if apellidos_tokens else ""
                apellido_materno = " ".join(apellidos_tokens[1:]) if len(apellidos_tokens) > 1 else ""
                apellidos = " ".join(apellidos_tokens)

                if (result.turno or "").lower() == "nocturno":
                    horario_entrada = "18:00"
                    horario_salida = "21:00"
                else:
                    horario_entrada = "08:00"
                    horario_salida = "17:00"

                docente = Docente(
                    numero_empleado=numero_empleado,
                    nombre=nombre,
                    apellido_paterno=apellido_paterno,
                    apellido_materno=apellido_materno,
                    apellidos=apellidos,
                    departamento="Sin especificar",
                    puesto="Docente",
                    horario_entrada=horario_entrada,
                    horario_salida=horario_salida,
                    qr_uuid=str(uuid.uuid4()),
                    activo=True,
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
                    dia_key = str(entry.dia_semana).lower().strip()
                    dia_numero = dia_map.get(dia_key)
                    if dia_numero is None:
                        errors.append(f"Día inválido: {entry.dia_semana}")
                        skipped_count += 1
                        continue

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
                            dia_semana=dia_numero,
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
                        dia_semana=dia_numero,
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

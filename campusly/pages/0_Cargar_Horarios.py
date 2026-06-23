from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from database.db import init_db
from services.horario_import import HorarioImportService
from services.ui import APP_NAME, configure_page, logout_button, page_hero, require_login, render_sidebar


def _generate_template_csv() -> bytes:
    """Genera una plantilla CSV de ejemplo."""
    template_data = {
        "numero_empleado": ["UC0320", "UC0320", "UC0320"],
        "turno": ["Matutino", "Matutino", "Matutino"],
        "dia_semana": ["Lunes", "Lunes", "Martes"],
        "numero_hora": [1, 2, 1],
        "salon": ["DI-A108", "DI-A108", "D1-A202"],
        "grupo": ["67QAI2A", "67QAI2A", "67TIAEVND2A"],
    }
    df = pd.DataFrame(template_data)
    return df.to_csv(index=False).encode("utf-8")


def main() -> None:
    init_db()
    configure_page(f"{APP_NAME} | Cargar Horarios")
    user = require_login(["Administrador"])

    render_sidebar(user)
    logout_button()

    page_hero("Cargar Horarios de Docentes", "Importa automáticamente los horarios desde un archivo CSV.")

    # Sección de información
    with st.expander("ℹ️ Instrucciones", expanded=True):
        st.markdown("""
        ### Formato del Archivo CSV
        
        El archivo debe tener las siguientes columnas:
        - **numero_empleado**: Clave del docente (ej: UC0320)
        - **turno**: Nombre del turno (Matutino o Nocturno)
        - **dia_semana**: Día de la semana (Lunes, Martes, Miércoles, Jueves, Viernes)
        - **numero_hora**: Número de hora clase (1-10 para Matutino, 1-4 para Nocturno)
        - **salon**: Código del salón (ej: DI-A108, D1-A202)
        - **grupo**: Código del grupo/materia (ej: 67QAI2A, 67TIAEVND2A)
        
        ### Ejemplo
        ```
        numero_empleado,turno,dia_semana,numero_hora,salon,grupo
        UC0320,Matutino,Lunes,1,DI-A108,67QAI2A
        UC0320,Matutino,Lunes,2,DI-A108,67QAI2A
        UC0320,Matutino,Martes,1,D1-A202,67TIAEVND2A
        ```
        """)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Descargar Plantilla CSV", use_container_width=True):
                template = _generate_template_csv()
                st.download_button(
                    label="Descargar horario_template.csv",
                    data=template,
                    file_name="horario_template.csv",
                    mime="text/csv",
                    key="download_template",
                )
        
        with col2:
            st.info("Usa la plantilla como base para llenar tus datos")

    # Sección de carga
    st.markdown("### Cargar Archivo")
    uploaded_file = st.file_uploader(
        "Selecciona un archivo CSV", type=["csv"], accept_multiple_files=False
    )

    if uploaded_file is None:
        st.stop()

    file_content = uploaded_file.read()

    # Validar archivo
    is_valid, validation_msg = HorarioImportService.validate_file(file_content)
    if not is_valid:
        st.error(f"❌ {validation_msg}")
        st.stop()

    st.success(f"✅ {validation_msg}")

    # Mostrar vista previa
    try:
        df = HorarioImportService.parse_csv(file_content)
        st.markdown("### Vista Previa")
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Error al procesar archivo: {e}")
        st.stop()

    # Opciones de importación
    st.markdown("### Opciones de Importación")

    col1, col2 = st.columns(2)
    with col1:
        clear_existing = st.checkbox(
            "Limpiar horarios existentes antes de importar",
            value=False,
            help="Si está activado, eliminará todos los horarios actuales de los docentes en el archivo",
        )
    with col2:
        if clear_existing:
            st.warning("⚠️ Los horarios existentes serán eliminados")

    # Botón de importación
    if st.button("🚀 Importar Horarios", use_container_width=True, type="primary"):
        progress_bar = st.progress(0)

        try:
            # Limpiar si es necesario
            if clear_existing:
                unique_employees = df["numero_empleado"].unique()
                for emp_id in unique_employees:
                    HorarioImportService.clear_docente_horarios(str(emp_id).strip())
                st.info(f"Horarios anteriores de {len(unique_employees)} docente(s) eliminados")

            # Importar
            progress_bar.progress(50)
            result = HorarioImportService.import_horarios(df)
            progress_bar.progress(100)

            # Mostrar resultados
            st.markdown("### Resultados de Importación")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Importados", result.imported_count, delta=f"+{result.imported_count}")
            with col2:
                st.metric("Omitidos", result.skipped_count)
            with col3:
                st.metric("Errores", len(result.errors))

            if result.success:
                st.success(f"✅ {result.message}")
            else:
                st.warning(result.message)

            # Mostrar errores si existen
            if result.errors:
                with st.expander("📋 Detalles de Errores"):
                    for error in result.errors[:20]:
                        st.write(f"• {error}")
                    if len(result.errors) > 20:
                        st.write(f"... y {len(result.errors) - 20} errores más")

        except Exception as e:
            st.error(f"Error durante la importación: {e}")


if __name__ == "__main__":
    main()

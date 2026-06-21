# Sistema de Asistencia Docente mediante QR

Aplicación web en Streamlit para el control de asistencia de docentes con QR, SQLite y reportes interactivos.

## Requisitos

- Python 3.12+
- Instalar dependencias con `pip install -r requirements.txt`
- En macOS, `pyzbar` puede requerir la librería del sistema `zbar`.

## Ejecución

```bash
streamlit run app.py
```

## Estructura

- `app.py`: inicio de sesión y portada.
- `pages/1_Docentes.py`: CRUD de docentes y generación de gafetes.
- `pages/2_Escaner_QR.py`: escáner QR y registro automático de asistencia.
- `pages/3_Asistencias.py`: consulta y filtros.
- `pages/4_Reportes.py`: reportes y exportación.
- `pages/5_Dashboard.py`: métricas y gráficas.

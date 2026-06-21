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

## Deploy en Streamlit Community Cloud

1. Sube el repositorio a GitHub.
2. En Streamlit Community Cloud selecciona `New app`.
3. Elige el repositorio y apunta al archivo principal `app.py`.
4. Espera a que instale las dependencias de `requirements.txt`.
5. Si el despliegue usa Linux, los paquetes de sistema ya están declarados en `packages.txt` para `cv2` y `pyzbar`.

## Nota para móvil

La app se adapta a navegador móvil. Para probarla desde el celular, abre la URL pública del despliegue y usa la página `Escáner QR` con permiso de cámara.

## Estructura

- `app.py`: inicio de sesión y portada.
- `pages/1_Docentes.py`: CRUD de docentes y generación de gafetes.
- `pages/2_Escaner_QR.py`: escáner QR y registro automático de asistencia.
- `pages/3_Asistencias.py`: consulta y filtros.
- `pages/4_Reportes.py`: reportes y exportación.
- `pages/5_Dashboard.py`: métricas y gráficas.

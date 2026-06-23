# 📊 Módulo de Importación de Horarios - Referencia Rápida

## 🚀 Inicio Rápido (3 Pasos)

### Paso 1: Preparar CSV
Crea un archivo `horarios.csv` con este formato:

```csv
numero_empleado,turno,dia_semana,numero_hora,salon,grupo
UC0320,Matutino,Lunes,1,DI-A108,67QAI2A
UC0320,Matutino,Lunes,2,DI-A108,67QAI2A
```

### Paso 2: Acceder al Sistema
1. Abre la aplicación Campusly
2. Inicia sesión como **Administrador**
3. Haz clic en **"Cargar Horarios"** en el menú

### Paso 3: Importar
1. Sube el archivo CSV
2. Revisa la vista previa
3. Haz clic en **"Importar Horarios"** 
4. ¡Listo! Los horarios se guardan automáticamente

---

## 📋 Estructura del CSV

| Campo | Valores | Ejemplo |
|-------|---------|---------|
| `numero_empleado` | Clave docente | UC0320 |
| `turno` | Matutino / Nocturno | Matutino |
| `dia_semana` | Lunes-Viernes | Martes |
| `numero_hora` | 1-10 (Mat) / 1-4 (Noc) | 5 |
| `salon` | Código salón | DI-A108 |
| `grupo` | Código grupo/materia | 67QAI2A |

---

## 📂 Archivos del Módulo

```
campusly/
├── pages/
│   └── 0_Cargar_Horarios.py          ← Interfaz Streamlit
├── services/
│   └── horario_import.py             ← Lógica de importación
├── data/
│   └── horario_ejemplo_omar_mata.csv ← Archivo de ejemplo
├── GUIA_IMPORTACION_HORARIOS.md      ← Guía completa
└── QUICKSTART.md                     ← Este archivo
```

---

## ✅ Características

✓ **Validación automática** - Verifica docentes, turnos, horas  
✓ **Sin duplicados** - Detecta y omite registros duplicados  
✓ **Importación en lote** - Importa cientos de registros en segundos  
✓ **Reemplazo opcional** - Limpia horarios anteriores si lo deseas  
✓ **Reportes detallados** - Muestra qué se importó y qué falló  
✓ **Plantilla descargable** - Descarga una plantilla vacía para llenar  

---

## � Docentes con Ambos Turnos

**Un docente puede trabajar en Matutino Y Nocturno simultáneamente.**

El sistema está diseñado específicamente para esto:

```csv
numero_empleado,turno,dia_semana,numero_hora,salon,grupo
UC0320,Matutino,Lunes,1,DI-A108,67QAI2A
UC0320,Matutino,Lunes,2,DI-A108,67QAI2A
UC0320,Nocturno,Lunes,1,DI-A105,ENGLISH1
UC0320,Nocturno,Lunes,2,DI-A105,ENGLISH1
```

**Resultado:**
- ✅ Mismo docente (UC0320)
- ✅ Mismo día (Lunes)
- ✅ **Diferentes turnos** (Matutino y Nocturno)
- ✅ Se importan **todos** sin conflicto

**Al escanear QR**, el prefecto selecciona primero el **Turno**, y el sistema valida si el docente está asignado en ese turno específico.

**Archivo de ejemplo:**
- `data/horario_completo_ambos_turnos.csv` - Muestra completa con 50 registros Matutino + 20 Nocturno

---

## �🔍 Errores Comunes y Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| "Docente no encontrado" | `numero_empleado` no existe | Verifica que el docente esté registrado en el sistema |
| "Turno no encontrado" | Nombre del turno incorrecto | Usa exactamente "Matutino" o "Nocturno" |
| "Día de semana inválido" | Día mal escrito | Usa: Lunes, Martes, Miércoles, Jueves, Viernes |
| "Hora clase no encontrada" | Número de hora no existe | Matutino: 1-10, Nocturno: 1-4 |

---

## 💡 Casos de Uso

### Caso 1: Importar un docente nuevo
```csv
numero_empleado,turno,dia_semana,numero_hora,salon,grupo
UC0321,Matutino,Lunes,1,DI-A101,PROG101
UC0321,Matutino,Martes,1,DI-A101,PROG101
```
**Resultado**: Se importan 2 horas del docente UC0321

### Caso 2: Actualizar horario existente
1. Activa **"Limpiar horarios existentes"**
2. Sube archivo con nuevo horario
**Resultado**: Se reemplaza el horario anterior

### Caso 3: Importar múltiples docentes
```csv
numero_empleado,turno,dia_semana,numero_hora,salon,grupo
UC0320,Matutino,Lunes,1,DI-A108,67QAI2A
UC0321,Nocturno,Lunes,1,DI-A105,68PROG1
UC0322,Matutino,Lunes,1,DI-A102,ENGLISH1
```
**Resultado**: Se importan 3 docentes (3 horas cada uno)

---

## 📊 Estadísticas de Ejemplo

Archivo: `horario_ejemplo_omar_mata.csv`
- **Docente**: Omar Alejandro Mata Garza (UC0320)
- **Registros**: 50
- **Turno**: Matutino
- **Cobertura**: 10 horas x 5 días (Lunes-Viernes)
- **Tiempo de importación**: < 1 segundo

Resultado de importación:
```
✅ Importados: 50
⊘ Omitidos: 0
❌ Errores: 0
```

---

## 🔐 Seguridad y Validaciones

- ✅ Solo Administrador puede importar
- ✅ Validación de estructura CSV
- ✅ Verificación de docentes en BD
- ✅ Verificación de turnos válidos
- ✅ Prevención de duplicados automática
- ✅ Registro de errores detallado

---

## 📞 Soporte

Para más información, consulta:
- **Guía Completa**: `GUIA_IMPORTACION_HORARIOS.md`
- **Ejemplo**: `data/horario_ejemplo_omar_mata.csv`
- **Código**: `services/horario_import.py`

---

**¡Disfruta importando horarios! 🎉**

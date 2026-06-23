# 📅 Guía de Carga de Horarios desde PDF

## ¿Qué es esto?

El **Sistema de Asistencia Docente mediante QR (Campusly)** ahora permite cargar horarios directamente desde archivos PDF. Recibirás un PDF de horario desde la Universidad Tecnológica Cadereyta con todos tus cursos, y podrás cargarlo fácilmente en el sistema.

## 📋 Requisitos

- Archivo PDF del horario (formato **aSc Horarios**)
- Acceso a la aplicación Campusly
- Permisos de carga (Administrador o Docente)

## 🚀 Paso a Paso

### Paso 1: Obtén tu PDF de Horario

Descarga tu horario en PDF desde el sistema de la Universidad. El PDF debe verse así:

```
Horario
Docente: Ing. Omar Alejandro Mata Garza
Turno: Matutino
Universidad Tecnológica Cadereyta

[Tabla con días: Lunes, Martes, Miércoles, Jueves, Viernes]
[Filas con horas: 8:00-8:50, 8:50-9:40, ...]
[Celdas con: Código Grupo, Materia, Salón]
```

### Paso 2: Abre la Aplicación Campusly

1. Accede a [campusly.streamlit.app](https://campusly.streamlit.app)
2. Inicia sesión con tu usuario
3. Ve a la sección **📅 Cargar Horarios**

### Paso 3: Carga tu PDF

1. Haz clic en **"Carga tu horario en PDF"**
2. Selecciona el archivo PDF desde tu computadora
3. La aplicación analizará automáticamente:
   - Tu nombre
   - Tu turno (Matutino/Nocturno)
   - Todas tus clases, salones y grupos

### Paso 4: Revisa la Vista Previa

El sistema mostrará una tabla con tu horario organizado por día:

| Día | Hora | Código | Materia | Salón |
|-----|------|--------|---------|-------|
| Lunes | Hora 1 | 67QAI2A | Informática I | DI-A108 |
| Lunes | Hora 2 | 67QAI2A | Informática I | DI-A108 |
| Martes | Hora 1 | 67TIAEVND2A | POO | D1-A202 |

**Revisa que todo sea correcto** antes de confirmar.

### Paso 5: Importa

1. Si todo está bien, haz clic en **✅ Importar Horario**
2. El sistema guardará todos tus registros automáticamente
3. Verás un confirmación con estadísticas:
   - Registros importados ✅
   - Duplicados detectados ⏭️
   - Errores (si los hay) ❌

## 💡 Casos de Uso

### Caso 1: Trabajo en Turno Matutino Solamente

1. Carga el PDF del Matutino
2. Listo, tu horario está en el sistema
3. Cuando los prefectos pasen por tu salón a la primera hora, podrán escanear tu QR

### Caso 2: Trabajo en Ambos Turnos

1. **Carga 1:** PDF del Matutino (10 horas)
   - Se importarán 50 registros (10 horas × 5 días)
2. **Carga 2:** PDF del Nocturno (4 horas)
   - Se importarán 20 registros (4 horas × 5 días)
3. El sistema detectará que es el mismo docente en diferentes turnos
4. No habrá conflictos, ambos turnos se guardarán correctamente

### Caso 3: Actualizar Horario

1. Vuelve a la sección **📅 Cargar Horarios**
2. Marca la opción **"🗑️ Limpiar horarios anteriores"**
3. Carga el nuevo PDF
4. Los horarios antiguos se eliminarán y se guardarán los nuevos

## ⚠️ Solución de Problemas

### El PDF no se procesa correctamente

**Síntoma:** Error "No se encontraron tablas en el PDF"

**Causas posibles:**
- El PDF no está en formato aSc Horarios
- El PDF está corrupto o protegido
- La calidad de escaneo es muy baja

**Solución:** Descarga nuevamente tu horario desde el sistema de la universidad

### No se encuentra el nombre o turno

**Síntoma:** Error "Falta el nombre del docente o turno"

**Causa:** El PDF no contiene esta información en el formato esperado

**Solución:** Asegúrate de que tu PDF muestre claramente:
- `Docente: [Tu Nombre]`
- `Turno: Matutino` o `Turno: Nocturno`

### La tabla se ve incorrecta

**Síntoma:** Datos faltantes o confusos en la vista previa

**Causa:** La estructura de la tabla es diferente

**Solución:** Verifica que el PDF contenga:
- Columnas: Lunes, Martes, Miércoles, Jueves, Viernes
- Filas: Horas de clase con horarios
- Celdas: Código grupo, materia, salón

## 📊 ¿Qué se importa exactamente?

El sistema extrae de tu PDF:

```
Para cada clase:
├── Día de la semana (Lunes, Martes, Miércoles, Jueves, Viernes)
├── Número de hora (1-10 para Matutino, 1-4 para Nocturno)
├── Código del grupo (ej: 67QAI2A)
├── Nombre de la materia (ej: Informática I)
├── Salón (ej: DI-A108)
└── Turno (Matutino/Nocturno)
```

Todo se guarda automáticamente en la base de datos.

## 🔐 Seguridad y Privacidad

- Tu PDF se procesa **solo en el servidor**
- Los datos se **no se guardan** en el archivo PDF
- Solo se extrae la **información estructurada** de la tabla
- Tu PDF **no se almacena**, se descarta después del procesamiento

## 📞 Soporte

Si tienes problemas:

1. Revisa esta guía (especialmente "Solución de Problemas")
2. Verifica que tu PDF sea el correcto
3. Descarga nuevamente tu horario
4. Intenta cargar de nuevo

Para asistencia adicional, contacta al administrador del sistema.

## 🎯 Siguientes Pasos

Después de cargar tu horario:

1. **Ve a "Escáner QR"** para empezar a registrar asistencia
2. Los prefectos pasarán por tu salón a cada hora
3. Escanean tu QR con el código de tu hora clase
4. Tu asistencia se registra automáticamente

## 📈 Estadísticas Después de la Carga

Después de importar, verás:

- **✅ Importados:** Registros cargados exitosamente
- **⏭️ Duplicados:** Registros que ya existían (no se duplican)
- **❌ Errores:** Problemas encontrados durante la importación

Si hay errores, puedes ver los detalles y corregirlos manualmente en "Asignar Horarios".

---

**Versión:** 2.0  
**Última actualización:** 2024  
**Formato soportado:** PDF (aSc Horarios)

# 📚 Guía de Importación de Horarios

## ¿Qué es el módulo de importación?

El módulo de **Cargar Horarios** permite importar automáticamente los horarios de los docentes desde un archivo CSV sin tener que crearlos manualmente uno por uno.

## Formato del Archivo CSV

El archivo debe ser un CSV con las siguientes **6 columnas obligatorias**:

| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| `numero_empleado` | Clave única del docente | UC0320 |
| `turno` | Nombre del turno | Matutino o Nocturno |
| `dia_semana` | Día de la semana | Lunes, Martes, Miércoles, Jueves, Viernes |
| `numero_hora` | Número de hora clase | 1 a 10 (Matutino), 1 a 4 (Nocturno) |
| `salon` | Código del salón | DI-A108, D1-A202, DII-A104 |
| `grupo` | Código del grupo/materia | 67QAI2A, 67TIAEVND2A, 64TIAEVND5 |

### Ejemplo de Contenido CSV

```csv
numero_empleado,turno,dia_semana,numero_hora,salon,grupo
UC0320,Matutino,Lunes,1,DI-A108,67QAI2A
UC0320,Matutino,Lunes,2,DI-A108,67QAI2A
UC0320,Matutino,Lunes,3,DII-A104,64TIAEVND5
UC0320,Matutino,Martes,1,DI-A203,67TIAEVND2B
UC0320,Matutino,Martes,2,DI-A203,67TIAEVND2B
```

## Paso a Paso para Importar

### 1. Acceder al Módulo
- Ingresa a la aplicación con usuario **Administrador**
- En el menú de la izquierda, haz clic en **"Cargar Horarios"** (es la primera opción)

### 2. Descargar la Plantilla (Opcional)
- En la sección de instrucciones, hay un botón **"Descargar Plantilla CSV"**
- Esto te proporciona una plantilla vacía que puedes completar
- Abre la plantilla en Excel o Google Sheets
- Rellena los datos según tu información

### 3. Preparar el Archivo CSV
El archivo puede venir de varias fuentes:

**Opción A: Desde Excel**
- Abre tu horario en Excel
- Crea un CSV con las 6 columnas requeridas
- Guarda como: `Archivo → Guardar como → CSV UTF-8 (.csv)`

**Opción B: Desde el PDF Original**
- Si tienes el PDF del horario (como el de aSc Horarios)
- Copia la información manualmente a Excel
- Convierte a CSV

**Opción C: Desde Google Sheets**
- Crea un Google Sheet con los datos
- Descarga como CSV: `Archivo → Descargar → CSV`

### 4. Subir el Archivo
- En la sección **"Cargar Archivo"**, haz clic en **"Browse files"**
- Selecciona tu archivo CSV
- El sistema valida automáticamente el formato

### 5. Revisar Vista Previa
- Se muestra una tabla con los datos a importar
- Verifica que todo se vea correcto
- Si hay errores, descarga la plantilla y corrige

### 6. Opciones de Importación

**Opción 1: Agregar sin reemplazar**
- Desactiva: "Limpiar horarios existentes antes de importar"
- Los nuevos registros se agregarán a los existentes
- No habrá duplicados (el sistema detecta automáticamente)

**Opción 2: Reemplazar todo**
- Activa: "Limpiar horarios existentes antes de importar"
- Se eliminan TODOS los horarios anteriores del docente
- Se importan solo los del archivo CSV
- Útil si necesitas actualizar completamente el horario

### 7. Importar
- Haz clic en el botón **"Importar Horarios"** (azul)
- Espera a que se complete la barra de progreso

### 8. Revisar Resultados
El sistema muestra:
- **Importados**: ✅ Cuántos registros se guardaron
- **Omitidos**: ⊘ Cuántos se saltaron (ya existían)
- **Errores**: ❌ Cuántos fallaron

Si hay errores, expande **"Detalles de Errores"** para ver qué salió mal.

## Validaciones Automáticas

El sistema valida automáticamente:

✅ Docente existe en la BD  
✅ Turno (Matutino/Nocturno) existe  
✅ Día de semana es válido  
✅ Hora clase existe para ese turno  
✅ No crea duplicados (si el registro ya existe)

Si hay errores:
- **Docente no encontrado**: Verifica el `numero_empleado`
- **Turno no encontrado**: Asegúrate que escribas "Matutino" o "Nocturno" exactamente
- **Día inválido**: Usa: Lunes, Martes, Miércoles, Jueves, Viernes
- **Hora no existe**: Verifica `numero_hora` (1-10 Matutino, 1-4 Nocturno)

## Ejemplo Práctico

Tenemos el horario de 3 docentes:

**Docente 1: Omar Alejandro Mata Garza**
- Lunes a Viernes
- Turnos: Matutino
- Clases en diversos salones

**Docente 2: María García López**
- Lunes a Viernes
- Turnos: Nocturno
- Clases en otro conjunto de salones

### Archivo CSV combinado:

```csv
numero_empleado,turno,dia_semana,numero_hora,salon,grupo
UC0320,Matutino,Lunes,1,DI-A108,67QAI2A
UC0320,Matutino,Lunes,2,DI-A108,67QAI2A
UC0321,Nocturno,Lunes,1,DI-A105,68PROG1
UC0321,Nocturno,Lunes,2,DI-A105,68PROG1
```

**Resultado**: Se importan 4 registros correctamente, cada docente en su turno correspondiente.

## Docentes Trabajando en Ambos Turnos

Una característica importante es que **un docente puede trabajar en Matutino Y Nocturno simultáneamente**.

### Ejemplo: Docente en Ambos Turnos

```csv
numero_empleado,turno,dia_semana,numero_hora,salon,grupo
UC0320,Matutino,Lunes,1,DI-A108,67QAI2A
UC0320,Matutino,Lunes,2,DI-A108,67QAI2A
UC0320,Matutino,Martes,1,DI-A203,67TIAEVND2B
UC0320,Nocturno,Lunes,1,DI-A105,ENGLISH1
UC0320,Nocturno,Lunes,2,DI-A105,ENGLISH1
UC0320,Nocturno,Martes,1,DI-A105,ENGLISH2
```

**Resultado:**
- ✅ 3 horas de Matutino importadas
- ✅ 3 horas de Nocturno importadas
- ✅ **Mismo docente, mismos días, DIFERENTES turnos** - Sin conflictos

### Cómo Funciona

1. El sistema diferencia los turnos automáticamente
2. El mismo docente puede estar asignado a múltiples horas en cada turno
3. Al escanear QR, el prefecto **selecciona el turno primero**
4. El sistema valida que el docente esté asignado en ese turno específico

### Archivos de Ejemplo

Dos archivos de ejemplo están disponibles:

1. **`data/horario_ejemplo_omar_mata.csv`** - Solo Matutino (50 registros)
2. **`data/horario_completo_ambos_turnos.csv`** - Matutino + Nocturno (70 registros totales)

Puedes descargar cualquiera y adaptarlo con tus datos.

## Preguntas Frecuentes

**P: ¿Qué pasa si importo un docente que ya existe?**  
R: El sistema no creará duplicados. Si el registro (docente, turno, hora, día, salón) ya existe, lo omitirá y continuará con los demás.

**P: ¿Puedo modificar un horario después de importarlo?**  
R: Sí, en la página **"Asignar Horarios"** puedes:
- Ver todas las asignaciones del docente
- Eliminar registros individuales
- Agregar nuevas asignaciones manualmente

**P: ¿Cómo borro todos los horarios de un docente?**  
R: En la importación, activa **"Limpiar horarios existentes"** antes de importar un archivo que solo contiene los horarios nuevos.

**P: ¿El sistema valida conflictos de horarios?**  
R: Actualmente no. El sistema solo valida que los datos sean correctos. Si un docente tiene dos clases a la misma hora en diferentes salones, ambas se guardarán. Esto es por diseño, ya que algunos docentes pueden tener clases paralelas.

**P: ¿Puedo importar múltiples docentes en un solo archivo?**  
R: Sí, el archivo puede contener cualquier cantidad de docentes. Solo asegúrate que cada uno tenga un `numero_empleado` válido.

**P: ¿Qué sucede si hay filas vacías o mal formateadas?**  
R: Se mostrarán en los errores durante la importación. Corrige esas filas y vuelve a intentar.

## Soporte Técnico

Si encuentras problemas:
1. Verifica que el archivo CSV tenga exactamente las 6 columnas requeridas
2. Comprueba que los valores sean válidos (turnos correctos, días válidos)
3. Revisa los detalles de errores para identificar filas problemáticas
4. Contacta al administrador del sistema

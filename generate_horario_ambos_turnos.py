"""
Script para generar un archivo CSV que demuestra un docente trabajando en AMBOS turnos
- Horario Matutino: 10 horas x 5 días = 50 registros
- Horario Nocturno: 4 horas x 5 días = 20 registros
- Total: 70 registros para UN solo docente en AMBOS turnos
"""
import pandas as pd

# Datos del docente en TURNO MATUTINO (50 registros)
horario_matutino = [
    # Lunes
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 1, "salon": "DI-A108", "grupo": "67QAI2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 2, "salon": "DI-A108", "grupo": "67QAI2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 3, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 4, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 5, "salon": "D1-A202", "grupo": "67TIAEVND2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 6, "salon": "D1-A202", "grupo": "67TIAEVND2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 7, "salon": "Comedor", "grupo": "Comida"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 8, "salon": "Oficina", "grupo": "Desarrollo Docente"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 9, "salon": "Oficina", "grupo": "Administrativo"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 10, "salon": "Oficina", "grupo": "Administrativo"},
    
    # Martes
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 1, "salon": "DI-A203", "grupo": "67TIAEVND2B"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 2, "salon": "DI-A203", "grupo": "67TIAEVND2B"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 3, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 4, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 5, "salon": "D1-A202", "grupo": "67TIAEVND2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 6, "salon": "DI-A108", "grupo": "67QAI2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 7, "salon": "Comedor", "grupo": "Comida"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 8, "salon": "Oficina", "grupo": "Desarrollo Docente"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 9, "salon": "Oficina", "grupo": "Administrativo"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 10, "salon": "Oficina", "grupo": "Administrativo"},
    
    # Miércoles
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 1, "salon": "DI-A203", "grupo": "67TIAEVND2B"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 2, "salon": "DI-A203", "grupo": "67TIAEVND2B"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 3, "salon": "DI-A108", "grupo": "67QAI2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 4, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 5, "salon": "DI-A108", "grupo": "67QAI2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 6, "salon": "DI-A203", "grupo": "67TIAEVND2B"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 7, "salon": "Comedor", "grupo": "Comida"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 8, "salon": "Oficina", "grupo": "Desarrollo Docente"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 9, "salon": "Oficina", "grupo": "Administrativo"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 10, "salon": "Oficina", "grupo": "Administrativo"},
    
    # Jueves
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 1, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 2, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 3, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 4, "salon": "D1-A202", "grupo": "67TIAEVND2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 5, "salon": "DI-A203", "grupo": "67TIAEVND2B"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 6, "salon": "DI-A203", "grupo": "67TIAEVND2B"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 7, "salon": "Comedor", "grupo": "Comida"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 8, "salon": "Oficina", "grupo": "Desarrollo Docente"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 9, "salon": "Oficina", "grupo": "Administrativo"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 10, "salon": "Estadía", "grupo": "Estadía"},
    
    # Viernes
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 1, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 2, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 3, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 4, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 5, "salon": "DI-A108", "grupo": "67QAI2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 6, "salon": "D1-A202", "grupo": "67TIAEVND2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 7, "salon": "Comedor", "grupo": "Comida"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 8, "salon": "Oficina", "grupo": "Desarrollo Docente"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 9, "salon": "Oficina", "grupo": "Administrativo"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 10, "salon": "Estadía", "grupo": "Estadía"},
]

# Datos del docente en TURNO NOCTURNO (20 registros)
horario_nocturno = [
    # Lunes
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Lunes", "numero_hora": 1, "salon": "DI-A105", "grupo": "ENGLISH1"},
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Lunes", "numero_hora": 2, "salon": "DI-A105", "grupo": "ENGLISH1"},
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Lunes", "numero_hora": 3, "salon": "DI-A106", "grupo": "PROG1"},
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Lunes", "numero_hora": 4, "salon": "DI-A106", "grupo": "PROG1"},
    
    # Martes
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Martes", "numero_hora": 1, "salon": "DI-A105", "grupo": "ENGLISH2"},
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Martes", "numero_hora": 2, "salon": "DI-A105", "grupo": "ENGLISH2"},
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Martes", "numero_hora": 3, "salon": "DI-A106", "grupo": "PROG2"},
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Martes", "numero_hora": 4, "salon": "DI-A106", "grupo": "PROG2"},
    
    # Miércoles
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Miércoles", "numero_hora": 1, "salon": "DI-A105", "grupo": "ENGLISH1"},
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Miércoles", "numero_hora": 2, "salon": "DI-A105", "grupo": "ENGLISH1"},
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Miércoles", "numero_hora": 3, "salon": "DI-A106", "grupo": "PROG1"},
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Miércoles", "numero_hora": 4, "salon": "DI-A106", "grupo": "PROG1"},
    
    # Jueves
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Jueves", "numero_hora": 1, "salon": "DI-A105", "grupo": "ENGLISH3"},
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Jueves", "numero_hora": 2, "salon": "DI-A105", "grupo": "ENGLISH3"},
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Jueves", "numero_hora": 3, "salon": "DI-A106", "grupo": "PROG3"},
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Jueves", "numero_hora": 4, "salon": "DI-A106", "grupo": "PROG3"},
    
    # Viernes
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Viernes", "numero_hora": 1, "salon": "DI-A105", "grupo": "ENGLISH2"},
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Viernes", "numero_hora": 2, "salon": "DI-A105", "grupo": "ENGLISH2"},
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Viernes", "numero_hora": 3, "salon": "DI-A106", "grupo": "PROG2"},
    {"numero_empleado": "UC0320", "turno": "Nocturno", "dia_semana": "Viernes", "numero_hora": 4, "salon": "DI-A106", "grupo": "PROG2"},
]

# Combinar ambos horarios
horario_completo = horario_matutino + horario_nocturno

# Crear DataFrame
df = pd.DataFrame(horario_completo)

# Guardar a CSV
output_path = "data/horario_completo_ambos_turnos.csv"
df.to_csv(output_path, index=False)

print(f"✅ Archivo generado exitosamente: {output_path}")
print(f"\n📊 ESTADÍSTICAS:")
print(f"  Total de registros: {len(df)}")
print(f"  Turnos: {df['turno'].unique().tolist()}")
print(f"  Docente: UC0320 (Omar Alejandro Mata Garza)")
print(f"\n🔍 DESGLOSE:")
print(f"  Turno Matutino: {len(horario_matutino)} registros (10 horas x 5 días)")
print(f"  Turno Nocturno: {len(horario_nocturno)} registros (4 horas x 5 días)")
print(f"\n📋 PRIMEROS REGISTROS DE CADA TURNO:")
print("\n  MATUTINO:")
print(df[df['turno']=='Matutino'].head(3).to_string(index=False))
print("\n  NOCTURNO:")
print(df[df['turno']=='Nocturno'].head(3).to_string(index=False))

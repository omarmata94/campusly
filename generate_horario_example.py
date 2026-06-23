"""
Script para generar un archivo CSV de ejemplo basado en el horario del Ing. Omar Alejandro Mata Garza
"""
import pandas as pd
from datetime import datetime

# Datos del horario del PDF
horario_data = [
    # Lunes
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 1, "salon": "DI-A108", "grupo": "67QAI2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 2, "salon": "DI-A108", "grupo": "67QAI2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 3, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 4, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 5, "salon": "D1-A202", "grupo": "67TIAEVND2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 6, "salon": "D1-A202", "grupo": "67TIAEVND2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 7, "salon": "Comida", "grupo": "Comida"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 8, "salon": "Administrativo", "grupo": "Desarrollo Docente"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 9, "salon": "Administrativo", "grupo": "Administrativo"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Lunes", "numero_hora": 10, "salon": "Administrativo", "grupo": "Administrativo"},
    
    # Martes
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 1, "salon": "DI-A203", "grupo": "67TIAEVND2B"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 2, "salon": "DI-A203", "grupo": "67TIAEVND2B"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 3, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 4, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 5, "salon": "D1-A202", "grupo": "67TIAEVND2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 6, "salon": "DI-A108", "grupo": "67QAI2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 7, "salon": "Comida", "grupo": "Comida"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 8, "salon": "Administrativo", "grupo": "Desarrollo Docente"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 9, "salon": "Administrativo", "grupo": "Administrativo"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Martes", "numero_hora": 10, "salon": "Administrativo", "grupo": "Administrativo"},
    
    # Miércoles
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 1, "salon": "DI-A203", "grupo": "67TIAEVND2B"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 2, "salon": "DI-A203", "grupo": "67TIAEVND2B"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 3, "salon": "DI-A108", "grupo": "67QAI2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 4, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 5, "salon": "DI-A108", "grupo": "67QAI2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 6, "salon": "DI-A203", "grupo": "67TIAEVND2B (Tutoría)"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 7, "salon": "Comida", "grupo": "Comida"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 8, "salon": "Administrativo", "grupo": "Desarrollo Docente"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 9, "salon": "Administrativo", "grupo": "Administrativo"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Miércoles", "numero_hora": 10, "salon": "Administrativo", "grupo": "Administrativo"},
    
    # Jueves
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 1, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 2, "salon": "DII-A104", "grupo": "64TIAEVND5"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 3, "salon": "DII-A104", "grupo": "64TIAEVND5 (Integradora II)"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 4, "salon": "D1-A202", "grupo": "67TIAEVND2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 5, "salon": "DI-A203", "grupo": "67TIAEVND2B"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 6, "salon": "DI-A203", "grupo": "67TIAEVND2B"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 7, "salon": "Comida", "grupo": "Comida"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 8, "salon": "Administrativo", "grupo": "Desarrollo Docente"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 9, "salon": "Administrativo", "grupo": "Administrativo"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Jueves", "numero_hora": 10, "salon": "Estadía", "grupo": "Estadía"},
    
    # Viernes
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 1, "salon": "DII-A104", "grupo": "64TIAEVND5 (Estadía)"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 2, "salon": "DII-A104", "grupo": "64TIAEVND5 (Estadía)"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 3, "salon": "DII-A104", "grupo": "64TIAEVND5 (Integradora II)"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 4, "salon": "DII-A104", "grupo": "64TIAEVND5 (Integradora II)"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 5, "salon": "DI-A108", "grupo": "67QAI2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 6, "salon": "D1-A202", "grupo": "67TIAEVND2A"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 7, "salon": "Comida", "grupo": "Comida"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 8, "salon": "Administrativo", "grupo": "Desarrollo Docente"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 9, "salon": "Administrativo", "grupo": "Administrativo"},
    {"numero_empleado": "UC0320", "turno": "Matutino", "dia_semana": "Viernes", "numero_hora": 10, "salon": "Estadía", "grupo": "Estadía"},
]

# Crear DataFrame
df = pd.DataFrame(horario_data)

# Guardar a CSV
output_path = "data/horario_ejemplo_omar_mata.csv"
df.to_csv(output_path, index=False)

print(f"✅ Archivo generado exitosamente: {output_path}")
print(f"📊 Total de registros: {len(df)}")
print(f"\nPrimeros registros:")
print(df.head(10).to_string())

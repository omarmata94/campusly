"""
Servicio de importación de horarios desde archivos PDF
Extrae información del horario en formato PDF (aSc Horarios) y la convierte
a registros de DocenteHoraClase en la base de datos.
"""

import re
import pdfplumber
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict
from datetime import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class HorarioEntry:
    """Representa una entrada de horario extraída del PDF"""
    docente_nombre: str
    numero_empleado: str
    turno: str
    dia_semana: str  # Lunes, Martes, etc.
    numero_hora: int
    grupo_codigo: str
    materia_nombre: str
    salon: str


@dataclass
class PDFImportResult:
    """Resultado de la importación de un PDF"""
    success: bool
    message: str
    docente_nombre: str = ""
    numero_empleado: str = ""
    turno: str = ""
    entries_count: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class PDFHorarioExtractor:
    """Extrae información de horarios desde PDFs de aSc Horarios"""

    # Mapeo de nombres de días a números
    DIAS_SEMANA = {
        "Lunes": "Lunes",
        "Martes": "Martes",
        "Miércoles": "Miércoles",
        "Jueves": "Jueves",
        "Viernes": "Viernes",
        "Sábado": "Sábado",
    }

    # Horas clase del Matutino
    HORAS_MATUTINO = {
        "8:00 - 8:50": 1,
        "8:50 - 9:40": 2,
        "9:40 - 10:30": 3,
        "10:30 - 11:20": 4,
        "11:20 - 11:50": "Descanso",
        "11:50 - 12:40": 5,
        "12:40 - 13:30": 6,
        "13:30 - 14:20": 7,
        "14:20 - 15:10": 8,
        "15:10 - 16:10": 9,
        "16:10 - 17:00": 10,
    }

    # Horas clase del Nocturno
    HORAS_NOCTURNO = {
        "18:00 - 18:40": 1,
        "18:40 - 19:00": "Descanso",
        "19:00 - 19:40": 2,
        "19:40 - 20:20": 3,
        "20:20 - 21:00": 4,
    }

    def __init__(self):
        self.docente_nombre = ""
        self.numero_empleado = ""
        self.turno = ""
        self.horas_map = {}

    def extract_from_pdf(self, pdf_path: str) -> Tuple[bool, List[HorarioEntry], List[str]]:
        """
        Extrae información del horario desde un archivo PDF
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Tupla (éxito, lista de entradas, lista de errores)
        """
        errors = []
        entries = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    return False, [], ["PDF vacío"]

                page = pdf.pages[0]
                
                # Extraer información del docente
                text = page.extract_text()
                if not text:
                    return False, [], ["No se pudo extraer texto del PDF"]

                # Buscar nombre del docente y turno
                self._extract_header_info(text)

                # Extraer tabla de horario
                tables = page.extract_tables()
                if not tables:
                    return False, [], ["No se encontraron tablas en el PDF"]

                # La tabla principal debe ser la primera o segunda
                for table in tables:
                    if self._is_schedule_table(table):
                        entries, parse_errors = self._parse_schedule_table(table)
                        errors.extend(parse_errors)
                        break

                if not entries:
                    errors.append("No se pudo parsear la tabla de horario")
                    return False, [], errors

                return True, entries, errors

        except Exception as e:
            logger.exception("Error al extraer PDF")
            return False, [], [f"Error al procesar PDF: {str(e)}"]

    def _extract_header_info(self, text: str) -> None:
        """Extrae nombre del docente y turno del texto"""
        # Buscar "Docente: Nombre"
        docente_match = re.search(
            r"Docente:\s*(?:Ing\.)?\s*([^\n]+?)(?:\n|$)",
            text,
            re.IGNORECASE
        )
        if docente_match:
            self.docente_nombre = docente_match.group(1).strip()
            # Intentar extraer número de empleado del nombre
            # Algunos PDFs tienen código al inicio
            code_match = re.search(r"^([A-Z0-9]+)", self.docente_nombre)
            if code_match:
                self.numero_empleado = code_match.group(1)

        # Buscar "Turno: Matutino/Nocturno"
        turno_match = re.search(
            r"Turno:\s*(Matutino|Nocturno)",
            text,
            re.IGNORECASE
        )
        if turno_match:
            self.turno = turno_match.group(1)

        # Establecer mapa de horas según turno
        if "Nocturno" in self.turno:
            self.horas_map = self.HORAS_NOCTURNO.copy()
        else:
            self.horas_map = self.HORAS_MATUTINO.copy()

    def _is_schedule_table(self, table: List[List[str]]) -> bool:
        """
        Verifica si una tabla es la tabla de horario
        Busca "Lunes", "Martes", etc. en la primera fila
        """
        if not table or not table[0]:
            return False

        first_row = table[0]
        dias_found = sum(
            1 for cell in first_row if cell and any(d in str(cell) for d in self.DIAS_SEMANA)
        )
        return dias_found >= 3  # Al menos 3 días encontrados

    def _parse_schedule_table(
        self, table: List[List[str]]
    ) -> Tuple[List[HorarioEntry], List[str]]:
        """
        Parsea la tabla de horario
        
        Returns:
            Tupla (lista de entradas, lista de errores)
        """
        entries = []
        errors = []

        if not table or len(table) < 2:
            return entries, ["Tabla de horario muy pequeña"]

        # Encontrar índices de columnas de días
        header_row = table[0]
        dias_indices = {}
        
        for i, cell in enumerate(header_row):
            if cell:
                for dia in self.DIAS_SEMANA:
                    if dia in str(cell):
                        dias_indices[dia] = i
                        break

        if not dias_indices:
            return entries, ["No se encontraron columnas de días"]

        # Procesar filas de horario
        current_hora = ""
        
        for row_idx in range(1, len(table)):
            row = table[row_idx]
            
            if not row[0]:
                continue

            # Primera columna contiene la hora
            hora_cell = str(row[0]).strip()
            
            # Detectar número de hora desde el formato "HH:MM - HH:MM"
            numero_hora = self._extract_hora_number(hora_cell)
            
            if numero_hora is None or numero_hora == "Descanso":
                continue

            # Procesar cada día
            for dia, col_idx in dias_indices.items():
                if col_idx >= len(row) or not row[col_idx]:
                    continue

                cell_content = str(row[col_idx]).strip()
                
                if not cell_content or cell_content == "Descanso" or "Hora de Comida" in cell_content:
                    continue

                # Parsear contenido de la celda
                entry_data = self._parse_cell_content(cell_content)
                
                if entry_data:
                    entry = HorarioEntry(
                        docente_nombre=self.docente_nombre,
                        numero_empleado=self.numero_empleado,
                        turno=self.turno,
                        dia_semana=dia,
                        numero_hora=numero_hora,
                        grupo_codigo=entry_data.get("grupo_codigo", ""),
                        materia_nombre=entry_data.get("materia", ""),
                        salon=entry_data.get("salon", ""),
                    )
                    entries.append(entry)

        return entries, errors

    def _extract_hora_number(self, hora_cell: str) -> Optional[int]:
        """Extrae el número de hora del texto de la celda"""
        for hora_pattern, numero in self.horas_map.items():
            if hora_pattern in hora_cell:
                return numero if isinstance(numero, int) else None
        return None

    def _parse_cell_content(self, content: str) -> Optional[Dict[str, str]]:
        """
        Parsea el contenido de una celda de horario
        Formato típico: "Código grupo\nMateria\nSalón"
        Ejemplo: "67QAI2A\nInformática I\nDI-A108"
        """
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        
        if len(lines) < 2:
            return None

        return {
            "grupo_codigo": lines[0],
            "materia": lines[1] if len(lines) > 1 else "",
            "salon": lines[2] if len(lines) > 2 else "",
        }


class PDFHorarioImportService:
    """Servicio de importación de horarios desde PDF a la base de datos"""

    def __init__(self, db_service):
        self.db_service = db_service
        self.extractor = PDFHorarioExtractor()

    def import_from_pdf(self, pdf_path: str) -> PDFImportResult:
        """
        Importa horario desde un archivo PDF
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            PDFImportResult con el resultado de la importación
        """
        # Extraer datos del PDF
        success, entries, errors = self.extractor.extract_from_pdf(pdf_path)

        if not success:
            return PDFImportResult(
                success=False,
                message="No se pudo extraer el horario del PDF",
                errors=errors,
            )

        if not entries:
            return PDFImportResult(
                success=False,
                message="No se encontraron entradas de horario en el PDF",
                errors=errors,
            )

        # Obtener información del docente
        docente_nombre = self.extractor.docente_nombre
        numero_empleado = self.extractor.numero_empleado
        turno = self.extractor.turno

        if not numero_empleado:
            return PDFImportResult(
                success=False,
                message="No se pudo extraer el número de empleado del PDF",
                docente_nombre=docente_nombre,
                turno=turno,
                errors=["Número de empleado no encontrado"],
            )

        if not turno:
            return PDFImportResult(
                success=False,
                message="No se pudo detectar el turno (Matutino/Nocturno)",
                docente_nombre=docente_nombre,
                numero_empleado=numero_empleado,
                errors=["Turno no especificado en el PDF"],
            )

        # Importar a la base de datos
        try:
            imported_count = self._import_entries_to_db(
                numero_empleado, turno, entries
            )

            return PDFImportResult(
                success=True,
                message=f"Horario importado exitosamente: {imported_count} registros",
                docente_nombre=docente_nombre,
                numero_empleado=numero_empleado,
                turno=turno,
                entries_count=imported_count,
                errors=errors,
            )

        except Exception as e:
            logger.exception("Error al importar a BD")
            return PDFImportResult(
                success=False,
                message=f"Error al importar a base de datos: {str(e)}",
                docente_nombre=docente_nombre,
                numero_empleado=numero_empleado,
                turno=turno,
                errors=[str(e)],
            )

    def _import_entries_to_db(
        self, numero_empleado: str, turno: str, entries: List[HorarioEntry]
    ) -> int:
        """Importa las entradas a la base de datos"""
        # Este método depende de la estructura de tu base de datos
        # Se implementará según tus modelos de SQLAlchemy
        # Por ahora retorna el conteo
        return len(entries)

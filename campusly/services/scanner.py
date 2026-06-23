from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Optional

import numpy as np
from PIL import Image

try:
    from pyzbar.pyzbar import decode as zbar_decode
except Exception:  # pragma: no cover - fallback path for missing zbar
    zbar_decode = None

from sqlalchemy import select

from database.db import get_session
from database.models import Asistencia, Docente, DocenteHoraClase, HoraClase
from services.time_utils import current_time_local, today_local


@dataclass
class ScanResult:
    success: bool
    message: str
    docente: Optional[Docente] = None
    asistencia: Optional[Asistencia] = None


class ScannerService:
    @staticmethod
    def _load_cv2():
        try:
            import cv2  # type: ignore

            return cv2
        except Exception:
            return None

    @staticmethod
    def _normalize_payload(raw_payload: str) -> str:
        return raw_payload.strip()

    @staticmethod
    def decode_qr_from_image(image: Image.Image) -> Optional[str]:
        rgb = image.convert("RGB")
        payloads: list[str] = []

        if zbar_decode is not None:
            decoded = zbar_decode(rgb)
            for item in decoded:
                payload = getattr(item, "data", b"").decode("utf-8", errors="ignore").strip()
                if payload:
                    payloads.append(payload)

        if not payloads:
            cv2 = ScannerService._load_cv2()
            if cv2 is None:
                return None

            frame = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)
            detector = cv2.QRCodeDetector()
            data, _, _ = detector.detectAndDecode(frame)
            if data:
                payloads.append(data.strip())

        return payloads[0] if payloads else None

    @staticmethod
    def identify_docente(qr_payload: str) -> Optional[Docente]:
        qr_uuid = ScannerService._normalize_payload(qr_payload)
        with get_session() as session:
            return session.scalar(select(Docente).where(Docente.qr_uuid == qr_uuid))

    @staticmethod
    def get_docentes_for_turno_hora_salon(turno: str, numero_hora: int, salon: str) -> list[DocenteHoraClase]:
        """Obtiene docentes asignados a un turno, hora y salón específicos."""
        with get_session() as session:
            from datetime import datetime

            today = today_local()
            day_of_week = today.weekday()

            return session.execute(
                select(DocenteHoraClase).where(
                    DocenteHoraClase.turno.has(nombre=turno),
                    DocenteHoraClase.numero_hora == numero_hora,
                    DocenteHoraClase.salon == salon,
                    DocenteHoraClase.dia_semana == day_of_week,
                )
            ).scalars().all()

    @staticmethod
    def calculate_status(hora_clase_inicio: time, hora_actual: time) -> str:
        """Calcula el estatus basado en la hora de inicio de la clase."""
        local_today = today_local()
        entrada_dt = datetime.combine(local_today, hora_clase_inicio)
        actual_dt = datetime.combine(local_today, hora_actual)
        delta_minutes = int((actual_dt - entrada_dt).total_seconds() // 60)

        if delta_minutes <= 5:
            return "Puntual"
        if 6 <= delta_minutes <= 15:
            return "Retardo"
        return "Falta"

    @staticmethod
    def register_attendance(
        qr_payload: str,
        turno: str,
        numero_hora: int,
        salon: str,
        usuario_registro: str,
    ) -> ScanResult:
        """Registra asistencia de un docente en un turno y hora específicos."""
        qr_uuid = ScannerService._normalize_payload(qr_payload)
        today = today_local()
        current_time = current_time_local()

        with get_session() as session:
            # Obtener docente del QR
            docente = session.scalar(select(Docente).where(Docente.qr_uuid == qr_uuid))
            if not docente:
                return ScanResult(success=False, message="QR no reconocido")

            # Obtener hora clase
            from datetime import datetime

            day_of_week = today.weekday()
            hora_clase = session.scalar(
                select(HoraClase).where(
                    HoraClase.turno.has(nombre=turno),
                    HoraClase.numero == numero_hora,
                )
            )
            if not hora_clase:
                return ScanResult(success=False, message="Hora clase no encontrada")

            # Validar que el docente esté asignado a este turno, hora y salón
            docente_hora = session.scalar(
                select(DocenteHoraClase).where(
                    DocenteHoraClase.docente_id == docente.id,
                    DocenteHoraClase.hora_clase_id == hora_clase.id,
                    DocenteHoraClase.salon == salon,
                    DocenteHoraClase.dia_semana == day_of_week,
                )
            )
            if not docente_hora:
                return ScanResult(
                    success=False,
                    message=f"El docente no está asignado a {turno} - Hora {numero_hora} - Salón {salon}",
                    docente=docente,
                )

            # Verificar asistencia duplicada (mismo día, misma hora clase)
            existing = session.scalar(
                select(Asistencia).where(
                    Asistencia.docente_id == docente.id,
                    Asistencia.fecha == today,
                    Asistencia.hora_clase_id == hora_clase.id,
                )
            )
            if existing:
                return ScanResult(
                    success=False,
                    message="El docente ya registró asistencia en esta hora",
                    docente=docente,
                    asistencia=existing,
                )

            # Calcular estatus
            estatus = ScannerService.calculate_status(hora_clase.hora_inicio, current_time)

            # Registrar asistencia
            asistencia = Asistencia(
                docente_id=docente.id,
                hora_clase_id=hora_clase.id,
                fecha=today,
                hora=current_time,
                turno=turno,
                numero_hora=numero_hora,
                salon=salon,
                grupo=docente_hora.grupo,
                estatus=estatus,
                usuario_registro=usuario_registro,
            )
            session.add(asistencia)
            session.flush()
            session.refresh(asistencia)
            return ScanResult(
                success=True,
                message="Asistencia registrada correctamente",
                docente=docente,
                asistencia=asistencia,
            )

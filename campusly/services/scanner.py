from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Optional

import cv2
import numpy as np
from PIL import Image

try:
    from pyzbar.pyzbar import decode as zbar_decode
except Exception:  # pragma: no cover - fallback path for missing zbar
    zbar_decode = None

from sqlalchemy import select

from database.db import get_session
from database.models import Asistencia, Docente
from services.qr_generator import QRGenerator


@dataclass(slots=True)
class ScanResult:
    success: bool
    message: str
    docente: Optional[Docente] = None
    asistencia: Optional[Asistencia] = None


class ScannerService:
    @staticmethod
    def _normalize_payload(raw_payload: str) -> str:
        return raw_payload.strip()

    @staticmethod
    def decode_qr_from_image(image: Image.Image) -> Optional[str]:
        rgb = image.convert("RGB")
        frame = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)
        payloads: list[str] = []

        if zbar_decode is not None:
            decoded = zbar_decode(frame)
            for item in decoded:
                payload = getattr(item, "data", b"").decode("utf-8", errors="ignore").strip()
                if payload:
                    payloads.append(payload)

        if not payloads:
            detector = cv2.QRCodeDetector()
            data, _, _ = detector.detectAndDecode(frame)
            if data:
                payloads.append(data.strip())

        return payloads[0] if payloads else None

    @staticmethod
    def calculate_status(entrada: str, hora_actual: time) -> str:
        entrada_dt = datetime.combine(date.today(), datetime.strptime(entrada, "%H:%M").time())
        actual_dt = datetime.combine(date.today(), hora_actual)
        delta_minutes = int((actual_dt - entrada_dt).total_seconds() // 60)

        if delta_minutes <= 5:
            return "Puntual"
        if 6 <= delta_minutes <= 15:
            return "Retardo"
        return "Falta"

    @staticmethod
    def register_attendance(qr_payload: str, usuario_registro: str) -> ScanResult:
        qr_uuid = ScannerService._normalize_payload(qr_payload)
        today = date.today()
        current_time = datetime.now().time().replace(microsecond=0)

        with get_session() as session:
            docente = session.scalar(select(Docente).where(Docente.qr_uuid == qr_uuid))
            if not docente:
                return ScanResult(success=False, message="QR no reconocido")

            existing = session.scalar(
                select(Asistencia).where(Asistencia.docente_id == docente.id, Asistencia.fecha == today)
            )
            if existing:
                return ScanResult(success=False, message="El docente ya registró asistencia hoy", docente=docente, asistencia=existing)

            estatus = ScannerService.calculate_status(docente.horario_entrada, current_time)
            asistencia = Asistencia(
                docente_id=docente.id,
                fecha=today,
                hora=current_time,
                estatus=estatus,
                usuario_registro=usuario_registro,
            )
            session.add(asistencia)
            session.flush()
            session.refresh(asistencia)
            return ScanResult(success=True, message="Asistencia registrada correctamente", docente=docente, asistencia=asistencia)

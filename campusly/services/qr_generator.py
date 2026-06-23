from __future__ import annotations

import uuid
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional

import qrcode
from PIL import Image, ImageDraw, ImageFont


ROOT_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = ROOT_DIR / "assets"
QR_DIR = ASSETS_DIR / "qrs"
BADGES_DIR = ROOT_DIR / "data" / "badges"

QR_DIR.mkdir(parents=True, exist_ok=True)
BADGES_DIR.mkdir(parents=True, exist_ok=True)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    for font_path in candidates:
        try:
            return ImageFont.truetype(font_path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _create_placeholder_logo(size: int = 180) -> Image.Image:
    image = Image.new("RGBA", (size, size), (18, 43, 70, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, size - 8, size - 8), radius=28, outline=(255, 255, 255, 220), width=4)
    title_font = _load_font(48, bold=True)
    small_font = _load_font(18)
    draw.text((size / 2, 62), "C", fill="white", anchor="mm", font=title_font)
    draw.text((size / 2, 118), "Campusly", fill=(224, 235, 255), anchor="mm", font=small_font)
    return image


@dataclass
class BadgeAsset:
    pdf_path: Path
    image_path: Path


class QRGenerator:
    @staticmethod
    def generate_uuid() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def generate_qr_bytes(payload: str) -> bytes:
        qr = qrcode.QRCode(version=4, box_size=10, border=3)
        qr.add_data(payload)
        qr.make(fit=True)
        image = qr.make_image(fill_color="#102542", back_color="white").convert("RGB")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def save_qr(payload: str, qr_uuid: str) -> Path:
        qr_path = QR_DIR / f"{qr_uuid}.png"
        qr_path.write_bytes(QRGenerator.generate_qr_bytes(payload))
        return qr_path


class BadgeGenerator:
    @staticmethod
    def _compose_badge(
        full_name: str,
        employee_number: str,
        department: str,
        qr_path: Path,
        photo_path: Optional[Path] = None,
        logo_path: Optional[Path] = None,
    ) -> Image.Image:
        canvas = Image.new("RGB", (1050, 650), "white")
        draw = ImageDraw.Draw(canvas)

        draw.rounded_rectangle((18, 18, 1032, 632), radius=36, outline=(16, 37, 66), width=6, fill=(248, 250, 252))
        draw.rounded_rectangle((32, 32, 1018, 128), radius=28, fill=(16, 37, 66))

        logo = None
        if logo_path and logo_path.exists():
            logo = Image.open(logo_path).convert("RGBA")
        else:
            logo = _create_placeholder_logo(160)
        logo = logo.resize((110, 110))
        canvas.paste(logo, (52, 42), logo if logo.mode == "RGBA" else None)

        title_font = _load_font(34, bold=True)
        subtitle_font = _load_font(20)
        draw.text((184, 60), "Sistema de Asistencia Docente", fill="white", font=title_font)
        draw.text((184, 100), "Gafete institucional con QR", fill=(220, 229, 241), font=subtitle_font)

        photo_box = (56, 182, 362, 488)
        draw.rounded_rectangle(photo_box, radius=28, outline=(16, 37, 66), width=4, fill="white")

        if photo_path and photo_path.exists():
            photo = Image.open(photo_path).convert("RGB")
            photo.thumbnail((280, 280))
            offset_x = 56 + (306 - photo.width) // 2
            offset_y = 182 + (306 - photo.height) // 2
            canvas.paste(photo, (offset_x, offset_y))
        else:
            placeholder_font = _load_font(24, bold=True)
            draw.text((209, 335), "SIN FOTO", fill=(110, 125, 145), anchor="mm", font=placeholder_font)

        qr = Image.open(qr_path).convert("RGB")
        qr = qr.resize((220, 220))
        draw.rounded_rectangle((742, 228, 982, 468), radius=28, outline=(16, 37, 66), width=4, fill="white")
        canvas.paste(qr, (752, 238))

        label_font = _load_font(18, bold=True)
        value_font = _load_font(30, bold=True)
        small_font = _load_font(24)

        draw.text((414, 202), "Docente", fill=(46, 58, 78), font=label_font)
        draw.text((414, 232), full_name.upper(), fill=(16, 37, 66), font=value_font)
        draw.text((414, 300), f"No. Empleado: {employee_number}", fill=(46, 58, 78), font=small_font)
        draw.text((414, 350), f"Departamento: {department}", fill=(46, 58, 78), font=small_font)
        draw.text((414, 430), "Presenta este gafete al prefecto para registrar asistencia.", fill=(78, 92, 110), font=subtitle_font)

        draw.rounded_rectangle((414, 502, 708, 574), radius=18, fill=(231, 239, 249))
        draw.text((561, 538), "QR institucional", fill=(16, 37, 66), anchor="mm", font=label_font)

        return canvas

    @staticmethod
    def generate_badge_pdf(
        full_name: str,
        employee_number: str,
        department: str,
        qr_uuid: str,
        photo_path: Optional[Path] = None,
        logo_path: Optional[Path] = None,
    ) -> BadgeAsset:
        qr_path = QR_DIR / f"{qr_uuid}.png"
        if not qr_path.exists():
            QRGenerator.save_qr(qr_uuid, qr_uuid)

        badge = BadgeGenerator._compose_badge(
            full_name=full_name,
            employee_number=employee_number,
            department=department,
            qr_path=qr_path,
            photo_path=photo_path,
            logo_path=logo_path,
        )
        image_path = BADGES_DIR / f"{qr_uuid}.png"
        pdf_path = BADGES_DIR / f"{qr_uuid}.pdf"
        badge.save(image_path)
        badge.convert("RGB").save(pdf_path, "PDF", resolution=300.0)
        return BadgeAsset(pdf_path=pdf_path, image_path=image_path)

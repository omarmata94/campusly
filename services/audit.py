from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from sqlalchemy import func, select

from database.db import get_session
from database.models import AuditLog


def _serialize_details(details: Any | None) -> str:
    if details is None:
        return ""
    if isinstance(details, str):
        return details[:255]
    return json.dumps(details, ensure_ascii=False, default=str)[:255]


def record_event(
    *,
    usuario: str,
    accion: str,
    entidad: str,
    descripcion: str,
    entidad_id: str | int | None = None,
    detalles: Any | None = None,
) -> None:
    with get_session() as session:
        session.add(
            AuditLog(
                fecha_evento=datetime.now(),
                usuario=usuario,
                accion=accion,
                entidad=entidad,
                entidad_id="" if entidad_id is None else str(entidad_id),
                descripcion=f"{descripcion}{' | ' + _serialize_details(detalles) if detalles else ''}"[:255],
            )
        )
        session.commit()


def distinct_users() -> list[str]:
    with get_session() as session:
        rows = session.execute(
            select(AuditLog.usuario)
            .distinct()
            .order_by(AuditLog.usuario)
        ).all()
    return [row[0] for row in rows if row[0]]


def recent_events(limit: int = 12, usuario: str | None = None) -> pd.DataFrame:
    with get_session() as session:
        query = select(AuditLog)
        if usuario:
            query = query.where(AuditLog.usuario == usuario)
        rows = session.execute(
            query.order_by(AuditLog.fecha_evento.desc(), AuditLog.id.desc()).limit(limit)
        ).scalars().all()

    df = pd.DataFrame([
        {
            "fecha_evento": row.fecha_evento,
            "usuario": row.usuario,
            "accion": row.accion,
            "entidad": row.entidad,
            "entidad_id": row.entidad_id,
            "descripcion": row.descripcion,
        }
        for row in rows
    ])
    if not df.empty:
        df["fecha_evento"] = pd.to_datetime(df["fecha_evento"])
    return df


def action_summary(days: int = 7, usuario: str | None = None) -> pd.DataFrame:
    since = datetime.now() - timedelta(days=days)
    with get_session() as session:
        query = select(
            AuditLog.accion.label("accion"),
            func.count(AuditLog.id).label("total"),
        ).where(AuditLog.fecha_evento >= since)
        if usuario:
            query = query.where(AuditLog.usuario == usuario)
        rows = session.execute(query.group_by(AuditLog.accion).order_by(func.count(AuditLog.id).desc())).mappings().all()
    return pd.DataFrame(rows)


def total_events(days: int = 7, usuario: str | None = None) -> int:
    since = datetime.now() - timedelta(days=days)
    with get_session() as session:
        query = select(func.count(AuditLog.id)).where(AuditLog.fecha_evento >= since)
        if usuario:
            query = query.where(AuditLog.usuario == usuario)
        total = session.scalar(query) or 0
    return int(total)
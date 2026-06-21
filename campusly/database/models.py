from __future__ import annotations

from datetime import date, time

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Docente(Base):
    __tablename__ = "docentes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_empleado: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(160), nullable=False)
    departamento: Mapped[str] = mapped_column(String(120), nullable=False)
    puesto: Mapped[str] = mapped_column(String(120), nullable=False)
    horario_entrada: Mapped[str] = mapped_column(String(5), nullable=False)
    horario_salida: Mapped[str] = mapped_column(String(5), nullable=False)
    qr_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    asistencias: Mapped[list["Asistencia"]] = relationship(back_populates="docente")


class Asistencia(Base):
    __tablename__ = "asistencias"
    __table_args__ = (UniqueConstraint("docente_id", "fecha", name="uq_docente_fecha"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    docente_id: Mapped[int] = mapped_column(ForeignKey("docentes.id"), nullable=False, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    hora: Mapped[time] = mapped_column(Time, nullable=False)
    estatus: Mapped[str] = mapped_column(String(20), nullable=False)
    usuario_registro: Mapped[str] = mapped_column(String(120), nullable=False)

    docente: Mapped[Docente] = relationship(back_populates="asistencias")


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    usuario: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)

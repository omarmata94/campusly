from __future__ import annotations

from datetime import date, time

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Turno(Base):
    __tablename__ = "turnos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    horas_clase: Mapped[list["HoraClase"]] = relationship(back_populates="turno")
    docente_horas: Mapped[list["DocenteHoraClase"]] = relationship(back_populates="turno")


class HoraClase(Base):
    __tablename__ = "horas_clase"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    turno_id: Mapped[int] = mapped_column(ForeignKey("turnos.id"), nullable=False, index=True)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    duracion_minutos: Mapped[int] = mapped_column(Integer, nullable=False)

    turno: Mapped[Turno] = relationship(back_populates="horas_clase")
    docente_horas: Mapped[list["DocenteHoraClase"]] = relationship(back_populates="hora_clase")
    asistencias: Mapped[list["Asistencia"]] = relationship(back_populates="hora_clase")


class Docente(Base):
    __tablename__ = "docentes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_empleado: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    apellido_paterno: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    apellido_materno: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    apellidos: Mapped[str] = mapped_column(String(160), nullable=False)
    departamento: Mapped[str] = mapped_column(String(120), nullable=False)
    puesto: Mapped[str] = mapped_column(String(120), nullable=False)
    horario_entrada: Mapped[str] = mapped_column(String(5), nullable=False)
    horario_salida: Mapped[str] = mapped_column(String(5), nullable=False)
    qr_uuid: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    asistencias: Mapped[list["Asistencia"]] = relationship(back_populates="docente")
    docente_horas: Mapped[list["DocenteHoraClase"]] = relationship(back_populates="docente")


class DocenteHoraClase(Base):
    __tablename__ = "docente_horas_clase"
    __table_args__ = (UniqueConstraint("docente_id", "turno_id", "numero_hora", "dia_semana", name="uq_docente_hora_dia"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    docente_id: Mapped[int] = mapped_column(ForeignKey("docentes.id"), nullable=False, index=True)
    turno_id: Mapped[int] = mapped_column(ForeignKey("turnos.id"), nullable=False, index=True)
    hora_clase_id: Mapped[int] = mapped_column(ForeignKey("horas_clase.id"), nullable=False, index=True)
    numero_hora: Mapped[int] = mapped_column(Integer, nullable=False)
    dia_semana: Mapped[int] = mapped_column(Integer, nullable=False)
    salon: Mapped[str] = mapped_column(String(20), nullable=False)
    grupo: Mapped[str] = mapped_column(String(50), nullable=False)

    docente: Mapped[Docente] = relationship(back_populates="docente_horas")
    turno: Mapped[Turno] = relationship(back_populates="docente_horas")
    hora_clase: Mapped[HoraClase] = relationship(back_populates="docente_horas")


class Asistencia(Base):
    __tablename__ = "asistencias"
    __table_args__ = (UniqueConstraint("docente_id", "fecha", "hora_clase_id", name="uq_docente_fecha_hora"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    docente_id: Mapped[int] = mapped_column(ForeignKey("docentes.id"), nullable=False, index=True)
    hora_clase_id: Mapped[int] = mapped_column(ForeignKey("horas_clase.id"), nullable=False, index=True)
    fecha: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    anio: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    cuatrimestre: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    hora: Mapped[time] = mapped_column(Time, nullable=False)
    turno: Mapped[str] = mapped_column(String(20), nullable=False)
    numero_hora: Mapped[int] = mapped_column(Integer, nullable=False)
    salon: Mapped[str] = mapped_column(String(20), nullable=False)
    grupo: Mapped[str] = mapped_column(String(50), nullable=False)
    estatus: Mapped[str] = mapped_column(String(20), nullable=False)
    usuario_registro: Mapped[str] = mapped_column(String(120), nullable=False)

    docente: Mapped[Docente] = relationship(back_populates="asistencias")
    hora_clase: Mapped[HoraClase] = relationship(back_populates="asistencias")


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    usuario: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)

from __future__ import annotations

from contextlib import contextmanager
from datetime import time
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, Usuario, Turno, HoraClase


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "campusly.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    future=True,
)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
    expire_on_commit=False,
)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_docentes_columns()
    _initialize_turnos_y_horas()


def _ensure_docentes_columns() -> None:
    with engine.begin() as connection:
        columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(docentes)").fetchall()}

        if "apellido_paterno" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE docentes ADD COLUMN apellido_paterno VARCHAR(120) NOT NULL DEFAULT ''"
            )
        if "apellido_materno" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE docentes ADD COLUMN apellido_materno VARCHAR(120) NOT NULL DEFAULT ''"
            )

        connection.exec_driver_sql(
            """
            UPDATE docentes
            SET
                apellido_paterno = CASE
                    WHEN instr(trim(apellidos), ' ') > 0
                        THEN substr(trim(apellidos), 1, instr(trim(apellidos), ' ') - 1)
                    ELSE trim(apellidos)
                END,
                apellido_materno = CASE
                    WHEN instr(trim(apellidos), ' ') > 0
                        THEN substr(trim(apellidos), instr(trim(apellidos), ' ') + 1)
                    ELSE ''
                END
            WHERE
                ifnull(apellido_paterno, '') = ''
                AND ifnull(apellido_materno, '') = ''
                AND ifnull(apellidos, '') <> ''
            """
        )


def _initialize_turnos_y_horas() -> None:
    """Inicializa turnos y horas clase si no existen."""
    with get_session() as session:
        # Verificar si ya existen turnos
        turno_matutino = session.scalar(select(Turno).where(Turno.nombre == "Matutino"))
        turno_nocturno = session.scalar(select(Turno).where(Turno.nombre == "Nocturno"))

        if not turno_matutino:
            turno_matutino = Turno(nombre="Matutino")
            session.add(turno_matutino)
            session.flush()

        if not turno_nocturno:
            turno_nocturno = Turno(nombre="Nocturno")
            session.add(turno_nocturno)
            session.flush()

        # Definir horas clase del matutino
        horas_matutino = [
            (1, time(8, 0), time(8, 50), 50),
            (2, time(8, 50), time(9, 40), 50),
            (3, time(9, 40), time(10, 30), 50),
            (4, time(10, 30), time(11, 20), 50),
            # Descanso: 11:20 - 11:50 (no es hora clase)
            (5, time(11, 50), time(12, 40), 50),
            (6, time(12, 40), time(13, 30), 50),
            (7, time(13, 30), time(14, 20), 50),
            (8, time(14, 20), time(15, 10), 50),
            (9, time(15, 10), time(16, 10), 60),  # Tiempo administrativo
            (10, time(16, 10), time(17, 0), 50),
        ]

        # Definir horas clase del nocturno
        horas_nocturno = [
            (1, time(18, 0), time(18, 40), 40),
            # Descanso Ing: 18:40 - 19:00
            (2, time(19, 0), time(19, 40), 40),
            # Descanso TSU: 19:20 - 19:40
            (3, time(19, 40), time(20, 20), 40),
            (4, time(20, 20), time(21, 0), 40),
        ]

        # Insertar horas del matutino
        for numero, hora_inicio, hora_fin, duracion in horas_matutino:
            existing = session.scalar(
                select(HoraClase).where(
                    HoraClase.turno_id == turno_matutino.id,
                    HoraClase.numero == numero,
                )
            )
            if not existing:
                session.add(
                    HoraClase(
                        turno_id=turno_matutino.id,
                        numero=numero,
                        hora_inicio=hora_inicio,
                        hora_fin=hora_fin,
                        duracion_minutos=duracion,
                    )
                )

        # Insertar horas del nocturno
        for numero, hora_inicio, hora_fin, duracion in horas_nocturno:
            existing = session.scalar(
                select(HoraClase).where(
                    HoraClase.turno_id == turno_nocturno.id,
                    HoraClase.numero == numero,
                )
            )
            if not existing:
                session.add(
                    HoraClase(
                        turno_id=turno_nocturno.id,
                        numero=numero,
                        hora_inicio=hora_inicio,
                        hora_fin=hora_fin,
                        duracion_minutos=duracion,
                    )
                )


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def has_users() -> bool:
    with get_session() as session:
        return session.scalar(select(Usuario.id).limit(1)) is not None

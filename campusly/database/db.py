from __future__ import annotations

from contextlib import contextmanager
from datetime import time
import os
from pathlib import Path
from tempfile import gettempdir
from typing import Iterator

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, Usuario, Turno, HoraClase
from services.time_utils import current_academic_period


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = BASE_DIR / "data" / "campusly.db"


def _resolve_db_path() -> Path:
    candidates = []

    env_path = os.environ.get("CAMPUSLY_DB_PATH")
    if env_path:
        candidates.append(Path(env_path).expanduser())

    candidates.append(DEFAULT_DB_PATH)
    candidates.append(Path(gettempdir()) / "campusly.db")

    for candidate in candidates:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            continue

        if candidate.parent.exists() and os.access(candidate.parent, os.W_OK):
            return candidate

    return Path(gettempdir()) / "campusly.db"


DB_PATH = _resolve_db_path()

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
    _ensure_docente_horas_period_columns()
    _ensure_asistencias_columns()
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

        columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(docentes)").fetchall()}
        if "departamento" not in columns:
            return

        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.exec_driver_sql("DROP TABLE IF EXISTS docentes_new")
        connection.exec_driver_sql(
            """
            CREATE TABLE docentes_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_empleado VARCHAR(32) NOT NULL UNIQUE,
                nombre VARCHAR(120) NOT NULL,
                apellido_paterno VARCHAR(120) NOT NULL DEFAULT '',
                apellido_materno VARCHAR(120) NOT NULL DEFAULT '',
                apellidos VARCHAR(160) NOT NULL,
                puesto VARCHAR(120) NOT NULL,
                horario_entrada VARCHAR(5) NOT NULL,
                horario_salida VARCHAR(5) NOT NULL,
                qr_uuid VARCHAR(36) NOT NULL UNIQUE,
                activo BOOLEAN NOT NULL
            )
            """
        )
        connection.exec_driver_sql(
            """
            INSERT INTO docentes_new (
                id, numero_empleado, nombre, apellido_paterno, apellido_materno, apellidos, puesto,
                horario_entrada, horario_salida, qr_uuid, activo
            )
            SELECT
                id, numero_empleado, nombre, apellido_paterno, apellido_materno, apellidos, puesto,
                horario_entrada, horario_salida, qr_uuid, activo
            FROM docentes
            """
        )
        connection.exec_driver_sql("DROP TABLE docentes")
        connection.exec_driver_sql("ALTER TABLE docentes_new RENAME TO docentes")
        connection.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS ix_docentes_numero_empleado ON docentes (numero_empleado)")
        connection.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS ix_docentes_qr_uuid ON docentes (qr_uuid)")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")


def _ensure_docente_horas_period_columns() -> None:
    current_year, current_cuatrimestre = current_academic_period()
    with engine.begin() as connection:
        columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(docente_horas_clase)").fetchall()}

        if "anio" in columns and "cuatrimestre" in columns:
            return

        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.exec_driver_sql("DROP TABLE IF EXISTS docente_horas_clase_new")
        connection.exec_driver_sql(
            """
            CREATE TABLE docente_horas_clase_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                docente_id INTEGER NOT NULL,
                turno_id INTEGER NOT NULL,
                hora_clase_id INTEGER NOT NULL,
                numero_hora INTEGER NOT NULL,
                dia_semana INTEGER NOT NULL,
                anio INTEGER NOT NULL,
                cuatrimestre INTEGER NOT NULL,
                salon VARCHAR(20) NOT NULL,
                grupo VARCHAR(50) NOT NULL,
                UNIQUE (docente_id, turno_id, numero_hora, dia_semana, anio, cuatrimestre),
                FOREIGN KEY(docente_id) REFERENCES docentes (id),
                FOREIGN KEY(turno_id) REFERENCES turnos (id),
                FOREIGN KEY(hora_clase_id) REFERENCES horas_clase (id)
            )
            """
        )
        connection.exec_driver_sql(
            f"""
            INSERT INTO docente_horas_clase_new (
                id, docente_id, turno_id, hora_clase_id, numero_hora, dia_semana, anio, cuatrimestre, salon, grupo
            )
            SELECT
                id, docente_id, turno_id, hora_clase_id, numero_hora, dia_semana,
                {current_year}, {current_cuatrimestre}, salon, grupo
            FROM docente_horas_clase
            """
        )
        connection.exec_driver_sql("DROP TABLE docente_horas_clase")
        connection.exec_driver_sql("ALTER TABLE docente_horas_clase_new RENAME TO docente_horas_clase")
        connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_docente_horas_clase_docente_id ON docente_horas_clase (docente_id)")
        connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_docente_horas_clase_turno_id ON docente_horas_clase (turno_id)")
        connection.exec_driver_sql("CREATE INDEX IF NOT EXISTS ix_docente_horas_clase_hora_clase_id ON docente_horas_clase (hora_clase_id)")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")


def _ensure_asistencias_columns() -> None:
    with engine.begin() as connection:
        columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(asistencias)").fetchall()}

        if "anio" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE asistencias ADD COLUMN anio INTEGER NOT NULL DEFAULT 0"
            )
        if "cuatrimestre" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE asistencias ADD COLUMN cuatrimestre INTEGER NOT NULL DEFAULT 0"
            )

        connection.exec_driver_sql(
            """
            UPDATE asistencias
            SET anio = CASE WHEN anio = 0 THEN CAST(strftime('%Y', fecha) AS INTEGER) ELSE anio END,
                cuatrimestre = CASE
                    WHEN cuatrimestre = 0 THEN
                        CASE
                            WHEN CAST(strftime('%m', fecha) AS INTEGER) <= 4 THEN 1
                            WHEN CAST(strftime('%m', fecha) AS INTEGER) <= 8 THEN 2
                            ELSE 3
                        END
                    ELSE cuatrimestre
                END
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

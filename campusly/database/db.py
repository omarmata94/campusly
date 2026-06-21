from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, Usuario


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

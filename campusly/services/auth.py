from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select

from database.db import get_session
from database.models import Usuario


PBKDF2_ITERATIONS = 210000


@dataclass
class AuthenticatedUser:
    id: int
    nombre: str
    usuario: str
    rol: str


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            PBKDF2_ITERATIONS,
        ).hex()
        return f"{PBKDF2_ITERATIONS}${salt}${digest}"

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        try:
            iterations_str, salt, digest = stored_hash.split("$")
            iterations = int(iterations_str)
        except ValueError:
            return False

        test_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        ).hex()
        return hmac.compare_digest(test_digest, digest)

    @staticmethod
    def create_user(nombre: str, usuario: str, password: str, rol: str) -> AuthenticatedUser:
        with get_session() as session:
            existing = session.scalar(select(Usuario).where(Usuario.usuario == usuario))
            if existing:
                raise ValueError("El usuario ya existe")

            record = Usuario(
                nombre=nombre.strip(),
                usuario=usuario.strip(),
                password_hash=AuthService.hash_password(password),
                rol=rol,
            )
            session.add(record)
            session.flush()
            session.refresh(record)
            return AuthenticatedUser(
                id=record.id,
                nombre=record.nombre,
                usuario=record.usuario,
                rol=record.rol,
            )

    @staticmethod
    def authenticate(usuario: str, password: str) -> Optional[AuthenticatedUser]:
        with get_session() as session:
            record = session.scalar(select(Usuario).where(Usuario.usuario == usuario.strip()))
            if not record or not AuthService.verify_password(password, record.password_hash):
                return None

            return AuthenticatedUser(
                id=record.id,
                nombre=record.nombre,
                usuario=record.usuario,
                rol=record.rol,
            )

    @staticmethod
    def bootstrap_first_admin(nombre: str, usuario: str, password: str) -> AuthenticatedUser:
        return AuthService.create_user(nombre=nombre, usuario=usuario, password=password, rol="Administrador")

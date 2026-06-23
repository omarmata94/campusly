from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import func, select

from database.db import get_session, init_db
from database.models import Usuario
from services.auth import AuthService
from services.ui import APP_NAME, configure_page, logout_button, page_hero, render_sidebar, require_login


def _users_dataframe() -> pd.DataFrame:
    with get_session() as session:
        users = session.execute(select(Usuario).order_by(Usuario.id.desc())).scalars().all()

    rows = [
        {
            "ID": u.id,
            "Nombre": u.nombre,
            "Usuario": u.usuario,
            "Rol": u.rol,
        }
        for u in users
    ]
    return pd.DataFrame(rows)


def _list_users() -> list[Usuario]:
    with get_session() as session:
        return session.execute(select(Usuario).order_by(Usuario.id.asc())).scalars().all()


def _admin_count() -> int:
    with get_session() as session:
        count = session.scalar(select(func.count()).select_from(Usuario).where(Usuario.rol == "Administrador"))
        return int(count or 0)


def _reset_password(user_id: int, new_password: str) -> None:
    with get_session() as session:
        record = session.get(Usuario, user_id)
        if not record:
            raise ValueError("El usuario no existe")
        record.password_hash = AuthService.hash_password(new_password)
        session.flush()


def _update_role(user_id: int, new_role: str, current_user_id: int) -> None:
    with get_session() as session:
        record = session.get(Usuario, user_id)
        if not record:
            raise ValueError("El usuario no existe")

        if record.id == current_user_id:
            raise ValueError("No puedes cambiar tu propio rol desde esta pantalla")

        if record.rol == "Administrador" and new_role != "Administrador" and _admin_count() <= 1:
            raise ValueError("No puedes degradar al último administrador")

        record.rol = new_role
        session.flush()


def _delete_user(user_id: int, current_user_id: int) -> None:
    with get_session() as session:
        record = session.get(Usuario, user_id)
        if not record:
            raise ValueError("El usuario no existe")

        if record.id == current_user_id:
            raise ValueError("No puedes eliminar tu propio usuario")

        if record.rol == "Administrador" and _admin_count() <= 1:
            raise ValueError("No puedes eliminar al último administrador")

        session.delete(record)
        session.flush()


def main() -> None:
    init_db()
    configure_page(f"{APP_NAME} | Usuarios")
    user = require_login(["Administrador"])

    render_sidebar(user)
    logout_button()

    page_hero("Usuarios", "Gestión de cuentas del sistema. Solo administradores.")

    st.subheader("Crear usuario")
    with st.form("form_create_user", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre completo")
        usuario = c2.text_input("Usuario")
        c3, c4, c5 = st.columns(3)
        password = c3.text_input("Contraseña", type="password")
        confirm_password = c4.text_input("Confirmar contraseña", type="password")
        rol = c5.selectbox("Rol", ["Prefecto", "Administrador"], index=0)
        submitted = st.form_submit_button("Crear usuario", use_container_width=True, type="primary")

    if submitted:
        if not nombre.strip() or not usuario.strip() or not password:
            st.error("Todos los campos son obligatorios.")
        elif password != confirm_password:
            st.error("Las contraseñas no coinciden.")
        else:
            try:
                AuthService.create_user(
                    nombre=nombre.strip(),
                    usuario=usuario.strip(),
                    password=password,
                    rol=rol,
                )
                st.success(f"Usuario {rol} creado correctamente.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"No se pudo crear el usuario: {exc}")

    st.subheader("Administrar usuarios")
    users = _list_users()
    if not users:
        st.info("No hay usuarios para administrar.")
    else:
        user_options = {f"{u.id} - {u.usuario} ({u.rol})": u.id for u in users}
        selected_label = st.selectbox("Seleccionar usuario", list(user_options.keys()))
        selected_user_id = user_options[selected_label]

        tab_password, tab_role, tab_delete = st.tabs(["Restablecer contraseña", "Cambiar rol", "Eliminar usuario"])

        with tab_password:
            with st.form("form_reset_password"):
                new_password = st.text_input("Nueva contraseña", type="password")
                confirm_new_password = st.text_input("Confirmar nueva contraseña", type="password")
                submit_reset = st.form_submit_button("Restablecer contraseña", use_container_width=True)

            if submit_reset:
                if not new_password:
                    st.error("La nueva contraseña es obligatoria.")
                elif new_password != confirm_new_password:
                    st.error("Las contraseñas no coinciden.")
                else:
                    try:
                        _reset_password(selected_user_id, new_password)
                        st.success("Contraseña restablecida correctamente.")
                    except Exception as exc:
                        st.error(str(exc))

        with tab_role:
            with st.form("form_change_role"):
                new_role = st.selectbox("Nuevo rol", ["Prefecto", "Administrador"], index=0)
                submit_role = st.form_submit_button("Actualizar rol", use_container_width=True)

            if submit_role:
                try:
                    _update_role(selected_user_id, new_role, current_user_id=int(user["id"]))
                    st.success("Rol actualizado correctamente.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        with tab_delete:
            confirm_delete = st.checkbox("Confirmo que deseo eliminar este usuario", key="confirm_delete_user")
            if st.button("Eliminar usuario", type="secondary", use_container_width=True, disabled=not confirm_delete):
                try:
                    _delete_user(selected_user_id, current_user_id=int(user["id"]))
                    st.success("Usuario eliminado correctamente.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    st.subheader("Usuarios registrados")
    df = _users_dataframe()
    if df.empty:
        st.info("No hay usuarios registrados.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()

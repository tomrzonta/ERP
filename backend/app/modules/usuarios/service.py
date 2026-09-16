"""Regras de negócio de usuários."""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import Conflito
from app.core.security import hash_senha
from app.modules.usuarios import repository
from app.modules.usuarios.models import Usuario


def normalizar_email(email: str) -> str:
    return email.strip().lower()


def por_id(db: Session, usuario_id: uuid.UUID) -> Usuario | None:
    return repository.por_id(db, usuario_id)


def por_email(db: Session, email: str) -> Usuario | None:
    return repository.por_email(db, normalizar_email(email))


def criar_usuario(db: Session, *, nome: str, email: str, senha: str) -> Usuario:
    email = normalizar_email(email)
    if repository.por_email(db, email) is not None:
        raise Conflito("Este e-mail já está cadastrado.")
    usuario = Usuario(nome=nome.strip(), email=email, senha_hash=hash_senha(senha))
    db.add(usuario)
    db.flush()
    return usuario


def registrar_login(usuario: Usuario, agora: datetime) -> None:
    usuario.ultimo_login_em = agora

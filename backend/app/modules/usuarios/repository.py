"""Consultas do módulo de usuários."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.usuarios.models import Usuario


def por_id(db: Session, usuario_id: uuid.UUID) -> Usuario | None:
    return db.get(Usuario, usuario_id)


def por_email(db: Session, email: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(Usuario.email == email))

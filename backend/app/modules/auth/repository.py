"""Consultas do módulo de autenticação."""

import uuid
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.modules.auth.models import Sessao


def sessao_por_id(db: Session, sessao_id: uuid.UUID) -> Sessao | None:
    return db.get(Sessao, sessao_id)


def revogar_sessoes_do_usuario(db: Session, usuario_id: uuid.UUID, agora: datetime) -> None:
    db.execute(
        update(Sessao)
        .where(Sessao.usuario_id == usuario_id, Sessao.revogada_em.is_(None))
        .values(revogada_em=agora)
        .execution_options(synchronize_session="fetch")
    )

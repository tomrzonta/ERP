"""Consultas do módulo de assinaturas."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.assinaturas.models import Assinatura, Plano, PlanoRegra


def plano_por_id(db: Session, plano_id: uuid.UUID) -> Plano | None:
    return db.get(Plano, plano_id)


def plano_por_codigo(db: Session, codigo: str) -> Plano | None:
    return db.scalar(select(Plano).where(Plano.codigo == codigo))


def assinatura_da_empresa(db: Session, empresa_id: uuid.UUID) -> Assinatura | None:
    return db.scalar(select(Assinatura).where(Assinatura.empresa_id == empresa_id))


def regra(db: Session, plano_id: uuid.UUID, chave: str) -> PlanoRegra | None:
    return db.get(PlanoRegra, (plano_id, chave))

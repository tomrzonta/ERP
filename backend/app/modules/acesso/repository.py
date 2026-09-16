"""Consultas do módulo de acesso."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.acesso.models import Membro, Papel, PapelPermissao, StatusMembro


def codigos_do_papel(db: Session, papel_id: uuid.UUID) -> list[str]:
    return list(
        db.scalars(select(PapelPermissao.permissao).where(PapelPermissao.papel_id == papel_id))
    )


def vinculos_ativos(db: Session, usuario_id: uuid.UUID) -> list[tuple[Membro, Papel]]:
    consulta = (
        select(Membro, Papel)
        .join(Papel, Papel.id == Membro.papel_id)
        .where(Membro.usuario_id == usuario_id, Membro.status == StatusMembro.ATIVO)
    )
    return [(membro, papel) for membro, papel in db.execute(consulta)]


def vinculo_ativo(
    db: Session, empresa_id: uuid.UUID, usuario_id: uuid.UUID
) -> tuple[Membro, Papel] | None:
    consulta = (
        select(Membro, Papel)
        .join(Papel, Papel.id == Membro.papel_id)
        .where(
            Membro.empresa_id == empresa_id,
            Membro.usuario_id == usuario_id,
            Membro.status == StatusMembro.ATIVO,
        )
    )
    linha = db.execute(consulta).first()
    return (linha[0], linha[1]) if linha else None

"""Regras de negócio de papéis, permissões e membros.

Services fazem flush, mas não commit: quem confirma a transação é a
camada que recebeu a requisição. Assim, operações que envolvem vários
módulos são confirmadas ou desfeitas juntas.
"""

import uuid

from sqlalchemy.orm import Session

from app.core.permissions import catalogo, validar_codigos
from app.modules.acesso import repository
from app.modules.acesso.models import Membro, Papel, PapelPermissao, StatusMembro
from app.modules.acesso.papeis_padrao import DONO, PAPEIS_PADRAO


def criar_papeis_padrao(db: Session, empresa_id: uuid.UUID) -> dict[str, Papel]:
    """Cria os papéis padrão de uma empresa, indexados pelo código padrão."""
    papeis: dict[str, Papel] = {}
    for modelo in PAPEIS_PADRAO:
        validar_codigos(modelo.permissoes)
        papel = Papel(
            empresa_id=empresa_id,
            nome=modelo.nome,
            descricao=modelo.descricao,
            codigo_padrao=modelo.codigo,
            protegido=modelo.protegido,
        )
        db.add(papel)
        db.flush()
        for codigo in sorted(modelo.permissoes):
            db.add(PapelPermissao(papel_id=papel.id, permissao=codigo))
        papeis[modelo.codigo] = papel
    db.flush()
    return papeis


def adicionar_membro(
    db: Session,
    empresa_id: uuid.UUID,
    usuario_id: uuid.UUID,
    papel_id: uuid.UUID,
    status: StatusMembro = StatusMembro.ATIVO,
) -> Membro:
    membro = Membro(
        empresa_id=empresa_id, usuario_id=usuario_id, papel_id=papel_id, status=status
    )
    db.add(membro)
    db.flush()
    return membro


def permissoes_do_papel(db: Session, papel: Papel) -> frozenset[str]:
    """Permissões efetivas de um papel. O Dono tem todas."""
    if papel.codigo_padrao == DONO:
        return frozenset(catalogo())
    return frozenset(repository.codigos_do_papel(db, papel.id))

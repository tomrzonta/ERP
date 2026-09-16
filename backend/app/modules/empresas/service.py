"""Regras de negócio de empresas."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.acesso import service as acesso_service
from app.modules.acesso.models import Membro
from app.modules.acesso.papeis_padrao import DONO
from app.modules.assinaturas import service as assinaturas_service
from app.modules.assinaturas.models import Assinatura
from app.modules.empresas import repository
from app.modules.empresas.models import Empresa
from app.shared.texto import gerar_slug


@dataclass
class EmpresaCriada:
    empresa: Empresa
    dono: Membro
    assinatura: Assinatura


def gerar_slug_unico(db: Session, nome: str) -> str:
    base = gerar_slug(nome)
    candidato = base
    sufixo = 2
    while repository.slug_em_uso(db, candidato):
        candidato = f"{base}-{sufixo}"
        sufixo += 1
    return candidato


def criar_empresa_com_padroes(
    db: Session,
    *,
    nome_fantasia: str,
    usuario_dono_id: uuid.UUID,
    agora: datetime | None = None,
) -> EmpresaCriada:
    """Cria a empresa com papéis padrão, o usuário como Dono e o trial do Pro."""
    nome = nome_fantasia.strip()
    empresa = Empresa(nome_fantasia=nome, slug=gerar_slug_unico(db, nome))
    db.add(empresa)
    db.flush()

    papeis = acesso_service.criar_papeis_padrao(db, empresa.id)
    dono = acesso_service.adicionar_membro(db, empresa.id, usuario_dono_id, papeis[DONO].id)
    assinatura = assinaturas_service.criar_assinatura_trial(db, empresa.id, agora=agora)

    return EmpresaCriada(empresa=empresa, dono=dono, assinatura=assinatura)

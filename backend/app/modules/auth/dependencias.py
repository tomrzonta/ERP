"""Dependências de autenticação usadas pelos routers de todos os módulos.

- obter_autenticado: usuário logado, com ou sem empresa escolhida.
- obter_contexto: usuário dentro de uma empresa, com papel e permissões.
- requer_permissao / requer_recurso: exigências adicionais por rota.

A empresa vem SEMPRE da sessão validada, nunca do corpo ou da URL.
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import EmpresaNaoSelecionada, NaoAutenticado, PermissaoNegada
from app.core.permissions import validar_codigos
from app.core.security import TokenInvalido, ler_access_token
from app.modules.acesso import service as acesso_service
from app.modules.assinaturas import service as assinaturas_service
from app.modules.assinaturas.regras import Recurso
from app.modules.auth import repository
from app.modules.usuarios import service as usuarios_service

_bearer = HTTPBearer(auto_error=False)
MENSAGEM = "Sessão inválida ou expirada. Entre novamente."


@dataclass(frozen=True)
class Autenticado:
    usuario_id: uuid.UUID
    sessao_id: uuid.UUID
    empresa_id: uuid.UUID | None


@dataclass(frozen=True)
class Contexto:
    usuario_id: uuid.UUID
    sessao_id: uuid.UUID
    empresa_id: uuid.UUID
    papel_id: uuid.UUID
    papel_nome: str
    permissoes: frozenset[str]


def obter_autenticado(
    credenciais: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Autenticado:
    if credenciais is None:
        raise NaoAutenticado("Autenticação necessária.")
    try:
        dados = ler_access_token(credenciais.credentials)
    except TokenInvalido as erro:
        raise NaoAutenticado(MENSAGEM) from erro

    sessao = repository.sessao_por_id(db, dados.sessao_id)
    agora = datetime.now(UTC)
    if (
        sessao is None
        or sessao.revogada_em is not None
        or sessao.expira_em <= agora
        or sessao.usuario_id != dados.usuario_id
        # Token emitido para outra empresa, antes de uma troca
        or sessao.empresa_id != dados.empresa_id
    ):
        raise NaoAutenticado(MENSAGEM)

    usuario = usuarios_service.por_id(db, dados.usuario_id)
    if usuario is None or not usuario.ativo:
        raise NaoAutenticado(MENSAGEM)

    return Autenticado(
        usuario_id=dados.usuario_id, sessao_id=dados.sessao_id, empresa_id=dados.empresa_id
    )


def obter_contexto(
    autenticado: Autenticado = Depends(obter_autenticado),
    db: Session = Depends(get_db),
) -> Contexto:
    if autenticado.empresa_id is None:
        raise EmpresaNaoSelecionada("Escolha uma empresa para continuar.")

    acesso = acesso_service.acesso_ativo(db, autenticado.empresa_id, autenticado.usuario_id)
    if acesso is None:
        raise PermissaoNegada("Você não tem mais acesso a esta empresa.")

    return Contexto(
        usuario_id=autenticado.usuario_id,
        sessao_id=autenticado.sessao_id,
        empresa_id=autenticado.empresa_id,
        papel_id=acesso.papel.id,
        papel_nome=acesso.papel.nome,
        permissoes=acesso.permissoes,
    )


def requer_permissao(codigo: str) -> Callable[..., Contexto]:
    """Uso: contexto: Contexto = Depends(requer_permissao("membros.ver"))"""
    # Código inexistente falha ao iniciar a aplicação, não em produção
    validar_codigos({codigo})

    def dependencia(contexto: Contexto = Depends(obter_contexto)) -> Contexto:
        if codigo not in contexto.permissoes:
            raise PermissaoNegada("Você não tem permissão para esta ação.")
        return contexto

    return dependencia


def requer_recurso(recurso: Recurso) -> Callable[..., Contexto]:
    """Uso: contexto: Contexto = Depends(requer_recurso(Recurso.CUPONS))"""

    def dependencia(
        contexto: Contexto = Depends(obter_contexto),
        db: Session = Depends(get_db),
    ) -> Contexto:
        assinaturas_service.exigir_recurso(db, contexto.empresa_id, recurso)
        return contexto

    return dependencia

"""Cadastro, login, renovação e encerramento de sessões."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NaoAutenticado, NaoEncontrado
from app.core.security import (
    criar_access_token,
    gerar_segredo,
    hash_token,
    hashes_iguais,
    verificar_senha,
)
from app.modules.acesso import service as acesso_service
from app.modules.auth import repository
from app.modules.auth.models import Sessao
from app.modules.empresas import service as empresas_service
from app.modules.usuarios import service as usuarios_service

MENSAGEM_LOGIN_INVALIDO = "E-mail ou senha inválidos."
MENSAGEM_SESSAO_INVALIDA = "Sessão inválida ou expirada. Entre novamente."


@dataclass(frozen=True)
class Tokens:
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class EmpresaDisponivel:
    id: uuid.UUID
    nome: str
    papel: str


@dataclass(frozen=True)
class ResultadoLogin:
    tokens: Tokens
    empresa_ativa_id: uuid.UUID | None
    empresas: list[EmpresaDisponivel] = field(default_factory=list)


def _agora(agora: datetime | None) -> datetime:
    return agora or datetime.now(UTC)


def _emitir(sessao: Sessao, segredo: str, agora: datetime) -> Tokens:
    return Tokens(
        access_token=criar_access_token(sessao.usuario_id, sessao.id, sessao.empresa_id, agora),
        # O id da sessão vai junto para localizar a sessão sem buscar pelo hash
        refresh_token=f"{sessao.id}.{segredo}",
    )


def _abrir_sessao(
    db: Session,
    *,
    usuario_id: uuid.UUID,
    empresa_id: uuid.UUID | None,
    user_agent: str | None,
    ip: str | None,
    agora: datetime,
) -> Tokens:
    segredo = gerar_segredo()
    sessao = Sessao(
        usuario_id=usuario_id,
        empresa_id=empresa_id,
        token_hash=hash_token(segredo),
        expira_em=agora + timedelta(days=settings.refresh_token_dias),
        ultimo_uso_em=agora,
        user_agent=(user_agent or "")[:255] or None,
        ip=ip,
    )
    db.add(sessao)
    db.flush()
    return _emitir(sessao, segredo, agora)


def empresas_disponiveis(db: Session, usuario_id: uuid.UUID) -> list[EmpresaDisponivel]:
    vinculos = acesso_service.vinculos_ativos(db, usuario_id)
    papel_por_empresa = {membro.empresa_id: papel.nome for membro, papel in vinculos}
    empresas = empresas_service.ativas_por_ids(db, papel_por_empresa.keys())
    return sorted(
        (
            EmpresaDisponivel(id=e.id, nome=e.nome_fantasia, papel=papel_por_empresa[e.id])
            for e in empresas
        ),
        key=lambda item: item.nome.lower(),
    )


def cadastrar(
    db: Session,
    *,
    nome: str,
    email: str,
    senha: str,
    nome_empresa: str,
    user_agent: str | None = None,
    ip: str | None = None,
    agora: datetime | None = None,
) -> ResultadoLogin:
    """Cria usuário e empresa, e já entra na empresa criada."""
    agora = _agora(agora)
    usuario = usuarios_service.criar_usuario(db, nome=nome, email=email, senha=senha)
    criada = empresas_service.criar_empresa_com_padroes(
        db, nome_fantasia=nome_empresa, usuario_dono_id=usuario.id, agora=agora
    )
    usuarios_service.registrar_login(usuario, agora)
    tokens = _abrir_sessao(
        db,
        usuario_id=usuario.id,
        empresa_id=criada.empresa.id,
        user_agent=user_agent,
        ip=ip,
        agora=agora,
    )
    return ResultadoLogin(
        tokens=tokens,
        empresa_ativa_id=criada.empresa.id,
        empresas=empresas_disponiveis(db, usuario.id),
    )


def login(
    db: Session,
    *,
    email: str,
    senha: str,
    user_agent: str | None = None,
    ip: str | None = None,
    agora: datetime | None = None,
) -> ResultadoLogin:
    agora = _agora(agora)
    usuario = usuarios_service.por_email(db, email)
    senha_ok = verificar_senha(senha, usuario.senha_hash if usuario else None)
    if usuario is None or not senha_ok or not usuario.ativo:
        raise NaoAutenticado(MENSAGEM_LOGIN_INVALIDO)

    empresas = empresas_disponiveis(db, usuario.id)
    # Com uma única empresa, entra direto nela
    empresa_ativa_id = empresas[0].id if len(empresas) == 1 else None

    usuarios_service.registrar_login(usuario, agora)
    tokens = _abrir_sessao(
        db,
        usuario_id=usuario.id,
        empresa_id=empresa_ativa_id,
        user_agent=user_agent,
        ip=ip,
        agora=agora,
    )
    return ResultadoLogin(tokens=tokens, empresa_ativa_id=empresa_ativa_id, empresas=empresas)


def renovar(db: Session, refresh_token: str, agora: datetime | None = None) -> Tokens:
    """Troca o token de renovação por um novo.

    Se um token antigo for reapresentado, a sessão é revogada: é sinal de
    que o token pode ter sido copiado. Nesse caso a revogação precisa ser
    confirmada mesmo com o erro (ver router).
    """
    agora = _agora(agora)
    try:
        sessao_texto, segredo = refresh_token.split(".", 1)
        sessao_id = uuid.UUID(sessao_texto)
    except ValueError as erro:
        raise NaoAutenticado(MENSAGEM_SESSAO_INVALIDA) from erro

    sessao = repository.sessao_por_id(db, sessao_id)
    if sessao is None or sessao.revogada_em is not None or sessao.expira_em <= agora:
        raise NaoAutenticado(MENSAGEM_SESSAO_INVALIDA)

    if not hashes_iguais(sessao.token_hash, hash_token(segredo)):
        sessao.revogada_em = agora
        db.flush()
        raise NaoAutenticado(MENSAGEM_SESSAO_INVALIDA)

    usuario = usuarios_service.por_id(db, sessao.usuario_id)
    if usuario is None or not usuario.ativo:
        sessao.revogada_em = agora
        db.flush()
        raise NaoAutenticado(MENSAGEM_SESSAO_INVALIDA)

    novo_segredo = gerar_segredo()
    sessao.token_hash = hash_token(novo_segredo)
    sessao.ultimo_uso_em = agora
    db.flush()
    return _emitir(sessao, novo_segredo, agora)


def definir_empresa_ativa(
    db: Session,
    *,
    usuario_id: uuid.UUID,
    sessao_id: uuid.UUID,
    empresa_id: uuid.UUID,
    agora: datetime | None = None,
) -> str:
    """Troca a empresa da sessão e devolve um novo token de acesso."""
    agora = _agora(agora)
    empresa = empresas_service.por_id(db, empresa_id)
    acesso = acesso_service.acesso_ativo(db, empresa_id, usuario_id)
    # Empresa de outra pessoa responde como inexistente
    if empresa is None or not empresa.ativa or acesso is None:
        raise NaoEncontrado("Empresa não encontrada.")

    sessao = repository.sessao_por_id(db, sessao_id)
    if sessao is None or sessao.revogada_em is not None:
        raise NaoAutenticado(MENSAGEM_SESSAO_INVALIDA)

    sessao.empresa_id = empresa_id
    sessao.ultimo_uso_em = agora
    db.flush()
    return criar_access_token(usuario_id, sessao.id, empresa_id, agora)


def sair(db: Session, sessao_id: uuid.UUID, agora: datetime | None = None) -> None:
    sessao = repository.sessao_por_id(db, sessao_id)
    if sessao is not None and sessao.revogada_em is None:
        sessao.revogada_em = _agora(agora)
        db.flush()


def sair_de_todos(db: Session, usuario_id: uuid.UUID, agora: datetime | None = None) -> None:
    repository.revogar_sessoes_do_usuario(db, usuario_id, _agora(agora))
    db.flush()

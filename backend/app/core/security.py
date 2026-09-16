"""Senhas e tokens.

Nada de criptografia escrita à mão: hash de senha com Argon2 (pwdlib)
e tokens de acesso assinados com JWT (PyJWT).
"""

import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

ALGORITMO = "HS256"

_hasher = PasswordHash.recommended()
# Usado quando o e-mail não existe, para o tempo de resposta não revelar isso
_HASH_FALSO = _hasher.hash("senha-inexistente-apenas-para-tempo-constante")


class TokenInvalido(Exception):
    pass


@dataclass(frozen=True)
class DadosAccessToken:
    usuario_id: uuid.UUID
    sessao_id: uuid.UUID
    empresa_id: uuid.UUID | None


def hash_senha(senha: str) -> str:
    return _hasher.hash(senha)


def verificar_senha(senha: str, senha_hash: str | None) -> bool:
    if senha_hash is None:
        _hasher.verify(senha, _HASH_FALSO)
        return False
    return _hasher.verify(senha, senha_hash)


def criar_access_token(
    usuario_id: uuid.UUID,
    sessao_id: uuid.UUID,
    empresa_id: uuid.UUID | None,
    agora: datetime | None = None,
) -> str:
    agora = agora or datetime.now(UTC)
    payload = {
        "sub": str(usuario_id),
        "sid": str(sessao_id),
        "emp": str(empresa_id) if empresa_id else None,
        "typ": "access",
        "iat": agora,
        "exp": agora + timedelta(minutes=settings.access_token_minutos),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITMO)


def ler_access_token(token: str) -> DadosAccessToken:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[ALGORITMO],
            options={"require": ["exp", "sub", "sid"]},
        )
        if payload.get("typ") != "access":
            raise TokenInvalido()
        empresa = payload.get("emp")
        return DadosAccessToken(
            usuario_id=uuid.UUID(payload["sub"]),
            sessao_id=uuid.UUID(payload["sid"]),
            empresa_id=uuid.UUID(empresa) if empresa else None,
        )
    except (jwt.PyJWTError, ValueError, KeyError) as erro:
        raise TokenInvalido() from erro


def gerar_segredo() -> str:
    return secrets.token_urlsafe(48)


def hash_token(valor: str) -> str:
    """Tokens de renovação e convites são guardados só como hash."""
    return hashlib.sha256(valor.encode()).hexdigest()


def hashes_iguais(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)

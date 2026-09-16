"""Utilidades para evitar vazamento de segredos em logs."""

from app.core.config import settings


def mascarar_segredos(texto: str) -> str:
    """Remove a senha do banco de qualquer texto antes de registrar em log."""
    credenciais = settings.database_url.split("://", 1)[-1].rpartition("@")[0]
    _, _, senha = credenciais.partition(":")
    for variante in {senha, senha.strip("[]")}:
        if variante:
            texto = texto.replace(variante, "***")
    return texto

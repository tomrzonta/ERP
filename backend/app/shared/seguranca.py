"""Utilidades para evitar vazamento de segredos em logs."""

import re

from app.core.config import settings


def mascarar_segredos(texto: str) -> str:
    """Remove a senha do banco de qualquer texto antes de registrar em log.

    Mascara cada trecho da parte de credenciais da URL, para funcionar
    mesmo quando a URL está malformada.
    """
    sem_prefixo = settings.database_url.split("://", 1)[-1]
    credenciais = sem_prefixo.rpartition("@")[0]
    _, _, senha = credenciais.partition(":")

    for trecho in re.split(r"[@\[\]]", senha):
        if len(trecho) >= 4:
            texto = texto.replace(trecho, "***")
    return texto

"""Utilidades de texto."""

import re
import unicodedata


def gerar_slug(texto: str, tamanho_maximo: int = 50) -> str:
    """Converte um nome em endereço amigável: "Café & Cia" -> "cafe-cia"."""
    sem_acentos = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", sem_acentos.lower()).strip("-")
    slug = slug[:tamanho_maximo].rstrip("-")
    return slug or "loja"

"""Geração de CSV dos relatórios.

Formato pensado pro Excel em português: separador `;`, vírgula decimal,
UTF-8 com BOM (senão os acentos quebram) e data em horário de Brasília.
"""

import csv
import io
from datetime import datetime, timedelta, timezone
from decimal import Decimal

_BRASILIA = timezone(timedelta(hours=-3))
_BOM = "\ufeff"


def numero(valor: Decimal, casas: int = 2) -> str:
    return f"{valor:.{casas}f}".replace(".", ",")


def data_hora(momento: datetime) -> str:
    return momento.astimezone(_BRASILIA).strftime("%d/%m/%Y %H:%M")


def texto(valor: str | None) -> str:
    """Neutraliza fórmulas: texto digitado pelo usuário que começa com = + - @
    seria executado pela planilha (CSV injection)."""
    if not valor:
        return ""
    return "'" + valor if valor[0] in "=+-@\t\r" else valor


def gerar_csv(cabecalho: list[str], linhas: list[list[str]]) -> str:
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";", lineterminator="\r\n")
    escritor.writerow(cabecalho)
    escritor.writerows(linhas)
    return _BOM + saida.getvalue()

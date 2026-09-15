"""Utilidades de dinheiro. Nunca use float para valores monetários."""

from decimal import ROUND_HALF_UP, Decimal

CENTAVO = Decimal("0.01")


def to_money(valor: Decimal | int | str) -> Decimal:
    """Converte para Decimal com 2 casas, arredondando meio para cima."""
    if isinstance(valor, float):
        raise TypeError("Não use float para dinheiro. Passe str, int ou Decimal.")
    return Decimal(str(valor)).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def margem_percentual(preco: Decimal, custo: Decimal) -> Decimal | None:
    """Margem sobre o preço de venda: (preço - custo) / preço * 100.

    Ex.: preço 100, custo 60 -> margem 40%.
    Retorna None se o preço for zero.
    """
    if preco == 0:
        return None
    return ((preco - custo) / preco * 100).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def markup_percentual(preco: Decimal, custo: Decimal) -> Decimal | None:
    """Markup sobre o custo: (preço - custo) / custo * 100.

    Ex.: preço 100, custo 60 -> markup 66,67%.
    Retorna None se o custo for zero.
    """
    if custo == 0:
        return None
    return ((preco - custo) / custo * 100).quantize(CENTAVO, rounding=ROUND_HALF_UP)

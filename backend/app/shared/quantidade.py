"""Quantidades. Nunca use float: gramas e frações perdem precisão."""

from decimal import ROUND_HALF_UP, Decimal

CASAS_QUANTIDADE = Decimal("0.0001")
CASAS_CUSTO = Decimal("0.000001")


def to_quantidade(valor: Decimal | int | str) -> Decimal:
    """Converte para Decimal com 4 casas."""
    if isinstance(valor, float):
        raise TypeError("Não use float para quantidades. Passe str, int ou Decimal.")
    return Decimal(str(valor)).quantize(CASAS_QUANTIDADE, rounding=ROUND_HALF_UP)


def to_custo(valor: Decimal | int | str) -> Decimal:
    """Custo unitário com 6 casas (ex. custo por grama)."""
    if isinstance(valor, float):
        raise TypeError("Não use float para custos. Passe str, int ou Decimal.")
    return Decimal(str(valor)).quantize(CASAS_CUSTO, rounding=ROUND_HALF_UP)

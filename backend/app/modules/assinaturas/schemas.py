"""Formatos de saída da API de assinatura."""

from decimal import Decimal

from pydantic import BaseModel


class UsoDoLimiteSaida(BaseModel):
    chave: str
    rotulo: str
    usado: int
    # Nulo = ilimitado no plano atual.
    limite: int | None
    percentual: Decimal | None


class UsoSaida(BaseModel):
    plano: str
    limites: list[UsoDoLimiteSaida]

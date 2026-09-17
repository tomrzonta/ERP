"""Catálogo de unidades de medida.

O código é a fonte da verdade; uma migração de dados insere as mesmas
unidades no banco, para a chave estrangeira dos produtos.

Cada unidade tem uma grandeza e um fator para a unidade canônica dela
(g para massa, ml para volume, cm para comprimento). Assim, converter é
uma multiplicação, e converter entre grandezas diferentes é impossível.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.core.exceptions import RegraDeNegocio
from app.shared.quantidade import to_quantidade


class Grandeza(StrEnum):
    CONTAGEM = "contagem"
    MASSA = "massa"
    VOLUME = "volume"
    COMPRIMENTO = "comprimento"
    AREA = "area"


@dataclass(frozen=True)
class Unidade:
    codigo: str
    nome: str
    grandeza: Grandeza
    fator_canonico: Decimal
    casas_exibidas: int


UNIDADES: dict[str, Unidade] = {
    unidade.codigo: unidade
    for unidade in (
        Unidade("un", "Unidade", Grandeza.CONTAGEM, Decimal("1"), 0),
        Unidade("g", "Grama", Grandeza.MASSA, Decimal("1"), 1),
        Unidade("kg", "Quilo", Grandeza.MASSA, Decimal("1000"), 3),
        Unidade("ml", "Mililitro", Grandeza.VOLUME, Decimal("1"), 0),
        Unidade("l", "Litro", Grandeza.VOLUME, Decimal("1000"), 3),
        Unidade("cm", "Centímetro", Grandeza.COMPRIMENTO, Decimal("1"), 1),
        Unidade("m", "Metro", Grandeza.COMPRIMENTO, Decimal("100"), 2),
        Unidade("m2", "Metro quadrado", Grandeza.AREA, Decimal("1"), 2),
    )
}


def unidade(codigo: str) -> Unidade:
    try:
        return UNIDADES[codigo]
    except KeyError as erro:
        raise RegraDeNegocio(f"Unidade de medida desconhecida: {codigo}.") from erro


def converter(quantidade: Decimal, de: str, para: str) -> Decimal:
    """Converte entre unidades da mesma grandeza (kg → g, l → ml)."""
    origem, destino = unidade(de), unidade(para)
    if origem.grandeza != destino.grandeza:
        raise RegraDeNegocio(
            f"Não é possível converter {origem.nome} em {destino.nome}: "
            f"são grandezas diferentes."
        )
    if origem.codigo == destino.codigo:
        return to_quantidade(quantidade)
    canonico = Decimal(str(quantidade)) * origem.fator_canonico
    return to_quantidade(canonico / destino.fator_canonico)

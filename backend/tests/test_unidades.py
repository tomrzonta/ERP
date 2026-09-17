from decimal import Decimal

import pytest

from app.core.exceptions import RegraDeNegocio
from app.modules.produtos.unidades import UNIDADES, converter, unidade


def test_converte_dentro_da_mesma_grandeza():
    assert converter(Decimal("1.5"), "kg", "g") == Decimal("1500.0000")
    assert converter(Decimal("250"), "g", "kg") == Decimal("0.2500")
    assert converter(Decimal("2"), "l", "ml") == Decimal("2000.0000")
    assert converter(Decimal("1"), "m", "cm") == Decimal("100.0000")


def test_mesma_unidade_apenas_arredonda():
    assert converter(Decimal("0.15"), "kg", "kg") == Decimal("0.1500")


def test_recusa_conversao_entre_grandezas_diferentes():
    with pytest.raises(RegraDeNegocio):
        converter(Decimal("1"), "kg", "l")


def test_recusa_unidade_desconhecida():
    with pytest.raises(RegraDeNegocio):
        unidade("saco")


def test_catalogo_tem_fator_positivo_e_grandeza():
    for item in UNIDADES.values():
        assert item.fator_canonico > 0
        assert item.grandeza

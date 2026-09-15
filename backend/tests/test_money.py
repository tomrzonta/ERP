from decimal import Decimal

import pytest

from app.shared.money import margem_percentual, markup_percentual, to_money


def test_to_money_arredonda_meio_para_cima():
    assert to_money("10.005") == Decimal("10.01")


def test_to_money_recusa_float():
    with pytest.raises(TypeError):
        to_money(10.5)


def test_margem_e_markup():
    preco, custo = Decimal("100"), Decimal("60")
    assert margem_percentual(preco, custo) == Decimal("40.00")
    assert markup_percentual(preco, custo) == Decimal("66.67")


def test_margem_com_preco_zero():
    assert margem_percentual(Decimal("0"), Decimal("10")) is None

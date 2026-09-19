"""estorno em movimentacoes

Adiciona 'estorno' ao tipo de movimento de estoque (cancelamento de venda
já fechada, Fase 3 Bloco 3). O autogenerate não detecta mudança em CHECK
constraint (native_enum=False), por isso o drop/create manual.

Revision ID: 9cd65cef8fd7
Revises: 6f8ee0ed2796
Create Date: 2026-09-18 22:50:32.547443
"""
from collections.abc import Sequence

from alembic import op


revision: str = '9cd65cef8fd7'
down_revision: str | None = '6f8ee0ed2796'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ANTIGO = "entrada", "saida", "ajuste", "montagem", "reserva", "liberacao"
_NOVO = (*_ANTIGO, "estorno")


def upgrade() -> None:
    op.drop_constraint(op.f("ck_movimentacoes_estoque_tipo_movimento"), "movimentacoes_estoque", type_="check")
    op.create_check_constraint(
        "tipo_movimento",
        "movimentacoes_estoque",
        "tipo IN (" + ", ".join(f"'{valor}'" for valor in _NOVO) + ")",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_movimentacoes_estoque_tipo_movimento"), "movimentacoes_estoque", type_="check")
    op.create_check_constraint(
        "tipo_movimento",
        "movimentacoes_estoque",
        "tipo IN (" + ", ".join(f"'{valor}'" for valor in _ANTIGO) + ")",
    )

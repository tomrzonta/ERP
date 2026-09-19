"""unifica kit e montado

Kit e montado viraram um único tipo (kit): sempre tem saldo próprio,
alimentado pela montagem. Não há mais o kit "calculado" sem estoque.

Migração de dados:
1. Converte produtos com tipo='montado' para 'kit' (defensivo — nenhuma
   empresa tinha esse tipo até agora, mas protege dados reais).
2. Aperta o CHECK constraint de produtos.tipo para ('simples', 'kit').
3. Remove o recurso 'composto_montado' do plano Pro: a distinção deixou
   de existir, então não faz mais sentido gatilhar por ele.

Revision ID: f3a6c9e2b810
Revises: ad2d8b6451e5
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f3a6c9e2b810"
down_revision: str | None = "ad2d8b6451e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE produtos SET tipo = 'kit' WHERE tipo = 'montado'")

    op.drop_constraint(op.f("ck_produtos_tipo_produto"), "produtos", type_="check")
    # Nome "cru" (sem o prefixo ck_produtos_): a naming convention da
    # metadata monta o nome final sozinha, senão ele fica duplicado.
    op.create_check_constraint("tipo_produto", "produtos", "tipo IN ('simples', 'kit')")

    op.execute(
        """
        DELETE FROM plano_regras
        WHERE chave = 'composto_montado'
          AND plano_id IN (SELECT id FROM planos WHERE codigo = 'pro')
        """
    )


def downgrade() -> None:
    op.execute(
        """
        INSERT INTO plano_regras (plano_id, chave, tipo, valor)
        SELECT id, 'composto_montado', 'recurso', NULL FROM planos WHERE codigo = 'pro'
        ON CONFLICT DO NOTHING
        """
    )

    op.drop_constraint(op.f("ck_produtos_tipo_produto"), "produtos", type_="check")
    op.create_check_constraint(
        "tipo_produto", "produtos", "tipo IN ('simples', 'kit', 'montado')"
    )

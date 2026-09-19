"""remove producao (tempo de preparo, recursos produtivos, capacidade)

Decisão do desenvolvedor: atribuir tempo de máquina e de pessoa ficaria
confuso demais pro usuário final. Derruba as tabelas `producao_produtos` e
`recursos_produtivos` e o recurso de plano `capacidade_producao`. Custos
adicionais manuais (`custos_adicionais_produto`) continuam.

Revision ID: 7d2c41a9e5b3
Revises: 09708ecf13e7
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7d2c41a9e5b3"
down_revision: str | None = "09708ecf13e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("DELETE FROM plano_regras WHERE chave = 'capacidade_producao'"))
    op.drop_table("producao_produtos")
    op.drop_table("recursos_produtivos")


def downgrade() -> None:
    raise NotImplementedError("Remoção de produção é definitiva; não há como restaurar os dados.")

"""exportação de relatórios (recurso Pro)

Revision ID: b7e1a5c93d26
Revises: a4d6f8b2c015
"""
from collections.abc import Sequence

from alembic import op

revision: str = "b7e1a5c93d26"
down_revision: str | None = "a4d6f8b2c015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO plano_regras (plano_id, chave, tipo, valor)
        SELECT id, 'exportacao_relatorios', 'recurso', NULL FROM planos WHERE codigo = 'pro'
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM plano_regras WHERE chave = 'exportacao_relatorios'")

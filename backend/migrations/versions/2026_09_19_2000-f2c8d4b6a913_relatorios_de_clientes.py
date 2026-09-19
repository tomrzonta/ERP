"""relatórios de clientes (recurso Pro)

Revision ID: f2c8d4b6a913
Revises: e9b3c7a41f52
"""
from collections.abc import Sequence

from alembic import op

revision: str = "f2c8d4b6a913"
down_revision: str | None = "e9b3c7a41f52"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO plano_regras (plano_id, chave, tipo, valor)
        SELECT id, 'relatorios_clientes', 'recurso', NULL FROM planos WHERE codigo = 'pro'
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM plano_regras WHERE chave = 'relatorios_clientes'")

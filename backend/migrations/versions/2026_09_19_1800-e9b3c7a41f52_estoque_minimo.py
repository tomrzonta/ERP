"""estoque mínimo no produto

Revision ID: e9b3c7a41f52
Revises: d5a7e1c39b48
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e9b3c7a41f52"
down_revision: str | None = "d5a7e1c39b48"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("produtos", sa.Column("estoque_minimo", sa.Numeric(precision=18, scale=4), nullable=True))


def downgrade() -> None:
    op.drop_column("produtos", "estoque_minimo")

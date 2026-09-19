"""permissão de relatórios

Concede `relatorios.ver` ao papel padrão Gerente já existente nas empresas
(o Dono tem todas de forma implícita).

Revision ID: d5a7e1c39b48
Revises: c81f5a3d7e20
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d5a7e1c39b48"
down_revision: str | None = "c81f5a3d7e20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO papel_permissoes (papel_id, permissao)
            SELECT id, 'relatorios.ver' FROM papeis WHERE codigo_padrao = 'gerente'
            ON CONFLICT DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM papel_permissoes WHERE permissao = 'relatorios.ver'"))

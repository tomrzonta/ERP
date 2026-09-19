"""contas a pagar e a receber

Cria `contas_financeiras` e libera o recurso `contas_pagar_receber` no
plano Pro.

Revision ID: c81f5a3d7e20
Revises: 7d2c41a9e5b3
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c81f5a3d7e20"
down_revision: str | None = "7d2c41a9e5b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contas_financeiras",
        sa.Column("tipo", sa.Enum("pagar", "receber", name="tipo_conta", native_enum=False, create_constraint=True, length=20), nullable=False),
        sa.Column("status", sa.Enum("aberta", "paga", "cancelada", name="status_conta", native_enum=False, create_constraint=True, length=20), server_default="aberta", nullable=False),
        sa.Column("descricao", sa.String(length=255), nullable=False),
        sa.Column("contraparte", sa.String(length=120), nullable=True),
        sa.Column("valor", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("vencimento", sa.Date(), nullable=False),
        sa.Column("pago_em", sa.Date(), nullable=True),
        sa.Column("forma_pagamento", sa.Enum("dinheiro", "cartao", "pix", name="forma_pagamento_conta", native_enum=False, create_constraint=True, length=20), nullable=True),
        sa.Column("criado_por_usuario_id", sa.UUID(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("empresa_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["criado_por_usuario_id"], ["usuarios.id"], name=op.f("fk_contas_financeiras_criado_por_usuario_id_usuarios"), ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"], name=op.f("fk_contas_financeiras_empresa_id_empresas"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contas_financeiras")),
    )
    op.create_index(op.f("ix_contas_financeiras_empresa_id"), "contas_financeiras", ["empresa_id"])
    op.create_index(op.f("ix_contas_financeiras_tipo"), "contas_financeiras", ["tipo"])
    op.create_index(op.f("ix_contas_financeiras_status"), "contas_financeiras", ["status"])
    op.create_index(op.f("ix_contas_financeiras_vencimento"), "contas_financeiras", ["vencimento"])

    op.execute(
        """
        INSERT INTO plano_regras (plano_id, chave, tipo, valor)
        SELECT id, 'contas_pagar_receber', 'recurso', NULL FROM planos WHERE codigo = 'pro'
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM plano_regras WHERE chave = 'contas_pagar_receber'")
    op.drop_table("contas_financeiras")

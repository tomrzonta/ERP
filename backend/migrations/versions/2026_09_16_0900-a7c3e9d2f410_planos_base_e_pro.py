"""planos base e pro

Migração de dados: cadastra os planos e suas regras.
Valores de limites são provisórios (ver decisões em aberto no roadmap).

Revision ID: a7c3e9d2f410
Revises: 4b98eb171eb9
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a7c3e9d2f410"
down_revision: str | None = "4b98eb171eb9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PLANO_BASE_ID = uuid.UUID("5b0f8a52-3c1d-4e7a-9f21-0d6c2b8e4a11")
PLANO_PRO_ID = uuid.UUID("9e4d7c13-8a2b-4f60-b5e9-1c3a7d2f6b22")

RECURSOS_PRO = (
    "custos_adicionais",
    "composto_montado",
    "composto_aninhado",
    "papeis_editaveis",
    "margem_avancada",
    "alertas",
    "marketplaces",
    "dominio_proprio",
    "margem_por_canal",
    "cupons",
    "fidelidade",
    "segmentacao_clientes",
)

# chave: (Base, Pro). None = ilimitado
LIMITES = {
    "max_produtos_simples": (200, None),
    "max_compostos": (5, None),
    "max_usuarios": (2, None),
    "max_caixas_offline": (1, None),
    "max_produtos_vitrine": (30, None),
}


def upgrade() -> None:
    planos = sa.table(
        "planos",
        sa.column("id", sa.Uuid),
        sa.column("codigo", sa.String),
        sa.column("nome", sa.String),
    )
    regras = sa.table(
        "plano_regras",
        sa.column("plano_id", sa.Uuid),
        sa.column("chave", sa.String),
        sa.column("tipo", sa.String),
        sa.column("valor", sa.Integer),
    )

    op.bulk_insert(
        planos,
        [
            {"id": PLANO_BASE_ID, "codigo": "base", "nome": "Base"},
            {"id": PLANO_PRO_ID, "codigo": "pro", "nome": "Pro"},
        ],
    )

    linhas = []
    for chave, (valor_base, valor_pro) in LIMITES.items():
        linhas.append(
            {
                "plano_id": PLANO_BASE_ID,
                "chave": chave,
                "tipo": "limite",
                "valor": valor_base,
            }
        )
        linhas.append(
            {
                "plano_id": PLANO_PRO_ID,
                "chave": chave,
                "tipo": "limite",
                "valor": valor_pro,
            }
        )
    for chave in RECURSOS_PRO:
        linhas.append(
            {"plano_id": PLANO_PRO_ID, "chave": chave, "tipo": "recurso", "valor": None}
        )
    op.bulk_insert(regras, linhas)


def downgrade() -> None:
    op.execute(
        "DELETE FROM plano_regras WHERE plano_id IN "
        "(SELECT id FROM planos WHERE codigo IN ('base', 'pro'))"
    )
    op.execute("DELETE FROM planos WHERE codigo IN ('base', 'pro')")

"""unidades de medida e permissoes de produtos

Migração de dados:
1. Cadastra o catálogo de unidades (espelho de produtos/unidades.py).
2. Concede as permissões novas de produtos aos papéis padrão que já existem
   nas empresas criadas antes desta versão.

Revision ID: b2d5f8a1c934
Revises: e73bc431d3d1
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2d5f8a1c934"
down_revision: str | None = "e73bc431d3d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# codigo, nome, grandeza, fator_canonico, casas_exibidas
UNIDADES = (
    ("un", "Unidade", "contagem", "1", 0),
    ("g", "Grama", "massa", "1", 1),
    ("kg", "Quilo", "massa", "1000", 3),
    ("ml", "Mililitro", "volume", "1", 0),
    ("l", "Litro", "volume", "1000", 3),
    ("cm", "Centímetro", "comprimento", "1", 1),
    ("m", "Metro", "comprimento", "100", 2),
    ("m2", "Metro quadrado", "area", "1", 2),
)

# Permissões novas por papel padrão (ver acesso/papeis_padrao.py)
PERMISSOES_POR_PAPEL = {
    "gerente": ("produtos.ver", "produtos.editar", "produtos.ver_custo"),
    "caixa": ("produtos.ver",),
    "estoquista": ("produtos.ver", "produtos.editar", "produtos.ver_custo"),
}


def upgrade() -> None:
    unidades = sa.table(
        "unidades",
        sa.column("codigo", sa.String),
        sa.column("nome", sa.String),
        sa.column("grandeza", sa.String),
        sa.column("fator_canonico", sa.Numeric),
        sa.column("casas_exibidas", sa.Integer),
    )
    op.bulk_insert(
        unidades,
        [
            {
                "codigo": codigo,
                "nome": nome,
                "grandeza": grandeza,
                "fator_canonico": fator,
                "casas_exibidas": casas,
            }
            for codigo, nome, grandeza, fator, casas in UNIDADES
        ],
    )

    for codigo_padrao, permissoes in PERMISSOES_POR_PAPEL.items():
        for permissao in permissoes:
            op.execute(
                sa.text(
                    """
                    INSERT INTO papel_permissoes (papel_id, permissao)
                    SELECT id, :permissao FROM papeis WHERE codigo_padrao = :codigo_padrao
                    ON CONFLICT DO NOTHING
                    """
                ).bindparams(permissao=permissao, codigo_padrao=codigo_padrao)
            )


def downgrade() -> None:
    for codigo_padrao, permissoes in PERMISSOES_POR_PAPEL.items():
        op.execute(
            sa.text(
                """
                DELETE FROM papel_permissoes
                WHERE permissao = ANY(:permissoes)
                  AND papel_id IN (SELECT id FROM papeis WHERE codigo_padrao = :codigo_padrao)
                """
            ).bindparams(permissoes=list(permissoes), codigo_padrao=codigo_padrao)
        )
    op.execute("DELETE FROM unidades")

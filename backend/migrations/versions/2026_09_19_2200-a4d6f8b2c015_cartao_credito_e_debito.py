"""cartão de crédito e débito como formas de pagamento

Acrescenta `cartao_credito` e `cartao_debito` às formas de pagamento. O
valor antigo `cartao` continua válido (é o histórico das vendas já feitas,
que não dizia se foi crédito ou débito); a tela só oferece os dois novos.
Autogenerate não enxerga mudança em CHECK, então é manual — e os nomes vão
"crus", sem o prefixo da naming convention.

Revision ID: a4d6f8b2c015
Revises: f2c8d4b6a913
"""
from collections.abc import Sequence

from alembic import op

revision: str = "a4d6f8b2c015"
down_revision: str | None = "f2c8d4b6a913"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (tabela, coluna, nome cru da constraint, nome completo atual)
ALVOS = (
    ("pagamentos_venda", "forma", "forma_pagamento", "ck_pagamentos_venda_forma_pagamento"),
    (
        "lancamentos_caixa",
        "forma_pagamento",
        "forma_pagamento_lancamento",
        "ck_lancamentos_caixa_forma_pagamento_lancamento",
    ),
    (
        "contas_financeiras",
        "forma_pagamento",
        "forma_pagamento_conta",
        "ck_contas_financeiras_forma_pagamento_conta",
    ),
)

NOVAS = "'dinheiro', 'cartao', 'cartao_credito', 'cartao_debito', 'pix'"
ANTIGAS = "'dinheiro', 'cartao', 'pix'"


def _trocar(valores: str) -> None:
    for tabela, coluna, nome, nome_completo in ALVOS:
        op.drop_constraint(op.f(nome_completo), tabela, type_="check")
        op.create_check_constraint(nome, tabela, f"{coluna} IN ({valores})")


def upgrade() -> None:
    _trocar(NOVAS)


def downgrade() -> None:
    # Volta a `cartao` o que foi registrado como crédito ou débito.
    for tabela, coluna, _, _ in ALVOS:
        op.execute(
            f"UPDATE {tabela} SET {coluna} = 'cartao' "
            f"WHERE {coluna} IN ('cartao_credito', 'cartao_debito')"
        )
    _trocar(ANTIGAS)

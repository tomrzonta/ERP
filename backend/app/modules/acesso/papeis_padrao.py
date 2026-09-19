"""Papéis criados automaticamente em cada empresa nova.

O Dono tem todas as permissões de forma implícita, inclusive as que
forem criadas no futuro. Os demais recebem permissões explícitas.

Ao criar uma permissão nova que deva valer para um papel padrão,
inclua-a aqui E crie uma migração de dados concedendo-a aos papéis
já existentes com o mesmo codigo_padrao.
"""

from dataclasses import dataclass
from decimal import Decimal

DONO = "dono"


@dataclass(frozen=True)
class PapelPadrao:
    codigo: str
    nome: str
    descricao: str
    protegido: bool
    permissoes: frozenset[str]
    # Nulo = sem limite de desconto em vendas.
    limite_desconto_percentual: Decimal | None = None


PAPEIS_PADRAO: tuple[PapelPadrao, ...] = (
    PapelPadrao(
        codigo=DONO,
        nome="Dono",
        descricao="Acesso total à empresa",
        protegido=True,
        permissoes=frozenset(),  # todas, de forma implícita
    ),
    PapelPadrao(
        codigo="gerente",
        nome="Gerente",
        descricao="Gestão do dia a dia, sem assinatura e papéis",
        protegido=False,
        permissoes=frozenset(
            {
                "membros.ver",
                "membros.gerenciar",
                "empresa.editar",
                "assinatura.ver",
                "produtos.ver",
                "produtos.editar",
                "produtos.ver_custo",
                "estoque.ver",
                "estoque.movimentar",
                "estoque.ajustar",
                "clientes.ver",
                "clientes.editar",
                "vendas.ver",
                "vendas.registrar",
                "vendas.desconto_acima_limite",
                "vendas.cancelar",
                "financeiro.ver",
                "financeiro.operar",
                "relatorios.ver",
            }
        ),
    ),
    PapelPadrao(
        codigo="caixa",
        nome="Caixa",
        descricao="Vendas e caixa do dia",
        protegido=False,
        # Vê produtos, preços e saldo de estoque, mas não custo nem margem
        permissoes=frozenset(
            {
                "produtos.ver",
                "estoque.ver",
                "clientes.ver",
                "clientes.editar",
                "vendas.ver",
                "vendas.registrar",
                "financeiro.ver",
                "financeiro.operar",
            }
        ),
        limite_desconto_percentual=Decimal("10"),
    ),
    PapelPadrao(
        codigo="estoquista",
        nome="Estoquista",
        descricao="Produtos e movimentações de estoque",
        protegido=False,
        permissoes=frozenset(
            {
                "produtos.ver",
                "produtos.editar",
                "produtos.ver_custo",
                "estoque.ver",
                "estoque.movimentar",
                "estoque.ajustar",
            }
        ),
    ),
)

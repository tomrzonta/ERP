from app.core.permissions import Permissao

PERMISSOES = (
    Permissao("estoque.ver", "Ver saldo e movimentações de estoque"),
    Permissao("estoque.movimentar", "Registrar entradas, saídas e reservas de estoque"),
    Permissao("estoque.ajustar", "Ajustar o estoque a partir de uma contagem"),
)

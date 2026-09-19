from app.core.permissions import Permissao

PERMISSOES = (
    Permissao("vendas.ver", "Ver vendas e histórico"),
    Permissao("vendas.registrar", "Registrar vendas no PDV"),
    Permissao("vendas.desconto_acima_limite", "Aplicar desconto acima do limite do papel"),
    Permissao("vendas.cancelar", "Cancelar venda já fechada, com estorno de estoque"),
)

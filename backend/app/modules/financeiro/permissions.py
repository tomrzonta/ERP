from app.core.permissions import Permissao

PERMISSOES = (
    Permissao("financeiro.ver", "Ver caixa e lançamentos"),
    Permissao("financeiro.operar", "Abrir/fechar caixa e lançar entrada ou saída"),
)

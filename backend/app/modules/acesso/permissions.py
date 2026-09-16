from app.core.permissions import Permissao

PERMISSOES = (
    Permissao("membros.ver", "Ver os membros da empresa"),
    Permissao("membros.gerenciar", "Convidar, alterar papel e desativar membros"),
    Permissao("papeis.gerenciar", "Criar e editar papéis e suas permissões"),
)

from app.core.permissions import Permissao

PERMISSOES = (
    Permissao("produtos.ver", "Ver produtos, categorias e preços"),
    Permissao("produtos.editar", "Criar e editar produtos e categorias"),
    Permissao("produtos.ver_custo", "Ver custo e margem dos produtos"),
)

from app.core.permissions import Permissao

PERMISSOES = (
    Permissao("clientes.ver", "Ver clientes e histórico de compras"),
    Permissao("clientes.editar", "Cadastrar, editar, mesclar e anonimizar clientes"),
)

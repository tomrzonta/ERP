"""Catálogo de permissões do sistema.

Cada módulo declara as próprias permissões no seu permissions.py.
Este arquivo reúne todas e valida códigos. O banco guarda apenas
os códigos concedidos a cada papel.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache

FORMATO_CODIGO = re.compile(r"^[a-z_]+\.[a-z_]+$")


@dataclass(frozen=True)
class Permissao:
    codigo: str
    descricao: str


@lru_cache
def catalogo() -> dict[str, Permissao]:
    """Todas as permissões conhecidas, indexadas pelo código."""
    # Imports aqui dentro para evitar import circular com os módulos
    from app.modules.acesso.permissions import PERMISSOES as acesso
    from app.modules.assinaturas.permissions import PERMISSOES as assinaturas
    from app.modules.clientes.permissions import PERMISSOES as clientes
    from app.modules.empresas.permissions import PERMISSOES as empresas
    from app.modules.estoque.permissions import PERMISSOES as estoque
    from app.modules.financeiro.permissions import PERMISSOES as financeiro
    from app.modules.produtos.permissions import PERMISSOES as produtos
    from app.modules.relatorios.permissions import PERMISSOES as relatorios
    from app.modules.vendas.permissions import PERMISSOES as vendas

    resultado: dict[str, Permissao] = {}
    for permissao in (
        *acesso,
        *assinaturas,
        *clientes,
        *empresas,
        *estoque,
        *financeiro,
        *produtos,
        *relatorios,
        *vendas,
    ):
        if not FORMATO_CODIGO.match(permissao.codigo):
            raise RuntimeError(f"Código de permissão inválido: {permissao.codigo}")
        if permissao.codigo in resultado:
            raise RuntimeError(f"Permissão declarada duas vezes: {permissao.codigo}")
        resultado[permissao.codigo] = permissao
    return resultado


def validar_codigos(codigos: Iterable[str]) -> None:
    """Garante que todos os códigos existem no catálogo."""
    desconhecidos = sorted(set(codigos) - set(catalogo()))
    if desconhecidos:
        raise ValueError(f"Permissões desconhecidas: {', '.join(desconhecidos)}")

"""Regras de negócio de produtos, categorias e unidades alternativas."""

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import Conflito, RegraDeNegocio
from app.modules.assinaturas import service as assinaturas_service
from app.modules.assinaturas.regras import Limite
from app.modules.produtos import unidades as catalogo_unidades
from app.modules.produtos.models import (
    Categoria,
    Produto,
    ProdutoUnidade,
    StatusProduto,
    TipoProduto,
)
from app.modules.produtos.repository import CategoriaRepositorio, ProdutoRepositorio
from app.shared.quantidade import to_custo

LIMITE_POR_TIPO = {
    TipoProduto.SIMPLES: Limite.MAX_PRODUTOS_SIMPLES,
    TipoProduto.COMPOSTO: Limite.MAX_COMPOSTOS,
}


# --- categorias ---


def criar_categoria(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    nome: str,
    categoria_pai_id: uuid.UUID | None = None,
) -> Categoria:
    repo = CategoriaRepositorio(db, empresa_id)
    nome = nome.strip()
    if repo.nome_em_uso(nome):
        raise Conflito("Já existe uma categoria com esse nome.")
    if categoria_pai_id is not None:
        repo.obter_ou_erro(categoria_pai_id)
    return repo.adicionar(Categoria(nome=nome, categoria_pai_id=categoria_pai_id))


def listar_categorias(db: Session, empresa_id: uuid.UUID) -> list[Categoria]:
    return CategoriaRepositorio(db, empresa_id).listar(limite=200)


# --- produtos ---


def proximo_sku(repo: ProdutoRepositorio) -> str:
    """Sugere PRD-0001, PRD-0002... pulando os que já existem."""
    proximo = repo.contar() + 1
    while True:
        sku = f"PRD-{proximo:04d}"
        if not repo.sku_em_uso(sku):
            return sku
        proximo += 1


def criar_produto(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    nome: str,
    unidade_codigo: str,
    tipo: TipoProduto = TipoProduto.SIMPLES,
    sku: str | None = None,
    categoria_id: uuid.UUID | None = None,
    preco_venda: Decimal = Decimal("0"),
    custo: Decimal = Decimal("0"),
    vendavel: bool = True,
    insumo: bool = False,
    controla_estoque: bool = True,
    codigo_barras: str | None = None,
    descricao: str | None = None,
) -> Produto:
    if tipo is TipoProduto.COMPOSTO:
        raise RegraDeNegocio("Produtos compostos serão criados na etapa de composição.")

    repo = ProdutoRepositorio(db, empresa_id)

    # Unidade precisa existir no catálogo
    catalogo_unidades.unidade(unidade_codigo)

    if not vendavel and not insumo:
        raise RegraDeNegocio("O produto precisa ser vendável, insumo, ou os dois.")

    if categoria_id is not None:
        CategoriaRepositorio(db, empresa_id).obter_ou_erro(categoria_id)

    # Limite do plano por tipo de produto
    assinaturas_service.verificar_limite(
        db, empresa_id, LIMITE_POR_TIPO[tipo], repo.contar_por_tipo(tipo)
    )

    sku_final = (sku or "").strip().upper() or proximo_sku(repo)
    if repo.sku_em_uso(sku_final):
        raise Conflito(f"O SKU {sku_final} já está em uso.")

    return repo.adicionar(
        Produto(
            sku=sku_final,
            nome=nome.strip(),
            tipo=tipo,
            unidade_codigo=unidade_codigo,
            categoria_id=categoria_id,
            preco_venda=preco_venda,
            custo_medio=to_custo(custo),
            custo_ultima_compra=to_custo(custo) if custo else None,
            vendavel=vendavel,
            insumo=insumo,
            controla_estoque=controla_estoque,
            codigo_barras=(codigo_barras or "").strip() or None,
            descricao=(descricao or "").strip() or None,
        )
    )


def obter_produto(db: Session, empresa_id: uuid.UUID, produto_id: uuid.UUID) -> Produto:
    return ProdutoRepositorio(db, empresa_id).obter_ou_erro(produto_id)


def atualizar_produto(
    db: Session,
    empresa_id: uuid.UUID,
    produto_id: uuid.UUID,
    campos: dict,
) -> Produto:
    repo = ProdutoRepositorio(db, empresa_id)
    produto = repo.obter_ou_erro(produto_id)

    if produto.status is StatusProduto.CONGELADO:
        raise RegraDeNegocio(
            "Este produto está congelado pelo limite do plano e não pode ser editado."
        )

    if "sku" in campos and campos["sku"]:
        novo_sku = campos["sku"].strip().upper()
        if novo_sku != produto.sku and repo.sku_em_uso(novo_sku):
            raise Conflito(f"O SKU {novo_sku} já está em uso.")
        campos["sku"] = novo_sku

    if "unidade_codigo" in campos and campos["unidade_codigo"]:
        catalogo_unidades.unidade(campos["unidade_codigo"])

    if campos.get("categoria_id") is not None:
        CategoriaRepositorio(db, empresa_id).obter_ou_erro(campos["categoria_id"])

    for campo, valor in campos.items():
        setattr(produto, campo, valor)

    if not produto.vendavel and not produto.insumo:
        raise RegraDeNegocio("O produto precisa ser vendável, insumo, ou os dois.")

    db.flush()
    return produto


def margem_percentual(produto: Produto) -> Decimal | None:
    """Margem sobre o preço de venda, usando o custo médio."""
    preco = Decimal(produto.preco_venda or 0)
    if preco == 0:
        return None
    custo = Decimal(produto.custo_medio or 0)
    return ((preco - custo) / preco * 100).quantize(Decimal("0.01"))


# --- unidades alternativas ---


def adicionar_unidade(
    db: Session,
    empresa_id: uuid.UUID,
    produto_id: uuid.UUID,
    *,
    nome: str,
    fator: Decimal,
    usa_na_compra: bool = True,
    usa_na_venda: bool = True,
) -> ProdutoUnidade:
    """Ex.: rolo = 1000 (g), caixa = 12 (un), fatia = 0,125 (un)."""
    repo = ProdutoRepositorio(db, empresa_id)
    repo.obter_ou_erro(produto_id)

    if fator <= 0:
        raise RegraDeNegocio("O fator da unidade precisa ser maior que zero.")
    if not usa_na_compra and not usa_na_venda:
        raise RegraDeNegocio("A unidade precisa valer para compra, para venda, ou para as duas.")

    nome = nome.strip()
    if any(u.nome.lower() == nome.lower() for u in repo.unidades_alternativas(produto_id)):
        raise Conflito(f"O produto já tem uma unidade chamada {nome}.")

    unidade = ProdutoUnidade(
        produto_id=produto_id,
        nome=nome,
        fator=fator,
        usa_na_compra=usa_na_compra,
        usa_na_venda=usa_na_venda,
    )
    db.add(unidade)
    db.flush()
    return unidade


def listar_unidades(
    db: Session, empresa_id: uuid.UUID, produto_id: uuid.UUID
) -> list[ProdutoUnidade]:
    repo = ProdutoRepositorio(db, empresa_id)
    repo.obter_ou_erro(produto_id)
    return repo.unidades_alternativas(produto_id)

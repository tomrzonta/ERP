"""Rotas de produtos, categorias e unidades."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencias import Contexto, obter_contexto, requer_permissao
from app.modules.produtos import service
from app.modules.produtos import unidades as catalogo_unidades
from app.modules.produtos.models import Produto, TipoProduto
from app.modules.produtos.schemas import (
    CategoriaEntrada,
    CategoriaSaida,
    ProdutoAtualizacao,
    ProdutoEntrada,
    ProdutoSaida,
    UnidadeAlternativaEntrada,
    UnidadeAlternativaSaida,
    UnidadeSaida,
)

router = APIRouter(tags=["produtos"])

PERMISSAO_CUSTO = "produtos.ver_custo"


def _saida(produto: Produto, contexto: Contexto) -> ProdutoSaida:
    mostra_custo = PERMISSAO_CUSTO in contexto.permissoes
    return ProdutoSaida(
        id=produto.id,
        sku=produto.sku,
        nome=produto.nome,
        tipo=produto.tipo,
        status=produto.status,
        unidade_codigo=produto.unidade_codigo,
        categoria_id=produto.categoria_id,
        vendavel=produto.vendavel,
        insumo=produto.insumo,
        controla_estoque=produto.controla_estoque,
        preco_venda=produto.preco_venda,
        codigo_barras=produto.codigo_barras,
        descricao=produto.descricao,
        publicado_na_vitrine=produto.publicado_na_vitrine,
        custo_medio=produto.custo_medio if mostra_custo else None,
        margem_percentual=service.margem_percentual(produto) if mostra_custo else None,
    )


@router.get("/unidades", response_model=list[UnidadeSaida])
def listar_unidades_de_medida(_: Contexto = Depends(obter_contexto)):
    return [
        UnidadeSaida(
            codigo=u.codigo, nome=u.nome, grandeza=u.grandeza, casas_exibidas=u.casas_exibidas
        )
        for u in catalogo_unidades.UNIDADES.values()
    ]


@router.get("/categorias", response_model=list[CategoriaSaida])
def listar_categorias(
    contexto: Contexto = Depends(requer_permissao("produtos.ver")),
    db: Session = Depends(get_db),
):
    return service.listar_categorias(db, contexto.empresa_id)


@router.post("/categorias", response_model=CategoriaSaida, status_code=status.HTTP_201_CREATED)
def criar_categoria(
    dados: CategoriaEntrada,
    contexto: Contexto = Depends(requer_permissao("produtos.editar")),
    db: Session = Depends(get_db),
):
    categoria = service.criar_categoria(
        db, contexto.empresa_id, nome=dados.nome, categoria_pai_id=dados.categoria_pai_id
    )
    db.commit()
    return categoria


@router.get("/produtos", response_model=list[ProdutoSaida])
def listar_produtos(
    termo: str | None = Query(default=None, max_length=60),
    tipo: TipoProduto | None = None,
    apenas_vendaveis: bool = False,
    limite: int = Query(default=50, ge=1, le=200),
    deslocamento: int = Query(default=0, ge=0),
    contexto: Contexto = Depends(requer_permissao("produtos.ver")),
    db: Session = Depends(get_db),
):
    from app.modules.produtos.repository import ProdutoRepositorio

    produtos = ProdutoRepositorio(db, contexto.empresa_id).buscar(
        termo=termo,
        tipo=tipo,
        apenas_vendaveis=apenas_vendaveis,
        limite=limite,
        deslocamento=deslocamento,
    )
    return [_saida(produto, contexto) for produto in produtos]


@router.post("/produtos", response_model=ProdutoSaida, status_code=status.HTTP_201_CREATED)
def criar_produto(
    dados: ProdutoEntrada,
    contexto: Contexto = Depends(requer_permissao("produtos.editar")),
    db: Session = Depends(get_db),
):
    produto = service.criar_produto(db, contexto.empresa_id, **dados.model_dump())
    db.commit()
    return _saida(produto, contexto)


@router.get("/produtos/{produto_id}", response_model=ProdutoSaida)
def obter_produto(
    produto_id: uuid.UUID,
    contexto: Contexto = Depends(requer_permissao("produtos.ver")),
    db: Session = Depends(get_db),
):
    produto = service.obter_produto(db, contexto.empresa_id, produto_id)
    return _saida(produto, contexto)


@router.patch("/produtos/{produto_id}", response_model=ProdutoSaida)
def atualizar_produto(
    produto_id: uuid.UUID,
    dados: ProdutoAtualizacao,
    contexto: Contexto = Depends(requer_permissao("produtos.editar")),
    db: Session = Depends(get_db),
):
    produto = service.atualizar_produto(
        db, contexto.empresa_id, produto_id, dados.model_dump(exclude_unset=True)
    )
    db.commit()
    return _saida(produto, contexto)


@router.get("/produtos/{produto_id}/unidades", response_model=list[UnidadeAlternativaSaida])
def listar_unidades_do_produto(
    produto_id: uuid.UUID,
    contexto: Contexto = Depends(requer_permissao("produtos.ver")),
    db: Session = Depends(get_db),
):
    return service.listar_unidades(db, contexto.empresa_id, produto_id)


@router.post(
    "/produtos/{produto_id}/unidades",
    response_model=UnidadeAlternativaSaida,
    status_code=status.HTTP_201_CREATED,
)
def adicionar_unidade_do_produto(
    produto_id: uuid.UUID,
    dados: UnidadeAlternativaEntrada,
    contexto: Contexto = Depends(requer_permissao("produtos.editar")),
    db: Session = Depends(get_db),
):
    unidade = service.adicionar_unidade(
        db, contexto.empresa_id, produto_id, **dados.model_dump()
    )
    db.commit()
    return unidade

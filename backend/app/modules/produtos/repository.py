"""Consultas do módulo de produtos."""

import uuid
from decimal import Decimal

from sqlalchemy import Select, exists, func, or_, select

from app.modules.produtos.models import (
    Categoria,
    CustoAdicionalProduto,
    Produto,
    ProdutoUnidade,
    TipoProduto,
)
from app.shared.repository import RepositorioDaEmpresa


class CategoriaRepositorio(RepositorioDaEmpresa[Categoria]):
    modelo = Categoria
    mensagem_nao_encontrado = "Categoria não encontrada."

    def nome_em_uso(self, nome: str) -> bool:
        consulta = self.selecionar().where(func.lower(Categoria.nome) == nome.lower())
        return self.db.scalar(select(exists(consulta))) or False


class ProdutoRepositorio(RepositorioDaEmpresa[Produto]):
    modelo = Produto
    mensagem_nao_encontrado = "Produto não encontrado."

    def sku_em_uso(self, sku: str) -> bool:
        consulta = self.selecionar().where(Produto.sku == sku)
        return self.db.scalar(select(exists(consulta))) or False

    def contar_por_tipo(self, tipo: TipoProduto) -> int:
        consulta = (
            select(func.count())
            .select_from(Produto)
            .where(Produto.empresa_id == self.empresa_id, Produto.tipo == tipo)
        )
        return self.db.scalar(consulta) or 0

    def buscar(
        self,
        *,
        termo: str | None = None,
        tipo: TipoProduto | None = None,
        apenas_vendaveis: bool = False,
        apenas_insumos: bool = False,
        apenas_com_controle_de_estoque: bool = False,
        limite: int = 50,
        deslocamento: int = 0,
    ) -> list[Produto]:
        consulta: Select[tuple[Produto]] = self.selecionar()
        if termo:
            like = f"%{termo.strip()}%"
            consulta = consulta.where(
                or_(
                    Produto.nome.ilike(like),
                    Produto.sku.ilike(like),
                    Produto.codigo_barras.ilike(like),
                )
            )
        if tipo is not None:
            consulta = consulta.where(Produto.tipo == tipo)
        if apenas_vendaveis:
            consulta = consulta.where(Produto.vendavel.is_(True))
        if apenas_insumos:
            consulta = consulta.where(Produto.insumo.is_(True))
        if apenas_com_controle_de_estoque:
            consulta = consulta.where(Produto.controla_estoque.is_(True))
        consulta = consulta.order_by(Produto.nome).limit(limite).offset(deslocamento)
        return list(self.db.scalars(consulta))

    def unidades_alternativas(self, produto_id: uuid.UUID) -> list[ProdutoUnidade]:
        consulta = (
            select(ProdutoUnidade)
            .where(ProdutoUnidade.produto_id == produto_id)
            .order_by(ProdutoUnidade.nome)
        )
        return list(self.db.scalars(consulta))

    def unidade_alternativa(
        self, produto_id: uuid.UUID, unidade_id: uuid.UUID
    ) -> ProdutoUnidade | None:
        consulta = select(ProdutoUnidade).where(
            ProdutoUnidade.produto_id == produto_id, ProdutoUnidade.id == unidade_id
        )
        return self.db.scalar(consulta)

    def custos_adicionais(self, produto_id: uuid.UUID) -> list[CustoAdicionalProduto]:
        consulta = (
            select(CustoAdicionalProduto)
            .where(CustoAdicionalProduto.produto_id == produto_id)
            .order_by(CustoAdicionalProduto.nome)
        )
        return list(self.db.scalars(consulta))

    def custo_adicional(
        self, produto_id: uuid.UUID, custo_id: uuid.UUID
    ) -> CustoAdicionalProduto | None:
        consulta = select(CustoAdicionalProduto).where(
            CustoAdicionalProduto.produto_id == produto_id, CustoAdicionalProduto.id == custo_id
        )
        return self.db.scalar(consulta)

    def soma_custos_adicionais(self, produto_id: uuid.UUID) -> Decimal:
        consulta = select(func.coalesce(func.sum(CustoAdicionalProduto.valor), 0)).where(
            CustoAdicionalProduto.produto_id == produto_id
        )
        return Decimal(self.db.scalar(consulta) or 0)

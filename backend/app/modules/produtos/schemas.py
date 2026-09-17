"""Formatos de entrada e saída da API de produtos."""

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.produtos.models import StatusProduto, TipoProduto


class UnidadeSaida(BaseModel):
    codigo: str
    nome: str
    grandeza: str
    casas_exibidas: int


class CategoriaEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=60)
    categoria_pai_id: uuid.UUID | None = None


class CategoriaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    categoria_pai_id: uuid.UUID | None


class ProdutoEntrada(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    unidade_codigo: str = Field(min_length=1, max_length=10)
    sku: str | None = Field(default=None, max_length=40)
    categoria_id: uuid.UUID | None = None
    preco_venda: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    custo: Decimal = Field(default=Decimal("0"), ge=0)
    vendavel: bool = True
    insumo: bool = False
    controla_estoque: bool = True
    codigo_barras: str | None = Field(default=None, max_length=20)
    descricao: str | None = Field(default=None, max_length=500)


class ProdutoAtualizacao(BaseModel):
    """Só os campos enviados são alterados."""

    nome: str | None = Field(default=None, min_length=2, max_length=120)
    sku: str | None = Field(default=None, max_length=40)
    unidade_codigo: str | None = Field(default=None, max_length=10)
    categoria_id: uuid.UUID | None = None
    preco_venda: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    vendavel: bool | None = None
    insumo: bool | None = None
    controla_estoque: bool | None = None
    codigo_barras: str | None = Field(default=None, max_length=20)
    descricao: str | None = Field(default=None, max_length=500)
    status: StatusProduto | None = None
    publicado_na_vitrine: bool | None = None
    descricao_publica: str | None = Field(default=None, max_length=2000)
    ncm: str | None = Field(default=None, max_length=8)
    cest: str | None = Field(default=None, max_length=7)
    origem: str | None = Field(default=None, max_length=1)


class UnidadeAlternativaEntrada(BaseModel):
    nome: str = Field(min_length=1, max_length=30)
    fator: Decimal = Field(gt=0)
    usa_na_compra: bool = True
    usa_na_venda: bool = True


class UnidadeAlternativaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    fator: Decimal
    usa_na_compra: bool
    usa_na_venda: bool


class ProdutoSaida(BaseModel):
    """Custo e margem só aparecem para quem tem produtos.ver_custo."""

    id: uuid.UUID
    sku: str
    nome: str
    tipo: TipoProduto
    status: StatusProduto
    unidade_codigo: str
    categoria_id: uuid.UUID | None
    vendavel: bool
    insumo: bool
    controla_estoque: bool
    preco_venda: Decimal
    codigo_barras: str | None
    descricao: str | None
    publicado_na_vitrine: bool
    custo_medio: Decimal | None = None
    margem_percentual: Decimal | None = None

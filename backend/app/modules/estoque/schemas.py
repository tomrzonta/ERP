"""Formatos de entrada e saída da API de estoque."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.estoque.models import TipoMovimento


class EntradaEntrada(BaseModel):
    id: uuid.UUID | None = None
    quantidade: Decimal = Field(gt=0)
    custo_unitario: Decimal = Field(ge=0)
    unidade_id: uuid.UUID | None = None
    ocorrido_em: datetime | None = None
    origem: str | None = Field(default=None, max_length=60)


class SaidaEntrada(BaseModel):
    id: uuid.UUID | None = None
    quantidade: Decimal = Field(gt=0)
    ocorrido_em: datetime | None = None
    origem: str | None = Field(default=None, max_length=60)


class AjusteEntrada(BaseModel):
    id: uuid.UUID | None = None
    quantidade_contada: Decimal = Field(ge=0)
    ocorrido_em: datetime | None = None
    origem: str | None = Field(default=None, max_length=60)


class ReservaEntrada(BaseModel):
    id: uuid.UUID | None = None
    quantidade: Decimal = Field(gt=0)
    origem: str | None = Field(default=None, max_length=60)


class MovimentoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    produto_id: uuid.UUID
    tipo: TipoMovimento
    quantidade: Decimal
    custo_unitario: Decimal | None
    origem: str | None
    ocorrido_em: datetime
    registrado_em: datetime


class SaldoSaida(BaseModel):
    produto_id: uuid.UUID
    fisico: Decimal
    reservado: Decimal
    disponivel: Decimal


class SaldoComProdutoSaida(BaseModel):
    produto_id: uuid.UUID
    nome: str
    sku: str
    unidade_codigo: str
    fisico: Decimal
    reservado: Decimal
    disponivel: Decimal


class AlertaEstoqueSaida(BaseModel):
    produto_id: uuid.UUID
    nome: str
    sku: str
    unidade_codigo: str
    tipo: str
    fisico: Decimal
    disponivel: Decimal
    estoque_minimo: Decimal | None

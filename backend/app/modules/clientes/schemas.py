"""Formatos de entrada e saída da API de clientes."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.clientes.models import OrigemCliente


class ClienteEntrada(BaseModel):
    id: uuid.UUID | None = None
    nome: str = Field(min_length=2, max_length=120)
    telefone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    cpf: str | None = Field(default=None, max_length=14)
    data_nascimento: date | None = None
    endereco: str | None = Field(default=None, max_length=500)
    consentimento_marketing: bool = False
    origem: OrigemCliente = OrigemCliente.BALCAO


class ClienteAtualizacao(BaseModel):
    """Só os campos enviados são alterados."""

    nome: str | None = Field(default=None, min_length=2, max_length=120)
    telefone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    cpf: str | None = Field(default=None, max_length=14)
    data_nascimento: date | None = None
    endereco: str | None = Field(default=None, max_length=500)
    consentimento_marketing: bool | None = None
    origem: OrigemCliente | None = None


class ClienteSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    telefone: str | None
    email: str | None
    cpf: str | None
    data_nascimento: date | None
    endereco: str | None
    consentimento_marketing: bool
    origem: OrigemCliente
    anonimizado_em: datetime | None


class MesclarClientesEntrada(BaseModel):
    duplicado_id: uuid.UUID


class MetricasClienteSaida(BaseModel):
    quantidade_compras: int
    valor_total: Decimal
    ticket_medio: Decimal | None
    primeira_compra: datetime | None
    ultima_compra: datetime | None


class CompraExportada(BaseModel):
    numero: str
    ocorrido_em: datetime
    total: Decimal


class ExportacaoClienteSaida(BaseModel):
    id: uuid.UUID
    nome: str
    telefone: str | None
    email: str | None
    cpf: str | None
    data_nascimento: date | None
    endereco: str | None
    consentimento_marketing: bool
    consentimento_em: datetime | None
    origem: OrigemCliente
    compras: list[CompraExportada]

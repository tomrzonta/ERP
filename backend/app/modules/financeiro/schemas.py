"""Formatos de entrada e saída da API do caixa."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.financeiro.models import (
    OrigemLancamento,
    StatusCaixa,
    StatusConta,
    TipoConta,
    TipoLancamento,
)
from app.modules.vendas.models import FormaPagamento


class AbrirCaixaEntrada(BaseModel):
    valor_inicial: Decimal = Field(ge=0, decimal_places=2)
    observacao: str | None = Field(default=None, max_length=500)


class FecharCaixaEntrada(BaseModel):
    valor_contado: Decimal = Field(ge=0, decimal_places=2)
    observacao: str | None = Field(default=None, max_length=500)


class LancamentoEntrada(BaseModel):
    tipo: TipoLancamento
    valor: Decimal = Field(gt=0, decimal_places=2)
    forma_pagamento: FormaPagamento
    descricao: str | None = Field(default=None, max_length=255)


class SincronizarLancamentoEntrada(BaseModel):
    id: uuid.UUID
    tipo: TipoLancamento
    valor: Decimal = Field(gt=0, decimal_places=2)
    forma_pagamento: FormaPagamento
    descricao: str | None = Field(default=None, max_length=255)
    ocorrido_em: datetime


class LancamentoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tipo: TipoLancamento
    origem: OrigemLancamento
    forma_pagamento: FormaPagamento
    valor: Decimal
    descricao: str | None
    venda_id: uuid.UUID | None
    ocorrido_em: datetime


class ResumoCaixaSaida(BaseModel):
    total_entradas: Decimal
    total_saidas: Decimal
    saldo_esperado_dinheiro: Decimal
    diferenca: Decimal | None


class CaixaSaida(BaseModel):
    id: uuid.UUID
    status: StatusCaixa
    valor_inicial: Decimal
    valor_contado: Decimal | None
    observacao: str | None
    aberto_por_usuario_id: uuid.UUID
    aberto_por_nome: str | None
    fechado_por_usuario_id: uuid.UUID | None
    fechado_por_nome: str | None
    aberto_em: datetime
    fechado_em: datetime | None
    resumo: ResumoCaixaSaida
    lancamentos: list[LancamentoSaida]


class ContaEntrada(BaseModel):
    tipo: TipoConta
    descricao: str = Field(min_length=1, max_length=255)
    contraparte: str | None = Field(default=None, max_length=120)
    valor: Decimal = Field(gt=0, decimal_places=2)
    vencimento: date


class BaixaContaEntrada(BaseModel):
    pago_em: date | None = None
    forma_pagamento: FormaPagamento | None = None


class ContaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tipo: TipoConta
    status: StatusConta
    descricao: str
    contraparte: str | None
    valor: Decimal
    vencimento: date
    pago_em: date | None
    forma_pagamento: FormaPagamento | None
    vencida: bool = False


class DiaProjetadoSaida(BaseModel):
    data: date
    a_receber: Decimal
    a_pagar: Decimal
    saldo_acumulado: Decimal


class FluxoProjetadoSaida(BaseModel):
    atrasadas_a_receber: Decimal
    atrasadas_a_pagar: Decimal
    dias: list[DiaProjetadoSaida]

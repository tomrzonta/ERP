"""Formatos de entrada e saída da API de vendas."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.clientes.schemas import ClienteEntrada
from app.modules.vendas.models import CanalVenda, FormaPagamento, StatusVenda


class AbrirVendaEntrada(BaseModel):
    id: uuid.UUID | None = None
    cliente_id: uuid.UUID | None = None
    # Cadastra o cliente e já vincula na mesma requisição, sem precisar
    # passar por /clientes antes. Ignorado se `cliente_id` for enviado.
    cliente_novo: ClienteEntrada | None = None
    ocorrido_em: datetime | None = None


class AtualizarClienteEntrada(BaseModel):
    cliente_id: uuid.UUID | None = None
    cliente_novo: ClienteEntrada | None = None


class ItemVendaEntrada(BaseModel):
    produto_id: uuid.UUID
    quantidade: Decimal = Field(gt=0)
    unidade_id: uuid.UUID | None = None
    desconto_percentual: Decimal = Field(default=Decimal("0"), ge=0, le=100)


class PagamentoEntrada(BaseModel):
    forma: FormaPagamento
    valor: Decimal = Field(gt=0, decimal_places=2)


class FecharVendaEntrada(BaseModel):
    pagamentos: list[PagamentoEntrada] = Field(min_length=1)


class ItemVendaOfflineEntrada(BaseModel):
    """Igual ao item normal, mas o preço vem do dispositivo (o que estava
    na cópia local no momento da venda), não do catálogo atual — o caixa
    pode ter ficado offline depois de um reajuste de preço."""

    produto_id: uuid.UUID
    quantidade: Decimal = Field(gt=0)
    unidade_id: uuid.UUID | None = None
    preco_tabela: Decimal = Field(ge=0, decimal_places=2)
    desconto_percentual: Decimal = Field(default=Decimal("0"), ge=0, le=100)


class SincronizarVendaEntrada(BaseModel):
    """Uma venda feita offline, enviada já completa (itens e pagamento) ao
    reconectar. `id` é obrigatório: é o que garante que reenviar depois de
    uma falha de rede não duplica a venda."""

    id: uuid.UUID
    cliente_id: uuid.UUID | None = None
    cliente_novo: ClienteEntrada | None = None
    itens: list[ItemVendaOfflineEntrada] = Field(min_length=1)
    pagamentos: list[PagamentoEntrada] = Field(min_length=1)
    ocorrido_em: datetime


class ItemVendaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    produto_id: uuid.UUID
    quantidade: Decimal
    preco_tabela: Decimal
    desconto: Decimal
    preco_final: Decimal
    custo_unitario: Decimal | None


class PagamentoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    forma: FormaPagamento
    valor: Decimal


class VendaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    numero: str
    cliente_id: uuid.UUID | None
    vendedor_usuario_id: uuid.UUID
    canal: CanalVenda
    status: StatusVenda
    subtotal: Decimal
    desconto_total: Decimal
    total: Decimal
    ocorrido_em: datetime
    fechado_em: datetime | None
    cancelado_em: datetime | None
    itens: list[ItemVendaSaida]
    pagamentos: list[PagamentoSaida]

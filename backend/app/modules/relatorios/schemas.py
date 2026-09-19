"""Formatos de saída dos relatórios."""

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.modules.vendas.models import FormaPagamento


class DiaVendasSaida(BaseModel):
    data: date
    quantidade: int
    faturamento: Decimal


class ProdutoVendidoSaida(BaseModel):
    produto_id: uuid.UUID
    nome: str
    quantidade: Decimal
    unidade_codigo: str
    receita: Decimal


class FormaPagamentoSaida(BaseModel):
    forma: FormaPagamento
    valor: Decimal


class ResumoSaida(BaseModel):
    inicio: date
    fim: date
    quantidade_vendas: int
    faturamento: Decimal
    ticket_medio: Decimal | None
    descontos: Decimal
    cancelamentos: int
    # Só vêm preenchidos pra quem tem `produtos.ver_custo`.
    lucro_bruto: Decimal | None
    margem_percentual: Decimal | None
    por_dia: list[DiaVendasSaida]
    mais_vendidos: list[ProdutoVendidoSaida]
    por_forma_pagamento: list[FormaPagamentoSaida]


class ClienteDoPeriodoSaida(BaseModel):
    cliente_id: uuid.UUID
    nome: str
    compras: int
    valor: Decimal


class ResumoClientesSaida(BaseModel):
    inicio: date
    fim: date
    clientes_que_compraram: int
    novos: int
    recorrentes: int
    compras_de_clientes: int
    valor_de_clientes: Decimal
    ticket_medio: Decimal | None
    compras_por_cliente: Decimal | None
    vendas_sem_cliente: int
    valor_sem_cliente: Decimal
    melhores: list[ClienteDoPeriodoSaida]


class InsumoConsumidoSaida(BaseModel):
    produto_id: uuid.UUID
    nome: str
    unidade_codigo: str
    consumido_em_montagens: Decimal
    baixado_por_ajuste: Decimal
    # Só pra quem tem `produtos.ver_custo`.
    custo_das_montagens: Decimal | None
    custo_dos_ajustes: Decimal | None
    custo_total: Decimal | None


class ResumoInsumosSaida(BaseModel):
    inicio: date
    fim: date
    custo_total: Decimal | None
    custo_dos_ajustes: Decimal | None
    insumos: list[InsumoConsumidoSaida]


class ProdutoComDescontoSaida(BaseModel):
    produto_id: uuid.UUID
    nome: str
    desconto: Decimal
    percentual: Decimal


class ResumoDescontosSaida(BaseModel):
    inicio: date
    fim: date
    receita_de_tabela: Decimal
    descontos: Decimal
    receita_final: Decimal
    percentual_de_desconto: Decimal | None
    itens_com_desconto: int
    vendas_com_desconto: int
    # Só pra quem tem `produtos.ver_custo`.
    lucro_sem_desconto: Decimal | None
    lucro_com_desconto: Decimal | None
    # Que parte do lucro possível foi cedida em desconto (em %).
    lucro_cedido_percentual: Decimal | None
    produtos: list[ProdutoComDescontoSaida]

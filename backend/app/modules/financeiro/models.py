"""Caixa do dia: sessão de caixa e lançamentos (Fase 5, seção 4.1 do
ROADMAP — "Financeiro: caixa do dia, entradas e saídas", plano Base).

Uma sessão de caixa abre com um valor inicial e fecha com o valor contado
(conferência). Abrir caixa não é obrigatório pra vender: quando existe um
caixa aberto, cada venda fechada vira um lançamento automático nele; sem
caixa aberto, a venda segue normal, só não gera lançamento nenhum.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.vendas.models import FormaPagamento
from app.shared.models import Base, EmpresaMixin, UUIDMixin


class StatusCaixa(StrEnum):
    ABERTO = "aberto"
    FECHADO = "fechado"


class TipoLancamento(StrEnum):
    ENTRADA = "entrada"
    SAIDA = "saida"


class OrigemLancamento(StrEnum):
    VENDA = "venda"
    MANUAL = "manual"


class TipoConta(StrEnum):
    PAGAR = "pagar"
    RECEBER = "receber"


class StatusConta(StrEnum):
    ABERTA = "aberta"
    PAGA = "paga"
    CANCELADA = "cancelada"


def _enum_curto(tipo: type[StrEnum], nome: str) -> Enum:
    return Enum(
        tipo,
        name=nome,
        native_enum=False,
        create_constraint=True,
        length=20,
        values_callable=lambda enum: [item.value for item in enum],
    )


class CaixaSessao(UUIDMixin, EmpresaMixin, Base):
    """Uma sessão de caixa: abre, acumula lançamentos, fecha. `id` pode vir
    do cliente (sincronização offline), igual ao padrão de sempre."""

    __tablename__ = "caixas_sessao"
    __table_args__ = (UniqueConstraint("empresa_id", "id"),)

    aberto_por_usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT")
    )
    fechado_por_usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT")
    )
    status: Mapped[StatusCaixa] = mapped_column(
        _enum_curto(StatusCaixa, "status_caixa"),
        default=StatusCaixa.ABERTO,
        server_default=StatusCaixa.ABERTO.value,
        index=True,
    )
    valor_inicial: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    # Contagem física informada no fechamento — nulo enquanto aberto.
    valor_contado: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    observacao: Mapped[str | None] = mapped_column(String(500))
    aberto_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    fechado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LancamentoCaixa(UUIDMixin, Base):
    """Uma entrada ou saída dentro de um caixa. Sem `empresa_id` própria —
    escopado pela sessão, igual `ProdutoUnidade`."""

    __tablename__ = "lancamentos_caixa"

    caixa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("caixas_sessao.id", ondelete="CASCADE"), index=True
    )
    tipo: Mapped[TipoLancamento] = mapped_column(_enum_curto(TipoLancamento, "tipo_lancamento"))
    origem: Mapped[OrigemLancamento] = mapped_column(
        _enum_curto(OrigemLancamento, "origem_lancamento")
    )
    forma_pagamento: Mapped[FormaPagamento] = mapped_column(
        _enum_curto(FormaPagamento, "forma_pagamento_lancamento")
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    descricao: Mapped[str | None] = mapped_column(String(255))
    # Preenchido só pra lançamento de origem "venda".
    venda_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendas.id", ondelete="RESTRICT")
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT")
    )
    ocorrido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registrado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ContaFinanceira(UUIDMixin, EmpresaMixin, Base):
    """Conta a pagar ou a receber (Pro). Independe do caixa do dia: dar baixa
    numa conta não gera lançamento de caixa. "Vencida" não é um status —
    é uma conta aberta cujo vencimento já passou (derivado na leitura)."""

    __tablename__ = "contas_financeiras"

    tipo: Mapped[TipoConta] = mapped_column(_enum_curto(TipoConta, "tipo_conta"), index=True)
    status: Mapped[StatusConta] = mapped_column(
        _enum_curto(StatusConta, "status_conta"),
        default=StatusConta.ABERTA,
        server_default=StatusConta.ABERTA.value,
        index=True,
    )
    descricao: Mapped[str] = mapped_column(String(255))
    # Fornecedor (a pagar) ou devedor (a receber), texto livre.
    contraparte: Mapped[str | None] = mapped_column(String(120))
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    vencimento: Mapped[date] = mapped_column(Date, index=True)
    pago_em: Mapped[date | None] = mapped_column(Date)
    forma_pagamento: Mapped[FormaPagamento | None] = mapped_column(
        _enum_curto(FormaPagamento, "forma_pagamento_conta")
    )
    criado_por_usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT")
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

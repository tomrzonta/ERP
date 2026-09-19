"""Movimentações de estoque e o saldo (cache) por produto."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models import Base, EmpresaMixin, TimestampMixin, UUIDMixin


class TipoMovimento(StrEnum):
    ENTRADA = "entrada"
    SAIDA = "saida"
    AJUSTE = "ajuste"
    # Composição de kits: implementado na Etapa 3
    MONTAGEM = "montagem"
    RESERVA = "reserva"
    LIBERACAO = "liberacao"
    # Cancelamento de venda já fechada: implementado na Fase 3 Bloco 3
    ESTORNO = "estorno"


class MovimentoEstoque(UUIDMixin, EmpresaMixin, Base):
    """Lançamento imutável do histórico de estoque.

    `quantidade` tem sinal e se refere ao saldo físico (entrada, saída,
    ajuste) ou ao reservado (reserva, liberação), conforme o `tipo`.
    O `id` pode vir do cliente (sincronização offline): reenviar o mesmo
    id não reprocessa o movimento, só devolve o já existente.
    """

    __tablename__ = "movimentacoes_estoque"
    __table_args__ = (UniqueConstraint("empresa_id", "id"),)

    produto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("produtos.id", ondelete="RESTRICT"), index=True
    )
    tipo: Mapped[TipoMovimento] = mapped_column(
        Enum(
            TipoMovimento,
            name="tipo_movimento",
            native_enum=False,
            create_constraint=True,
            length=20,
            values_callable=lambda enum: [item.value for item in enum],
        )
    )
    quantidade: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    # Vazio em reserva/liberação, que não têm custo
    custo_unitario: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    origem: Mapped[str | None] = mapped_column(String(60))
    # Quando aconteceu de fato (pode ser retroativo, ex. sync offline)
    ocorrido_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    # Quando entrou no sistema; a ordem de cálculo do custo médio segue esta coluna
    registrado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SaldoEstoque(UUIDMixin, EmpresaMixin, TimestampMixin, Base):
    """Cache do saldo por produto. A verdade histórica é `MovimentoEstoque`."""

    __tablename__ = "saldos_estoque"
    __table_args__ = (UniqueConstraint("empresa_id", "produto_id"),)

    produto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("produtos.id", ondelete="RESTRICT"), index=True
    )
    fisico: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"), server_default="0")
    reservado: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), default=Decimal("0"), server_default="0"
    )

    @property
    def disponivel(self) -> Decimal:
        return self.fisico - self.reservado

"""Vendas, itens e pagamentos (seções 6 e 7.4 do ROADMAP).

Uma venda é um ticket: nasce ABERTO (o caixa ainda pode adicionar e remover
itens), e só vira histórico de verdade quando FECHADO (pago) ou CANCELADO.
Cada item adicionado reserva o estoque na hora (evita vender o que não tem);
a reserva vira baixa de verdade só no fechamento. Cancelar um ticket em
ABERTO só libera as reservas; cancelar uma venda já FECHADA estorna o
estoque de verdade (`TipoMovimento.ESTORNO`) e exige a permissão
`vendas.cancelar` — mais sensível que descartar um ticket que nunca chegou
a ser pago.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models import Base, EmpresaMixin, TimestampMixin, UUIDMixin


class StatusVenda(StrEnum):
    ABERTO = "aberto"
    FECHADO = "fechado"
    CANCELADO = "cancelado"


class CanalVenda(StrEnum):
    PDV = "pdv"
    # Reservados pro futuro (Fases 10/11): ainda não é possível criar venda
    # com esses canais.
    VITRINE = "vitrine"
    MARKETPLACE = "marketplace"


class FormaPagamento(StrEnum):
    DINHEIRO = "dinheiro"
    # Histórico anterior à separação: não dizia se foi crédito ou débito.
    # A tela só oferece os dois abaixo.
    CARTAO = "cartao"
    CARTAO_CREDITO = "cartao_credito"
    CARTAO_DEBITO = "cartao_debito"
    PIX = "pix"


def _enum_curto(tipo: type[StrEnum], nome: str) -> Enum:
    return Enum(
        tipo,
        name=nome,
        native_enum=False,
        create_constraint=True,
        length=20,
        values_callable=lambda enum: [item.value for item in enum],
    )


class Venda(UUIDMixin, EmpresaMixin, Base):
    """Um ticket de venda. `id` pode vir do dispositivo (PDV offline), igual
    ao padrão já usado em estoque e clientes."""

    __tablename__ = "vendas"
    __table_args__ = (
        UniqueConstraint("empresa_id", "id"),
        UniqueConstraint("empresa_id", "numero"),
    )

    numero: Mapped[str] = mapped_column(String(20))
    cliente_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clientes.id", ondelete="RESTRICT"), index=True
    )
    vendedor_usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT")
    )
    canal: Mapped[CanalVenda] = mapped_column(
        _enum_curto(CanalVenda, "canal_venda"),
        default=CanalVenda.PDV,
        server_default=CanalVenda.PDV.value,
    )
    status: Mapped[StatusVenda] = mapped_column(
        _enum_curto(StatusVenda, "status_venda"),
        default=StatusVenda.ABERTO,
        server_default=StatusVenda.ABERTO.value,
        index=True,
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), server_default="0")
    desconto_total: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0"), server_default="0"
    )
    total: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), server_default="0")
    # Quando o ticket foi aberto (pode ser retroativo, ex. sync offline)
    ocorrido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Quando foi fechado (pago) — nulo enquanto aberto ou se foi cancelado
    fechado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Quando foi cancelado (ticket em aberto descartado, ou venda já fechada
    # cancelada com estorno de estoque) — nulo se nunca foi cancelado
    cancelado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Quando entrou no sistema
    registrado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ItemVenda(UUIDMixin, TimestampMixin, Base):
    """Linha de uma venda. Sem `empresa_id` própria — escopada pela venda,
    igual `ProdutoUnidade`."""

    __tablename__ = "itens_venda"

    venda_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendas.id", ondelete="CASCADE"), index=True
    )
    produto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("produtos.id", ondelete="RESTRICT"), index=True
    )
    # Reserva criada ao adicionar o item (enquanto o ticket está aberto);
    # nula pra produto que não controla estoque (serviço, mão de obra).
    movimento_reserva_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movimentacoes_estoque.id", ondelete="RESTRICT")
    )
    # Saída de verdade, gerada só no fechamento (a reserva é liberada e
    # convertida nesta baixa). Nula enquanto o ticket está aberto.
    movimento_estoque_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movimentacoes_estoque.id", ondelete="RESTRICT")
    )
    # Estorno gerado se a venda (já fechada) foi cancelada depois. Nula até
    # que isso aconteça.
    movimento_estorno_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("movimentacoes_estoque.id", ondelete="RESTRICT")
    )
    quantidade: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    # Preço de tabela, desconto e preço final, por unidade — sempre na
    # unidade de estoque do produto (a alternativa, se usada, já foi
    # convertida antes de chegar aqui).
    preco_tabela: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    desconto: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    preco_final: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    # Custo vigente no fechamento (vindo da saída gerada nesse momento);
    # nulo enquanto aberto, ou pra produto que não controla estoque.
    custo_unitario: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))


class PagamentoVenda(UUIDMixin, TimestampMixin, Base):
    """Uma forma de pagamento usada no fechamento de uma venda. Uma venda
    pode ter mais de uma (ex.: parte em dinheiro, parte no cartão). Sem
    `empresa_id` própria — escopada pela venda."""

    __tablename__ = "pagamentos_venda"

    venda_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendas.id", ondelete="CASCADE"), index=True
    )
    forma: Mapped[FormaPagamento] = mapped_column(_enum_curto(FormaPagamento, "forma_pagamento"))
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 2))

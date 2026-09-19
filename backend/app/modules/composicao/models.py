"""Componentes de um kit."""

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models import Base, EmpresaMixin, TimestampMixin, UUIDMixin


class ComponenteComposto(UUIDMixin, EmpresaMixin, TimestampMixin, Base):
    """Um componente da "receita" de um kit.

    A quantidade está sempre na unidade de estoque do componente.
    """

    __tablename__ = "componentes_compostos"
    __table_args__ = (
        UniqueConstraint("empresa_id", "produto_composto_id", "componente_id"),
    )

    produto_composto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("produtos.id", ondelete="CASCADE"), index=True
    )
    componente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("produtos.id", ondelete="RESTRICT"), index=True
    )
    quantidade: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    # Só entra na quantidade consumida durante a montagem
    perda_percentual: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0"), server_default="0"
    )

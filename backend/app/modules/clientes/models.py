"""Clientes da empresa (seção 7.1 do ROADMAP)."""

import uuid
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, UniqueConstraint, false
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models import Base, EmpresaMixin, TimestampMixin, UUIDMixin


class OrigemCliente(StrEnum):
    BALCAO = "balcao"
    VITRINE = "vitrine"
    MARKETPLACE = "marketplace"


class Cliente(UUIDMixin, EmpresaMixin, TimestampMixin, Base):
    """Cliente de uma empresa. Nunca compartilhado nem cruzado entre empresas.

    `id` pode vir do dispositivo (cadastro no PDV offline) — aceito do
    cliente da API, igual ao padrão já usado em estoque.
    """

    __tablename__ = "clientes"
    __table_args__ = (UniqueConstraint("empresa_id", "id"),)

    nome: Mapped[str] = mapped_column(String(120))
    # Principal meio de contato; não é único (duplicados existem, ver "mesclar")
    telefone: Mapped[str | None] = mapped_column(String(20), index=True)
    email: Mapped[str | None] = mapped_column(String(255))
    # Opcional; necessário só quando o cliente final pedir CPF na nota
    cpf: Mapped[str | None] = mapped_column(String(14))
    data_nascimento: Mapped[date | None] = mapped_column(Date)
    endereco: Mapped[str | None] = mapped_column(String(500))

    consentimento_marketing: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false()
    )
    consentimento_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    origem: Mapped[OrigemCliente] = mapped_column(
        Enum(
            OrigemCliente,
            name="origem_cliente",
            native_enum=False,
            create_constraint=True,
            length=20,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=OrigemCliente.BALCAO,
        server_default=OrigemCliente.BALCAO.value,
    )

    # Cadastro nunca é excluído nem desativado: fica armazenado até ser
    # necessário de novo.
    anonimizado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Preenchido quando este cadastro foi mesclado em outro (duplicado
    # descoberto depois). As vendas dele já foram todas reatribuídas ao
    # sobrevivente; este registro fica só de rastro, escondido da listagem.
    mesclado_com_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clientes.id", ondelete="RESTRICT")
    )

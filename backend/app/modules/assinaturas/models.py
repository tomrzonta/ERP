"""Planos, regras dos planos e assinaturas das empresas."""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    true,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models import Base, EmpresaMixin, TimestampMixin, UUIDMixin


def _enum(classe: type[StrEnum], nome: str) -> Enum:
    return Enum(
        classe,
        name=nome,
        native_enum=False,
        create_constraint=True,
        length=20,
        values_callable=lambda enum: [item.value for item in enum],
    )


class Plano(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "planos"

    codigo: Mapped[str] = mapped_column(String(30), unique=True)
    nome: Mapped[str] = mapped_column(String(60))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())


class TipoRegra(StrEnum):
    RECURSO = "recurso"
    LIMITE = "limite"


class PlanoRegra(Base):
    """Recurso incluído ou limite de um plano.

    Recurso: presente = incluído; valor sempre vazio.
    Limite: valor numérico, ou vazio para ilimitado.
    """

    __tablename__ = "plano_regras"
    __table_args__ = (
        CheckConstraint("tipo = 'limite' OR valor IS NULL", name="recurso_sem_valor"),
    )

    plano_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("planos.id", ondelete="CASCADE"), primary_key=True
    )
    chave: Mapped[str] = mapped_column(String(50), primary_key=True)
    tipo: Mapped[TipoRegra] = mapped_column(_enum(TipoRegra, "tipo_regra"))
    valor: Mapped[int | None] = mapped_column(Integer)


class StatusAssinatura(StrEnum):
    TRIAL = "trial"
    ATIVA = "ativa"
    INADIMPLENTE = "inadimplente"
    CANCELADA = "cancelada"


class Assinatura(UUIDMixin, EmpresaMixin, TimestampMixin, Base):
    """Assinatura da empresa. Existe exatamente uma por empresa."""

    __tablename__ = "assinaturas"
    __table_args__ = (UniqueConstraint("empresa_id"),)

    plano_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("planos.id", ondelete="RESTRICT")
    )
    status: Mapped[StatusAssinatura] = mapped_column(_enum(StatusAssinatura, "status_assinatura"))
    trial_termina_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    periodo_atual_termina_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    carencia_termina_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

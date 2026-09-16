"""Empresas: cada cliente do SaaS (tenant)."""

from sqlalchemy import Boolean, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models import Base, TimestampMixin, UUIDMixin


class Empresa(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "empresas"

    nome_fantasia: Mapped[str] = mapped_column(String(120))
    razao_social: Mapped[str | None] = mapped_column(String(200))
    # CPF ou CNPJ, apenas dígitos
    documento: Mapped[str | None] = mapped_column(String(14))
    # Endereço amigável, usado na vitrine
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    # Define o que é "hoje" em relatórios e caixa do dia
    fuso_horario: Mapped[str] = mapped_column(
        String(50), default="America/Sao_Paulo", server_default="America/Sao_Paulo"
    )
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

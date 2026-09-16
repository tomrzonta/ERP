"""Usuários: pessoas que operam o sistema e fazem login.

Usuário é global (sem empresa_id). A ligação com cada empresa fica em
acesso.Membro. Não confundir com clientes, que pertencem a uma empresa.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models import Base, TimestampMixin, UUIDMixin


class Usuario(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "usuarios"

    nome: Mapped[str] = mapped_column(String(120))
    # Sempre gravado em minúsculas pelo service
    email: Mapped[str] = mapped_column(String(254), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    email_verificado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ultimo_login_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

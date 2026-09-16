"""Acesso: papéis, permissões concedidas e membros de cada empresa."""

import uuid
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    UniqueConstraint,
    false,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models import Base, EmpresaMixin, TimestampMixin, UUIDMixin


class Papel(UUIDMixin, EmpresaMixin, TimestampMixin, Base):
    """Papel dentro de uma empresa (Dono, Gerente, Caixa...).

    Cada empresa tem as próprias cópias dos papéis padrão.
    """

    __tablename__ = "papeis"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nome"),
        # Permite que membros garantam, no banco, que o papel é da mesma empresa
        UniqueConstraint("empresa_id", "id"),
    )

    nome: Mapped[str] = mapped_column(String(60))
    descricao: Mapped[str | None] = mapped_column(String(255))
    # Identifica papéis criados a partir dos padrões (ex. "dono")
    codigo_padrao: Mapped[str | None] = mapped_column(String(30))
    # Protegido não pode ser editado nem excluído (ex. Dono)
    protegido: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())


class PapelPermissao(Base):
    """Permissão concedida a um papel.

    O catálogo de permissões válidas é definido no código de cada módulo;
    aqui ficam apenas os códigos concedidos.
    """

    __tablename__ = "papel_permissoes"

    papel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("papeis.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permissao: Mapped[str] = mapped_column(String(80), primary_key=True)


class StatusMembro(StrEnum):
    ATIVO = "ativo"
    CONVIDADO = "convidado"
    DESATIVADO = "desativado"


class Membro(UUIDMixin, EmpresaMixin, TimestampMixin, Base):
    """Ligação entre um usuário e uma empresa, com o papel que ele exerce nela."""

    __tablename__ = "membros"
    __table_args__ = (
        UniqueConstraint("empresa_id", "usuario_id"),
        # O papel precisa pertencer à mesma empresa do membro
        ForeignKeyConstraint(
            ["empresa_id", "papel_id"],
            ["papeis.empresa_id", "papeis.id"],
            ondelete="RESTRICT",
        ),
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        index=True,
    )
    papel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    status: Mapped[StatusMembro] = mapped_column(
        Enum(
            StatusMembro,
            name="status_membro",
            native_enum=False,
            create_constraint=True,
            length=20,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=StatusMembro.ATIVO,
        server_default=StatusMembro.ATIVO.value,
    )

"""Unidades de medida, categorias, produtos e unidades alternativas."""

import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    false,
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


class UnidadeMedida(Base):
    """Catálogo do sistema (não pertence a nenhuma empresa).

    Espelha app.modules.produtos.unidades.UNIDADES, que é a fonte da verdade.
    """

    __tablename__ = "unidades"

    codigo: Mapped[str] = mapped_column(String(10), primary_key=True)
    nome: Mapped[str] = mapped_column(String(40))
    grandeza: Mapped[str] = mapped_column(String(20))
    fator_canonico: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    casas_exibidas: Mapped[int] = mapped_column(Integer)


class Categoria(UUIDMixin, EmpresaMixin, TimestampMixin, Base):
    __tablename__ = "categorias"
    __table_args__ = (
        UniqueConstraint("empresa_id", "nome"),
        UniqueConstraint("empresa_id", "id"),
    )

    nome: Mapped[str] = mapped_column(String(60))
    categoria_pai_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class TipoProduto(StrEnum):
    SIMPLES = "simples"
    # Tem saldo próprio; a montagem dá baixa nos componentes e credita o kit
    KIT = "kit"


class StatusProduto(StrEnum):
    ATIVO = "ativo"
    INATIVO = "inativo"
    # Composto acima do limite do Base: vende o que tem, sem editar nem repor
    CONGELADO = "congelado"


class Produto(UUIDMixin, EmpresaMixin, TimestampMixin, Base):
    __tablename__ = "produtos"
    __table_args__ = (
        UniqueConstraint("empresa_id", "sku"),
        UniqueConstraint("empresa_id", "id"),
    )

    # Sempre em maiúsculas; chave do vínculo com anúncios de marketplaces
    sku: Mapped[str] = mapped_column(String(40))
    nome: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[TipoProduto] = mapped_column(_enum(TipoProduto, "tipo_produto"))
    status: Mapped[StatusProduto] = mapped_column(
        _enum(StatusProduto, "status_produto"),
        default=StatusProduto.ATIVO,
        server_default=StatusProduto.ATIVO.value,
    )

    # Unidade de estoque: saldo e custo são sempre gravados nela
    unidade_codigo: Mapped[str] = mapped_column(
        String(10), ForeignKey("unidades.codigo", ondelete="RESTRICT")
    )
    categoria_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    vendavel: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    # Insumo não vendável (filamento, terra) não aparece no PDV nem na vitrine
    insumo: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    # Serviços e mão de obra não têm saldo
    controla_estoque: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    preco_venda: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    custo_medio: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal("0"))
    custo_ultima_compra: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))

    # Abaixo (ou igual) disso, o saldo disponível gera alerta de estoque baixo.
    estoque_minimo: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    codigo_barras: Mapped[str | None] = mapped_column(String(20), index=True)
    descricao: Mapped[str | None] = mapped_column(String(500))

    # Vitrine (Fase 10)
    publicado_na_vitrine: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false()
    )
    descricao_publica: Mapped[str | None] = mapped_column(String(2000))

    # Fiscais (Fase 12), previstos desde já
    ncm: Mapped[str | None] = mapped_column(String(8))
    cest: Mapped[str | None] = mapped_column(String(7))
    origem: Mapped[str | None] = mapped_column(String(1))


class ProdutoUnidade(UUIDMixin, TimestampMixin, Base):
    """Embalagem ou fração do produto: rolo de 1 kg, caixa com 12, fatia de 1/8.

    O fator é sempre em relação à unidade de estoque do produto.
    """

    __tablename__ = "produto_unidades"
    __table_args__ = (UniqueConstraint("produto_id", "nome"),)

    produto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("produtos.id", ondelete="CASCADE"), index=True
    )
    nome: Mapped[str] = mapped_column(String(30))
    fator: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    usa_na_compra: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    usa_na_venda: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())


class CustoAdicionalProduto(UUIDMixin, TimestampMixin, Base):
    """Custo extra por unidade produzida (embalagem, energia, mão de obra) — Pro.

    Some ao custo_medio na hora de calcular o custo total e a margem. Sem
    `empresa_id` própria — é escopada pelo produto, igual `ProdutoUnidade`.
    """

    __tablename__ = "custos_adicionais_produto"
    __table_args__ = (UniqueConstraint("produto_id", "nome"),)

    produto_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("produtos.id", ondelete="CASCADE"), index=True
    )
    nome: Mapped[str] = mapped_column(String(60))
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 6))

"""Consultas do módulo de vendas."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Select, exists, func, select, update
from sqlalchemy.orm import Session

from app.modules.vendas.models import (
    FormaPagamento,
    ItemVenda,
    PagamentoVenda,
    StatusVenda,
    Venda,
)
from app.shared.repository import RepositorioDaEmpresa


class VendaRepositorio(RepositorioDaEmpresa[Venda]):
    modelo = Venda
    mensagem_nao_encontrado = "Venda não encontrada."

    def numero_em_uso(self, numero: str) -> bool:
        consulta = self.selecionar().where(Venda.numero == numero)
        return self.db.scalar(select(exists(consulta))) or False

    def buscar(
        self,
        *,
        status: StatusVenda | None = None,
        cliente_id: uuid.UUID | None = None,
        limite: int = 50,
        deslocamento: int = 0,
    ) -> list[Venda]:
        consulta: Select[tuple[Venda]] = self.selecionar()
        if status is not None:
            consulta = consulta.where(Venda.status == status)
        if cliente_id is not None:
            consulta = consulta.where(Venda.cliente_id == cliente_id)
        consulta = (
            consulta.order_by(Venda.ocorrido_em.desc()).limit(limite).offset(deslocamento)
        )
        return list(self.db.scalars(consulta))

    def metricas_do_cliente(self, cliente_id: uuid.UUID) -> tuple[int, Decimal, object, object]:
        """(quantidade de compras fechadas, valor total, primeira, última)."""
        consulta = select(
            func.count(Venda.id),
            func.coalesce(func.sum(Venda.total), 0),
            func.min(Venda.ocorrido_em),
            func.max(Venda.ocorrido_em),
        ).where(
            Venda.empresa_id == self.empresa_id,
            Venda.cliente_id == cliente_id,
            Venda.status == StatusVenda.FECHADO,
        )
        return self.db.execute(consulta).one()

    # --- Agregações do resumo (só vendas FECHADAS, por `ocorrido_em`) ---

    def _fechadas_no_periodo(self, inicio: datetime, fim: datetime):
        return (
            Venda.empresa_id == self.empresa_id,
            Venda.status == StatusVenda.FECHADO,
            Venda.ocorrido_em >= inicio,
            Venda.ocorrido_em < fim,
        )

    def totais_do_periodo(self, inicio: datetime, fim: datetime) -> tuple[int, Decimal, Decimal]:
        """(quantidade de vendas, faturamento, descontos concedidos)."""
        consulta = select(
            func.count(Venda.id),
            func.coalesce(func.sum(Venda.total), 0),
            func.coalesce(func.sum(Venda.desconto_total), 0),
        ).where(*self._fechadas_no_periodo(inicio, fim))
        return self.db.execute(consulta).one()

    def cancelamentos_do_periodo(self, inicio: datetime, fim: datetime) -> int:
        consulta = select(func.count(Venda.id)).where(
            Venda.empresa_id == self.empresa_id,
            Venda.status == StatusVenda.CANCELADO,
            Venda.cancelado_em.is_not(None),
            Venda.ocorrido_em >= inicio,
            Venda.ocorrido_em < fim,
        )
        return self.db.scalar(consulta) or 0

    def custo_do_periodo(self, inicio: datetime, fim: datetime) -> Decimal:
        """Custo das mercadorias vendidas (só itens que têm custo gravado)."""
        consulta = (
            select(func.coalesce(func.sum(ItemVenda.quantidade * ItemVenda.custo_unitario), 0))
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .where(*self._fechadas_no_periodo(inicio, fim), ItemVenda.custo_unitario.is_not(None))
        )
        return self.db.scalar(consulta) or Decimal("0")

    def faturamento_por_dia(
        self, inicio: datetime, fim: datetime, fuso: str
    ) -> list[tuple[date, int, Decimal]]:
        dia = func.date(func.timezone(fuso, Venda.ocorrido_em))
        consulta = (
            select(dia, func.count(Venda.id), func.sum(Venda.total))
            .where(*self._fechadas_no_periodo(inicio, fim))
            .group_by(dia)
            .order_by(dia)
        )
        return [tuple(linha) for linha in self.db.execute(consulta)]

    def produtos_mais_vendidos(
        self, inicio: datetime, fim: datetime, limite: int
    ) -> list[tuple[uuid.UUID, Decimal, Decimal]]:
        """(produto_id, quantidade vendida, receita), da maior receita pra menor."""
        receita = func.sum(ItemVenda.quantidade * ItemVenda.preco_final)
        consulta = (
            select(ItemVenda.produto_id, func.sum(ItemVenda.quantidade), receita)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .where(*self._fechadas_no_periodo(inicio, fim))
            .group_by(ItemVenda.produto_id)
            .order_by(receita.desc())
            .limit(limite)
        )
        return [tuple(linha) for linha in self.db.execute(consulta)]

    def recebido_por_forma(
        self, inicio: datetime, fim: datetime
    ) -> list[tuple[FormaPagamento, Decimal]]:
        consulta = (
            select(PagamentoVenda.forma, func.sum(PagamentoVenda.valor))
            .join(Venda, Venda.id == PagamentoVenda.venda_id)
            .where(*self._fechadas_no_periodo(inicio, fim))
            .group_by(PagamentoVenda.forma)
            .order_by(func.sum(PagamentoVenda.valor).desc())
        )
        return [tuple(linha) for linha in self.db.execute(consulta)]

    def itens_com_desconto(
        self, inicio: datetime, fim: datetime
    ) -> tuple[Decimal, Decimal, Decimal, Decimal, int, int]:
        """(receita a preço de tabela, descontos, receita final, custo,
        itens com desconto, vendas com desconto) — itens de vendas fechadas."""
        quantidade = ItemVenda.quantidade
        consulta = (
            select(
                func.coalesce(func.sum(quantidade * ItemVenda.preco_tabela), 0),
                func.coalesce(func.sum(quantidade * ItemVenda.desconto), 0),
                func.coalesce(func.sum(quantidade * ItemVenda.preco_final), 0),
                func.coalesce(
                    func.sum(quantidade * func.coalesce(ItemVenda.custo_unitario, 0)), 0
                ),
                func.count(ItemVenda.id).filter(ItemVenda.desconto > 0),
                func.count(func.distinct(ItemVenda.venda_id)).filter(ItemVenda.desconto > 0),
            )
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .where(*self._fechadas_no_periodo(inicio, fim))
        )
        return self.db.execute(consulta).one()

    def produtos_com_mais_desconto(
        self, inicio: datetime, fim: datetime, limite: int
    ) -> list[tuple[uuid.UUID, Decimal, Decimal]]:
        """(produto_id, desconto concedido, receita a preço de tabela)."""
        desconto = func.sum(ItemVenda.quantidade * ItemVenda.desconto)
        consulta = (
            select(
                ItemVenda.produto_id,
                desconto,
                func.sum(ItemVenda.quantidade * ItemVenda.preco_tabela),
            )
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .where(*self._fechadas_no_periodo(inicio, fim), ItemVenda.desconto > 0)
            .group_by(ItemVenda.produto_id)
            .order_by(desconto.desc())
            .limit(limite)
        )
        return [tuple(linha) for linha in self.db.execute(consulta)]

    def itens_para_exportar(
        self, inicio: datetime, fim: datetime, limite: int
    ) -> list[tuple[ItemVenda, Venda]]:
        consulta = (
            select(ItemVenda, Venda)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .where(*self._fechadas_no_periodo(inicio, fim))
            .order_by(Venda.ocorrido_em, Venda.numero, ItemVenda.created_at)
            .limit(limite)
        )
        return [(item, venda) for item, venda in self.db.execute(consulta)]

    def formas_por_venda(self, venda_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[FormaPagamento]]:
        if not venda_ids:
            return {}
        consulta = (
            select(PagamentoVenda.venda_id, PagamentoVenda.forma)
            .where(PagamentoVenda.venda_id.in_(venda_ids))
            .order_by(PagamentoVenda.created_at)
        )
        resultado: dict[uuid.UUID, list[FormaPagamento]] = {}
        for venda_id, forma in self.db.execute(consulta):
            resultado.setdefault(venda_id, []).append(forma)
        return resultado

    def compras_por_cliente(
        self, inicio: datetime, fim: datetime
    ) -> list[tuple[uuid.UUID, int, Decimal]]:
        """(cliente_id, compras fechadas, valor) no período, só clientes identificados."""
        consulta = (
            select(Venda.cliente_id, func.count(Venda.id), func.sum(Venda.total))
            .where(*self._fechadas_no_periodo(inicio, fim), Venda.cliente_id.is_not(None))
            .group_by(Venda.cliente_id)
        )
        return [tuple(linha) for linha in self.db.execute(consulta)]

    def vendas_sem_cliente(self, inicio: datetime, fim: datetime) -> tuple[int, Decimal]:
        consulta = select(func.count(Venda.id), func.coalesce(func.sum(Venda.total), 0)).where(
            *self._fechadas_no_periodo(inicio, fim), Venda.cliente_id.is_(None)
        )
        return self.db.execute(consulta).one()

    def primeira_compra_de(self, cliente_ids: list[uuid.UUID]) -> dict[uuid.UUID, datetime]:
        """Primeira compra fechada de cada cliente, em qualquer época."""
        if not cliente_ids:
            return {}
        consulta = (
            select(Venda.cliente_id, func.min(Venda.ocorrido_em))
            .where(
                Venda.empresa_id == self.empresa_id,
                Venda.status == StatusVenda.FECHADO,
                Venda.cliente_id.in_(cliente_ids),
            )
            .group_by(Venda.cliente_id)
        )
        return {cliente_id: primeira for cliente_id, primeira in self.db.execute(consulta)}

    def reatribuir_cliente(self, *, de_cliente_id: uuid.UUID, para_cliente_id: uuid.UUID) -> None:
        """Usado na mesclagem de clientes: todas as vendas do duplicado
        passam a apontar pro sobrevivente."""
        self.db.execute(
            update(Venda)
            .where(Venda.empresa_id == self.empresa_id, Venda.cliente_id == de_cliente_id)
            .values(cliente_id=para_cliente_id)
        )


def itens_da_venda(db: Session, venda_id: uuid.UUID) -> list[ItemVenda]:
    return list(db.scalars(select(ItemVenda).where(ItemVenda.venda_id == venda_id)))


def item_da_venda(db: Session, venda_id: uuid.UUID, item_id: uuid.UUID) -> ItemVenda | None:
    consulta = select(ItemVenda).where(ItemVenda.venda_id == venda_id, ItemVenda.id == item_id)
    return db.scalar(consulta)


def pagamentos_da_venda(db: Session, venda_id: uuid.UUID) -> list[PagamentoVenda]:
    return list(db.scalars(select(PagamentoVenda).where(PagamentoVenda.venda_id == venda_id)))

"""Consultas do módulo de estoque."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError

from app.modules.estoque.models import MovimentoEstoque, SaldoEstoque, TipoMovimento
from app.shared.repository import RepositorioDaEmpresa


class MovimentoRepositorio(RepositorioDaEmpresa[MovimentoEstoque]):
    modelo = MovimentoEstoque
    mensagem_nao_encontrado = "Movimento não encontrado."

    def buscar(
        self,
        *,
        produto_id: uuid.UUID | None = None,
        tipo: TipoMovimento | None = None,
        limite: int = 50,
        deslocamento: int = 0,
    ) -> list[MovimentoEstoque]:
        consulta = self.selecionar()
        if produto_id is not None:
            consulta = consulta.where(MovimentoEstoque.produto_id == produto_id)
        if tipo is not None:
            consulta = consulta.where(MovimentoEstoque.tipo == tipo)
        consulta = (
            consulta.order_by(MovimentoEstoque.registrado_em.desc())
            .limit(limite)
            .offset(deslocamento)
        )
        return list(self.db.scalars(consulta))


    def consumo_e_perdas(
        self, inicio: datetime, fim: datetime
    ) -> list[tuple[uuid.UUID, Decimal, Decimal, Decimal, Decimal]]:
        """Por produto, no período: (consumido em montagens, custo disso,
        baixado por ajuste, custo disso). Saídas têm quantidade negativa, então
        só entram movimentos com sinal negativo, invertidos."""
        q = MovimentoEstoque.quantidade
        custo = func.coalesce(MovimentoEstoque.custo_unitario, 0)
        e_montagem = (MovimentoEstoque.tipo == TipoMovimento.MONTAGEM) & (q < 0)
        e_ajuste = (MovimentoEstoque.tipo == TipoMovimento.AJUSTE) & (q < 0)

        def somar(condicao, valor):
            return func.coalesce(func.sum(case((condicao, valor), else_=0)), 0)

        consulta = (
            select(
                MovimentoEstoque.produto_id,
                somar(e_montagem, -q),
                somar(e_montagem, -q * custo),
                somar(e_ajuste, -q),
                somar(e_ajuste, -q * custo),
            )
            .where(
                MovimentoEstoque.empresa_id == self.empresa_id,
                MovimentoEstoque.tipo.in_((TipoMovimento.MONTAGEM, TipoMovimento.AJUSTE)),
                MovimentoEstoque.ocorrido_em >= inicio,
                MovimentoEstoque.ocorrido_em < fim,
            )
            .group_by(MovimentoEstoque.produto_id)
        )
        return [tuple(linha) for linha in self.db.execute(consulta)]


class SaldoRepositorio(RepositorioDaEmpresa[SaldoEstoque]):
    modelo = SaldoEstoque
    mensagem_nao_encontrado = "Saldo não encontrado."

    def por_produto(self, produto_id: uuid.UUID) -> SaldoEstoque | None:
        consulta = self.selecionar().where(SaldoEstoque.produto_id == produto_id)
        return self.db.scalar(consulta)

    def mapa_por_produtos(self, produto_ids: list[uuid.UUID]) -> dict[uuid.UUID, SaldoEstoque]:
        if not produto_ids:
            return {}
        consulta = self.selecionar().where(SaldoEstoque.produto_id.in_(produto_ids))
        return {saldo.produto_id: saldo for saldo in self.db.scalars(consulta)}

    def travar_ou_criar(self, produto_id: uuid.UUID) -> SaldoEstoque:
        """Saldo do produto com SELECT FOR UPDATE, criando-o na primeira vez.

        A criação roda num savepoint: se outra transação criar o mesmo saldo
        ao mesmo tempo, a constraint única falha, desfazemos o savepoint e
        buscamos de novo — o FOR UPDATE espera a outra transação terminar.
        """
        consulta = self.selecionar().where(SaldoEstoque.produto_id == produto_id).with_for_update()
        saldo = self.db.scalar(consulta)
        if saldo is not None:
            return saldo

        try:
            with self.db.begin_nested():
                saldo = SaldoEstoque(
                    produto_id=produto_id, fisico=Decimal("0"), reservado=Decimal("0")
                )
                self.adicionar(saldo)
            return saldo
        except IntegrityError:
            return self.db.scalar(consulta)  # type: ignore[return-value]

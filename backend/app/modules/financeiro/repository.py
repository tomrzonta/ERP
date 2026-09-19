"""Consultas do módulo financeiro (caixa e lançamentos)."""

import uuid
from datetime import date

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.modules.financeiro.models import (
    CaixaSessao,
    ContaFinanceira,
    LancamentoCaixa,
    StatusCaixa,
    StatusConta,
    TipoConta,
)
from app.shared.repository import RepositorioDaEmpresa


class CaixaRepositorio(RepositorioDaEmpresa[CaixaSessao]):
    modelo = CaixaSessao
    mensagem_nao_encontrado = "Caixa não encontrado."

    def contar_abertos(self) -> int:
        consulta = (
            select(func.count())
            .select_from(CaixaSessao)
            .where(CaixaSessao.empresa_id == self.empresa_id, CaixaSessao.status == StatusCaixa.ABERTO)
        )
        return self.db.scalar(consulta) or 0

    def aberto(self) -> CaixaSessao | None:
        consulta = self.selecionar().where(CaixaSessao.status == StatusCaixa.ABERTO)
        return self.db.scalar(consulta)

    def buscar(self, *, limite: int = 50, deslocamento: int = 0) -> list[CaixaSessao]:
        consulta: Select[tuple[CaixaSessao]] = (
            self.selecionar().order_by(CaixaSessao.aberto_em.desc()).limit(limite).offset(deslocamento)
        )
        return list(self.db.scalars(consulta))


class ContaRepositorio(RepositorioDaEmpresa[ContaFinanceira]):
    modelo = ContaFinanceira
    mensagem_nao_encontrado = "Conta não encontrada."

    def buscar(
        self,
        *,
        tipo: TipoConta | None = None,
        status: StatusConta | None = None,
        limite: int = 100,
        deslocamento: int = 0,
    ) -> list[ContaFinanceira]:
        consulta = self.selecionar()
        if tipo is not None:
            consulta = consulta.where(ContaFinanceira.tipo == tipo)
        if status is not None:
            consulta = consulta.where(ContaFinanceira.status == status)
        consulta = (
            consulta.order_by(ContaFinanceira.vencimento, ContaFinanceira.criado_em)
            .limit(limite)
            .offset(deslocamento)
        )
        return list(self.db.scalars(consulta))

    def abertas_ate(self, limite: date) -> list[ContaFinanceira]:
        consulta = self.selecionar().where(
            ContaFinanceira.status == StatusConta.ABERTA, ContaFinanceira.vencimento <= limite
        )
        return list(self.db.scalars(consulta))


def lancamentos_do_caixa(db: Session, caixa_id: uuid.UUID) -> list[LancamentoCaixa]:
    consulta = (
        select(LancamentoCaixa)
        .where(LancamentoCaixa.caixa_id == caixa_id)
        .order_by(LancamentoCaixa.ocorrido_em)
    )
    return list(db.scalars(consulta))


def lancamento_da_empresa(
    db: Session, empresa_id: uuid.UUID, lancamento_id: uuid.UUID
) -> LancamentoCaixa | None:
    """Busca por id garantindo a empresa (o lançamento não tem empresa_id
    própria — vai pela sessão de caixa)."""
    consulta = (
        select(LancamentoCaixa)
        .join(CaixaSessao, CaixaSessao.id == LancamentoCaixa.caixa_id)
        .where(LancamentoCaixa.id == lancamento_id, CaixaSessao.empresa_id == empresa_id)
    )
    return db.scalar(consulta)

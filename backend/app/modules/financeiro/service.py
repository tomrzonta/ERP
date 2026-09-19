"""Regras de negócio do caixa do dia."""

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal
from typing import TypedDict

from sqlalchemy.orm import Session

from app.core.exceptions import RegraDeNegocio
from app.modules.assinaturas import service as assinaturas_service
from app.modules.assinaturas.regras import Limite
from app.modules.financeiro import repository
from app.modules.financeiro.models import (
    CaixaSessao,
    ContaFinanceira,
    LancamentoCaixa,
    OrigemLancamento,
    StatusCaixa,
    StatusConta,
    TipoConta,
    TipoLancamento,
)
from app.modules.financeiro.repository import CaixaRepositorio, ContaRepositorio
from app.modules.vendas.models import FormaPagamento
from app.shared.money import to_money


class PagamentoDaVenda(TypedDict):
    forma: str
    valor: Decimal


@dataclass(frozen=True)
class ResumoCaixa:
    total_entradas: Decimal
    total_saidas: Decimal
    saldo_esperado_dinheiro: Decimal
    # Só depois de fechado (valor_contado - saldo_esperado_dinheiro).
    diferenca: Decimal | None


def _caixa_aberto_ou_erro(db: Session, empresa_id: uuid.UUID, caixa_id: uuid.UUID) -> CaixaSessao:
    caixa = CaixaRepositorio(db, empresa_id).obter_ou_erro(caixa_id)
    if caixa.status is not StatusCaixa.ABERTO:
        raise RegraDeNegocio("Este caixa já está fechado.")
    return caixa


def abrir_caixa(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    usuario_id: uuid.UUID,
    valor_inicial: Decimal,
    observacao: str | None = None,
) -> CaixaSessao:
    if valor_inicial < 0:
        raise RegraDeNegocio("O valor inicial não pode ser negativo.")

    repo = CaixaRepositorio(db, empresa_id)
    assinaturas_service.verificar_limite(
        db, empresa_id, Limite.MAX_CAIXAS_OFFLINE, repo.contar_abertos()
    )

    caixa = CaixaSessao(
        aberto_por_usuario_id=usuario_id,
        status=StatusCaixa.ABERTO,
        valor_inicial=to_money(valor_inicial),
        observacao=(observacao or "").strip() or None,
    )
    return repo.adicionar(caixa)


def fechar_caixa(
    db: Session,
    empresa_id: uuid.UUID,
    caixa_id: uuid.UUID,
    *,
    usuario_id: uuid.UUID,
    valor_contado: Decimal,
    observacao: str | None = None,
) -> CaixaSessao:
    if valor_contado < 0:
        raise RegraDeNegocio("O valor contado não pode ser negativo.")

    caixa = _caixa_aberto_ou_erro(db, empresa_id, caixa_id)
    caixa.status = StatusCaixa.FECHADO
    caixa.valor_contado = to_money(valor_contado)
    caixa.fechado_por_usuario_id = usuario_id
    caixa.fechado_em = datetime.now(UTC)
    if observacao is not None:
        caixa.observacao = observacao.strip() or None

    db.flush()
    return caixa


def caixa_aberto(db: Session, empresa_id: uuid.UUID) -> CaixaSessao | None:
    return CaixaRepositorio(db, empresa_id).aberto()


def obter_caixa(db: Session, empresa_id: uuid.UUID, caixa_id: uuid.UUID) -> CaixaSessao:
    return CaixaRepositorio(db, empresa_id).obter_ou_erro(caixa_id)


def listar_caixas(
    db: Session, empresa_id: uuid.UUID, *, limite: int = 50, deslocamento: int = 0
) -> list[CaixaSessao]:
    return CaixaRepositorio(db, empresa_id).buscar(limite=limite, deslocamento=deslocamento)


def lancar_manual(
    db: Session,
    empresa_id: uuid.UUID,
    caixa_id: uuid.UUID,
    *,
    usuario_id: uuid.UUID,
    tipo: TipoLancamento,
    valor: Decimal,
    forma_pagamento: FormaPagamento,
    descricao: str | None = None,
    ocorrido_em: datetime | None = None,
) -> LancamentoCaixa:
    if valor <= 0:
        raise RegraDeNegocio("O valor do lançamento precisa ser maior que zero.")

    _caixa_aberto_ou_erro(db, empresa_id, caixa_id)

    lancamento = LancamentoCaixa(
        caixa_id=caixa_id,
        tipo=tipo,
        origem=OrigemLancamento.MANUAL,
        forma_pagamento=forma_pagamento,
        valor=to_money(valor),
        descricao=(descricao or "").strip() or None,
        usuario_id=usuario_id,
        ocorrido_em=ocorrido_em if ocorrido_em is not None else datetime.now(UTC),
    )
    db.add(lancamento)
    db.flush()
    return lancamento


def sincronizar_lancamento_offline(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    id: uuid.UUID,
    usuario_id: uuid.UUID,
    tipo: TipoLancamento,
    valor: Decimal,
    forma_pagamento: FormaPagamento,
    ocorrido_em: datetime,
    descricao: str | None = None,
) -> LancamentoCaixa:
    """Entrada/saída avulsa feita offline. Entra no caixa aberto **agora**
    (o dispositivo pode nem saber qual era); sem caixa aberto, recusa.
    `id` do dispositivo: reenviar não duplica."""
    existente = repository.lancamento_da_empresa(db, empresa_id, id)
    if existente is not None:
        return existente

    if valor <= 0:
        raise RegraDeNegocio("O valor do lançamento precisa ser maior que zero.")
    caixa = caixa_aberto(db, empresa_id)
    if caixa is None:
        raise RegraDeNegocio("Não há caixa aberto pra receber este lançamento. Abra um caixa.")

    lancamento = LancamentoCaixa(
        caixa_id=caixa.id,
        tipo=tipo,
        origem=OrigemLancamento.MANUAL,
        forma_pagamento=forma_pagamento,
        valor=to_money(valor),
        descricao=(descricao or "").strip() or None,
        usuario_id=usuario_id,
        ocorrido_em=ocorrido_em,
    )
    lancamento.id = id
    db.add(lancamento)
    db.flush()
    return lancamento


def registrar_lancamentos_de_venda(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    venda_id: uuid.UUID,
    usuario_id: uuid.UUID,
    pagamentos: list[PagamentoDaVenda],
    ocorrido_em: datetime,
) -> None:
    """Chamado do módulo de vendas ao fechar uma venda (online ou
    sincronizada offline). Sem caixa aberto, não faz nada — abrir caixa não
    é obrigatório pra vender."""
    caixa = caixa_aberto(db, empresa_id)
    if caixa is None:
        return

    for pagamento in pagamentos:
        db.add(
            LancamentoCaixa(
                caixa_id=caixa.id,
                tipo=TipoLancamento.ENTRADA,
                origem=OrigemLancamento.VENDA,
                forma_pagamento=pagamento["forma"],
                valor=to_money(pagamento["valor"]),
                venda_id=venda_id,
                usuario_id=usuario_id,
                ocorrido_em=ocorrido_em,
            )
        )
    db.flush()


def listar_lancamentos(db: Session, caixa_id: uuid.UUID) -> list[LancamentoCaixa]:
    return repository.lancamentos_do_caixa(db, caixa_id)


def resumo_caixa(db: Session, caixa: CaixaSessao) -> ResumoCaixa:
    lancamentos = repository.lancamentos_do_caixa(db, caixa.id)

    total_entradas = Decimal("0")
    total_saidas = Decimal("0")
    dinheiro_entradas = Decimal("0")
    dinheiro_saidas = Decimal("0")

    for lancamento in lancamentos:
        if lancamento.tipo is TipoLancamento.ENTRADA:
            total_entradas += lancamento.valor
            if lancamento.forma_pagamento is FormaPagamento.DINHEIRO:
                dinheiro_entradas += lancamento.valor
        else:
            total_saidas += lancamento.valor
            if lancamento.forma_pagamento is FormaPagamento.DINHEIRO:
                dinheiro_saidas += lancamento.valor

    saldo_esperado_dinheiro = to_money(caixa.valor_inicial + dinheiro_entradas - dinheiro_saidas)
    diferenca = None
    if caixa.status is StatusCaixa.FECHADO and caixa.valor_contado is not None:
        diferenca = to_money(caixa.valor_contado - saldo_esperado_dinheiro)

    return ResumoCaixa(
        total_entradas=to_money(total_entradas),
        total_saidas=to_money(total_saidas),
        saldo_esperado_dinheiro=saldo_esperado_dinheiro,
        diferenca=diferenca,
    )


# --- Contas a pagar e a receber (Pro) -----------------------------------

_BRASILIA = timezone(timedelta(hours=-3))


def hoje() -> date:
    """Data de hoje no horário de Brasília (o servidor roda em UTC)."""
    return datetime.now(_BRASILIA).date()


def criar_conta(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    usuario_id: uuid.UUID,
    tipo: TipoConta,
    descricao: str,
    valor: Decimal,
    vencimento: date,
    contraparte: str | None = None,
) -> ContaFinanceira:
    descricao = descricao.strip()
    if not descricao:
        raise RegraDeNegocio("Informe a descrição da conta.")
    if valor <= 0:
        raise RegraDeNegocio("O valor da conta precisa ser maior que zero.")

    conta = ContaFinanceira(
        tipo=tipo,
        status=StatusConta.ABERTA,
        descricao=descricao,
        contraparte=(contraparte or "").strip() or None,
        valor=to_money(valor),
        vencimento=vencimento,
        criado_por_usuario_id=usuario_id,
    )
    return ContaRepositorio(db, empresa_id).adicionar(conta)


def _conta_aberta_ou_erro(
    db: Session, empresa_id: uuid.UUID, conta_id: uuid.UUID
) -> ContaFinanceira:
    conta = ContaRepositorio(db, empresa_id).obter_ou_erro(conta_id)
    if conta.status is not StatusConta.ABERTA:
        raise RegraDeNegocio("Só é possível alterar uma conta em aberto.")
    return conta


def marcar_paga(
    db: Session,
    empresa_id: uuid.UUID,
    conta_id: uuid.UUID,
    *,
    pago_em: date | None = None,
    forma_pagamento: FormaPagamento | None = None,
) -> ContaFinanceira:
    conta = _conta_aberta_ou_erro(db, empresa_id, conta_id)
    conta.status = StatusConta.PAGA
    conta.pago_em = pago_em or hoje()
    conta.forma_pagamento = forma_pagamento
    db.flush()
    return conta


def cancelar_conta(db: Session, empresa_id: uuid.UUID, conta_id: uuid.UUID) -> ContaFinanceira:
    conta = _conta_aberta_ou_erro(db, empresa_id, conta_id)
    conta.status = StatusConta.CANCELADA
    db.flush()
    return conta


def obter_conta(db: Session, empresa_id: uuid.UUID, conta_id: uuid.UUID) -> ContaFinanceira:
    return ContaRepositorio(db, empresa_id).obter_ou_erro(conta_id)


def listar_contas(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    tipo: TipoConta | None = None,
    status: StatusConta | None = None,
    limite: int = 100,
    deslocamento: int = 0,
) -> list[ContaFinanceira]:
    return ContaRepositorio(db, empresa_id).buscar(
        tipo=tipo, status=status, limite=limite, deslocamento=deslocamento
    )


@dataclass
class DiaProjetado:
    data: date
    a_receber: Decimal
    a_pagar: Decimal
    saldo_acumulado: Decimal


@dataclass
class FluxoProjetado:
    atrasadas_a_receber: Decimal
    atrasadas_a_pagar: Decimal
    dias: list[DiaProjetado]


def fluxo_projetado(
    db: Session, empresa_id: uuid.UUID, *, dias: int = 30, a_partir_de: date | None = None
) -> FluxoProjetado:
    """Projeção diária só com contas em aberto. Não parte de um saldo
    inicial (o caixa é por sessão, não um saldo corrente): o acumulado é o
    resultado líquido das contas. Contas já vencidas ficam à parte e entram
    no acumulado do primeiro dia, como se fossem liquidadas hoje."""
    if not 1 <= dias <= 365:
        raise RegraDeNegocio("O período da projeção deve ficar entre 1 e 365 dias.")

    inicio = a_partir_de or hoje()
    fim = inicio + timedelta(days=dias - 1)
    contas = ContaRepositorio(db, empresa_id).abertas_ate(fim)

    zero = Decimal("0.00")
    atrasadas_receber = atrasadas_pagar = zero
    por_dia: dict[date, list[Decimal]] = {}
    for conta in contas:
        if conta.vencimento < inicio:
            if conta.tipo is TipoConta.RECEBER:
                atrasadas_receber += conta.valor
            else:
                atrasadas_pagar += conta.valor
            continue
        totais = por_dia.setdefault(conta.vencimento, [zero, zero])
        totais[0 if conta.tipo is TipoConta.RECEBER else 1] += conta.valor

    acumulado = atrasadas_receber - atrasadas_pagar
    resultado: list[DiaProjetado] = []
    for deslocamento in range(dias):
        dia = inicio + timedelta(days=deslocamento)
        receber, pagar = por_dia.get(dia, [zero, zero])
        acumulado += receber - pagar
        resultado.append(DiaProjetado(dia, receber, pagar, acumulado))
    return FluxoProjetado(atrasadas_receber, atrasadas_pagar, resultado)

"""Rotas do caixa do dia."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import PermissaoNegada
from app.modules.assinaturas.regras import Recurso
from app.modules.auth.dependencias import Contexto, requer_permissao, requer_recurso
from app.modules.financeiro import service
from app.modules.usuarios import service as usuarios_service
from app.modules.financeiro.models import (
    CaixaSessao,
    ContaFinanceira,
    StatusConta,
    TipoConta,
)
from app.modules.financeiro.schemas import (
    AbrirCaixaEntrada,
    BaixaContaEntrada,
    CaixaSaida,
    ContaEntrada,
    ContaSaida,
    FecharCaixaEntrada,
    FluxoProjetadoSaida,
    LancamentoEntrada,
    LancamentoSaida,
    ResumoCaixaSaida,
    SincronizarLancamentoEntrada,
)

router = APIRouter(tags=["financeiro"])


def _exigir(contexto: Contexto, permissao: str) -> None:
    if permissao not in contexto.permissoes:
        raise PermissaoNegada("Você não tem permissão para esta ação.")


def _nome_do_usuario(db: Session, usuario_id: uuid.UUID | None) -> str | None:
    if usuario_id is None:
        return None
    usuario = usuarios_service.por_id(db, usuario_id)
    return usuario.nome if usuario else None


def _saida(db: Session, caixa: CaixaSessao) -> CaixaSaida:
    lancamentos = service.listar_lancamentos(db, caixa.id)
    resumo = service.resumo_caixa(db, caixa)
    return CaixaSaida(
        id=caixa.id,
        status=caixa.status,
        valor_inicial=caixa.valor_inicial,
        valor_contado=caixa.valor_contado,
        observacao=caixa.observacao,
        aberto_por_usuario_id=caixa.aberto_por_usuario_id,
        aberto_por_nome=_nome_do_usuario(db, caixa.aberto_por_usuario_id),
        fechado_por_usuario_id=caixa.fechado_por_usuario_id,
        fechado_por_nome=_nome_do_usuario(db, caixa.fechado_por_usuario_id),
        aberto_em=caixa.aberto_em,
        fechado_em=caixa.fechado_em,
        resumo=ResumoCaixaSaida(
            total_entradas=resumo.total_entradas,
            total_saidas=resumo.total_saidas,
            saldo_esperado_dinheiro=resumo.saldo_esperado_dinheiro,
            diferenca=resumo.diferenca,
        ),
        lancamentos=[LancamentoSaida.model_validate(item) for item in lancamentos],
    )


@router.get("/caixa/aberto", response_model=CaixaSaida | None)
def obter_caixa_aberto(
    contexto: Contexto = Depends(requer_permissao("financeiro.ver")),
    db: Session = Depends(get_db),
):
    caixa = service.caixa_aberto(db, contexto.empresa_id)
    if caixa is None:
        return None
    return _saida(db, caixa)


@router.get("/caixa", response_model=list[CaixaSaida])
def listar_caixas(
    limite: int = Query(default=50, ge=1, le=200),
    deslocamento: int = Query(default=0, ge=0),
    contexto: Contexto = Depends(requer_permissao("financeiro.ver")),
    db: Session = Depends(get_db),
):
    caixas = service.listar_caixas(db, contexto.empresa_id, limite=limite, deslocamento=deslocamento)
    return [_saida(db, caixa) for caixa in caixas]


@router.post("/caixa/abrir", response_model=CaixaSaida, status_code=status.HTTP_201_CREATED)
def abrir_caixa(
    dados: AbrirCaixaEntrada,
    contexto: Contexto = Depends(requer_permissao("financeiro.operar")),
    db: Session = Depends(get_db),
):
    caixa = service.abrir_caixa(
        db,
        contexto.empresa_id,
        usuario_id=contexto.usuario_id,
        valor_inicial=dados.valor_inicial,
        observacao=dados.observacao,
    )
    db.commit()
    return _saida(db, caixa)


@router.get("/caixa/{caixa_id}", response_model=CaixaSaida)
def obter_caixa(
    caixa_id: uuid.UUID,
    contexto: Contexto = Depends(requer_permissao("financeiro.ver")),
    db: Session = Depends(get_db),
):
    caixa = service.obter_caixa(db, contexto.empresa_id, caixa_id)
    return _saida(db, caixa)


@router.post("/caixa/{caixa_id}/fechar", response_model=CaixaSaida)
def fechar_caixa(
    caixa_id: uuid.UUID,
    dados: FecharCaixaEntrada,
    contexto: Contexto = Depends(requer_permissao("financeiro.operar")),
    db: Session = Depends(get_db),
):
    caixa = service.fechar_caixa(
        db,
        contexto.empresa_id,
        caixa_id,
        usuario_id=contexto.usuario_id,
        valor_contado=dados.valor_contado,
        observacao=dados.observacao,
    )
    db.commit()
    return _saida(db, caixa)


@router.post(
    "/caixa/{caixa_id}/lancamentos",
    response_model=CaixaSaida,
    status_code=status.HTTP_201_CREATED,
)
def lancar_manual(
    caixa_id: uuid.UUID,
    dados: LancamentoEntrada,
    contexto: Contexto = Depends(requer_permissao("financeiro.operar")),
    db: Session = Depends(get_db),
):
    service.lancar_manual(
        db,
        contexto.empresa_id,
        caixa_id,
        usuario_id=contexto.usuario_id,
        tipo=dados.tipo,
        valor=dados.valor,
        forma_pagamento=dados.forma_pagamento,
        descricao=dados.descricao,
    )
    db.commit()
    caixa = service.obter_caixa(db, contexto.empresa_id, caixa_id)
    return _saida(db, caixa)


@router.post(
    "/caixa/lancamentos/sincronizar",
    response_model=LancamentoSaida,
    status_code=status.HTTP_201_CREATED,
)
def sincronizar_lancamento_offline(
    dados: SincronizarLancamentoEntrada,
    contexto: Contexto = Depends(requer_permissao("financeiro.operar")),
    db: Session = Depends(get_db),
):
    lancamento = service.sincronizar_lancamento_offline(
        db,
        contexto.empresa_id,
        id=dados.id,
        usuario_id=contexto.usuario_id,
        tipo=dados.tipo,
        valor=dados.valor,
        forma_pagamento=dados.forma_pagamento,
        descricao=dados.descricao,
        ocorrido_em=dados.ocorrido_em,
    )
    db.commit()
    return lancamento


# --- Contas a pagar e a receber (Pro) -----------------------------------


def _conta_saida(conta: ContaFinanceira) -> ContaSaida:
    saida = ContaSaida.model_validate(conta)
    saida.vencida = conta.status is StatusConta.ABERTA and conta.vencimento < service.hoje()
    return saida


@router.get("/contas/fluxo-projetado", response_model=FluxoProjetadoSaida)
def fluxo_projetado(
    dias: int = Query(default=30, ge=1, le=365),
    contexto: Contexto = Depends(requer_recurso(Recurso.CONTAS_PAGAR_RECEBER)),
    db: Session = Depends(get_db),
):
    _exigir(contexto, "financeiro.ver")
    return service.fluxo_projetado(db, contexto.empresa_id, dias=dias)


@router.get("/contas", response_model=list[ContaSaida])
def listar_contas(
    tipo: TipoConta | None = None,
    status: StatusConta | None = None,
    limite: int = Query(default=100, ge=1, le=200),
    deslocamento: int = Query(default=0, ge=0),
    contexto: Contexto = Depends(requer_recurso(Recurso.CONTAS_PAGAR_RECEBER)),
    db: Session = Depends(get_db),
):
    _exigir(contexto, "financeiro.ver")
    contas = service.listar_contas(
        db, contexto.empresa_id, tipo=tipo, status=status, limite=limite, deslocamento=deslocamento
    )
    return [_conta_saida(conta) for conta in contas]


@router.post("/contas", response_model=ContaSaida, status_code=201)
def criar_conta(
    dados: ContaEntrada,
    contexto: Contexto = Depends(requer_recurso(Recurso.CONTAS_PAGAR_RECEBER)),
    db: Session = Depends(get_db),
):
    _exigir(contexto, "financeiro.operar")
    conta = service.criar_conta(
        db,
        contexto.empresa_id,
        usuario_id=contexto.usuario_id,
        tipo=dados.tipo,
        descricao=dados.descricao,
        valor=dados.valor,
        vencimento=dados.vencimento,
        contraparte=dados.contraparte,
    )
    db.commit()
    return _conta_saida(conta)


@router.post("/contas/{conta_id}/baixa", response_model=ContaSaida)
def dar_baixa(
    conta_id: uuid.UUID,
    dados: BaixaContaEntrada,
    contexto: Contexto = Depends(requer_recurso(Recurso.CONTAS_PAGAR_RECEBER)),
    db: Session = Depends(get_db),
):
    _exigir(contexto, "financeiro.operar")
    conta = service.marcar_paga(
        db,
        contexto.empresa_id,
        conta_id,
        pago_em=dados.pago_em,
        forma_pagamento=dados.forma_pagamento,
    )
    db.commit()
    return _conta_saida(conta)


@router.post("/contas/{conta_id}/cancelar", response_model=ContaSaida)
def cancelar_conta(
    conta_id: uuid.UUID,
    contexto: Contexto = Depends(requer_recurso(Recurso.CONTAS_PAGAR_RECEBER)),
    db: Session = Depends(get_db),
):
    _exigir(contexto, "financeiro.operar")
    conta = service.cancelar_conta(db, contexto.empresa_id, conta_id)
    db.commit()
    return _conta_saida(conta)

"""Rotas de estoque: saldo, movimentos, entradas, saídas, ajustes e reservas."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import PermissaoNegada
from app.modules.assinaturas.regras import Recurso
from app.modules.auth.dependencias import Contexto, requer_permissao, requer_recurso
from app.modules.estoque import service
from app.modules.estoque.models import TipoMovimento
from app.modules.estoque.schemas import (
    AjusteEntrada,
    AlertaEstoqueSaida,
    EntradaEntrada,
    MovimentoSaida,
    ReservaEntrada,
    SaidaEntrada,
    SaldoComProdutoSaida,
    SaldoSaida,
)

router = APIRouter(prefix="/estoque", tags=["estoque"])


@router.get("/saldos", response_model=list[SaldoComProdutoSaida])
def listar_saldos(
    termo: str | None = Query(default=None, max_length=60),
    limite: int = Query(default=50, ge=1, le=200),
    deslocamento: int = Query(default=0, ge=0),
    contexto: Contexto = Depends(requer_permissao("estoque.ver")),
    db: Session = Depends(get_db),
):
    saldos = service.listar_saldos(
        db, contexto.empresa_id, termo=termo, limite=limite, deslocamento=deslocamento
    )
    return [
        SaldoComProdutoSaida(
            produto_id=item.produto.id,
            nome=item.produto.nome,
            sku=item.produto.sku,
            unidade_codigo=item.produto.unidade_codigo,
            fisico=item.fisico,
            reservado=item.reservado,
            disponivel=item.disponivel,
        )
        for item in saldos
    ]


@router.get("/alertas", response_model=list[AlertaEstoqueSaida])
def alertas_de_estoque(
    contexto: Contexto = Depends(requer_recurso(Recurso.ALERTAS)),
    db: Session = Depends(get_db),
):
    """Estoque negativo e abaixo do mínimo (Pro)."""
    if "estoque.ver" not in contexto.permissoes:
        raise PermissaoNegada("Você não tem permissão para esta ação.")
    return [
        AlertaEstoqueSaida(
            produto_id=item.produto.id,
            nome=item.produto.nome,
            sku=item.produto.sku,
            unidade_codigo=item.produto.unidade_codigo,
            tipo=item.tipo,
            fisico=item.fisico,
            disponivel=item.disponivel,
            estoque_minimo=item.estoque_minimo,
        )
        for item in service.alertas_de_estoque(db, contexto.empresa_id)
    ]


@router.get("/produtos/{produto_id}/saldo", response_model=SaldoSaida)
def obter_saldo(
    produto_id: uuid.UUID,
    contexto: Contexto = Depends(requer_permissao("estoque.ver")),
    db: Session = Depends(get_db),
):
    saldo = service.obter_saldo(db, contexto.empresa_id, produto_id)
    return SaldoSaida(
        produto_id=saldo.produto_id,
        fisico=saldo.fisico,
        reservado=saldo.reservado,
        disponivel=saldo.disponivel,
    )


@router.get("/movimentos", response_model=list[MovimentoSaida])
def listar_movimentos(
    produto_id: uuid.UUID | None = None,
    tipo: TipoMovimento | None = None,
    limite: int = Query(default=50, ge=1, le=200),
    deslocamento: int = Query(default=0, ge=0),
    contexto: Contexto = Depends(requer_permissao("estoque.ver")),
    db: Session = Depends(get_db),
):
    return service.listar_movimentos(
        db,
        contexto.empresa_id,
        produto_id=produto_id,
        tipo=tipo,
        limite=limite,
        deslocamento=deslocamento,
    )


@router.post(
    "/produtos/{produto_id}/entradas",
    response_model=MovimentoSaida,
    status_code=status.HTTP_201_CREATED,
)
def registrar_entrada(
    produto_id: uuid.UUID,
    dados: EntradaEntrada,
    contexto: Contexto = Depends(requer_permissao("estoque.movimentar")),
    db: Session = Depends(get_db),
):
    movimento = service.registrar_entrada(db, contexto.empresa_id, produto_id, **dados.model_dump())
    db.commit()
    return movimento


@router.post(
    "/produtos/{produto_id}/saidas",
    response_model=MovimentoSaida,
    status_code=status.HTTP_201_CREATED,
)
def registrar_saida(
    produto_id: uuid.UUID,
    dados: SaidaEntrada,
    contexto: Contexto = Depends(requer_permissao("estoque.movimentar")),
    db: Session = Depends(get_db),
):
    movimento = service.registrar_saida(db, contexto.empresa_id, produto_id, **dados.model_dump())
    db.commit()
    return movimento


@router.post(
    "/produtos/{produto_id}/ajustes",
    response_model=MovimentoSaida | None,
    status_code=status.HTTP_200_OK,
)
def registrar_ajuste(
    produto_id: uuid.UUID,
    dados: AjusteEntrada,
    contexto: Contexto = Depends(requer_permissao("estoque.ajustar")),
    db: Session = Depends(get_db),
):
    movimento = service.registrar_ajuste(db, contexto.empresa_id, produto_id, **dados.model_dump())
    db.commit()
    return movimento


@router.post(
    "/produtos/{produto_id}/reservas",
    response_model=MovimentoSaida,
    status_code=status.HTTP_201_CREATED,
)
def reservar(
    produto_id: uuid.UUID,
    dados: ReservaEntrada,
    contexto: Contexto = Depends(requer_permissao("estoque.movimentar")),
    db: Session = Depends(get_db),
):
    movimento = service.reservar(db, contexto.empresa_id, produto_id, **dados.model_dump())
    db.commit()
    return movimento


@router.post(
    "/produtos/{produto_id}/reservas/liberar",
    response_model=MovimentoSaida,
    status_code=status.HTTP_201_CREATED,
)
def liberar_reserva(
    produto_id: uuid.UUID,
    dados: ReservaEntrada,
    contexto: Contexto = Depends(requer_permissao("estoque.movimentar")),
    db: Session = Depends(get_db),
):
    movimento = service.liberar_reserva(db, contexto.empresa_id, produto_id, **dados.model_dump())
    db.commit()
    return movimento

"""Rotas de vendas."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencias import Contexto, requer_permissao
from app.modules.vendas import service
from app.modules.vendas.models import StatusVenda, Venda
from app.modules.vendas.schemas import (
    AbrirVendaEntrada,
    AtualizarClienteEntrada,
    FecharVendaEntrada,
    ItemVendaEntrada,
    ItemVendaSaida,
    PagamentoSaida,
    SincronizarVendaEntrada,
    VendaSaida,
)

router = APIRouter(tags=["vendas"])

PERMISSAO_DESCONTO_LIVRE = "vendas.desconto_acima_limite"


def _saida(db: Session, venda: Venda) -> VendaSaida:
    itens = service.itens_da_venda(db, venda.id)
    pagamentos = service.pagamentos_da_venda(db, venda.id)
    return VendaSaida(
        id=venda.id,
        numero=venda.numero,
        cliente_id=venda.cliente_id,
        vendedor_usuario_id=venda.vendedor_usuario_id,
        canal=venda.canal,
        status=venda.status,
        subtotal=venda.subtotal,
        desconto_total=venda.desconto_total,
        total=venda.total,
        ocorrido_em=venda.ocorrido_em,
        fechado_em=venda.fechado_em,
        cancelado_em=venda.cancelado_em,
        itens=[ItemVendaSaida.model_validate(item) for item in itens],
        pagamentos=[PagamentoSaida.model_validate(pagamento) for pagamento in pagamentos],
    )


@router.get("/vendas", response_model=list[VendaSaida])
def listar_vendas(
    status_venda: StatusVenda | None = Query(default=None, alias="status"),
    cliente_id: uuid.UUID | None = None,
    limite: int = Query(default=50, ge=1, le=200),
    deslocamento: int = Query(default=0, ge=0),
    contexto: Contexto = Depends(requer_permissao("vendas.ver")),
    db: Session = Depends(get_db),
):
    vendas = service.listar_vendas(
        db,
        contexto.empresa_id,
        status=status_venda,
        cliente_id=cliente_id,
        limite=limite,
        deslocamento=deslocamento,
    )
    return [_saida(db, venda) for venda in vendas]


@router.post("/vendas", response_model=VendaSaida, status_code=status.HTTP_201_CREATED)
def abrir_venda(
    dados: AbrirVendaEntrada,
    contexto: Contexto = Depends(requer_permissao("vendas.registrar")),
    db: Session = Depends(get_db),
):
    venda = service.abrir_venda(
        db,
        contexto.empresa_id,
        vendedor_usuario_id=contexto.usuario_id,
        cliente_id=dados.cliente_id,
        cliente_novo=dados.cliente_novo.model_dump() if dados.cliente_novo else None,
        ocorrido_em=dados.ocorrido_em,
        id=dados.id,
    )
    db.commit()
    return _saida(db, venda)


@router.post(
    "/vendas/sincronizar", response_model=VendaSaida, status_code=status.HTTP_201_CREATED
)
def sincronizar_venda_offline(
    dados: SincronizarVendaEntrada,
    contexto: Contexto = Depends(requer_permissao("vendas.registrar")),
    db: Session = Depends(get_db),
):
    venda = service.sincronizar_venda_offline(
        db,
        contexto.empresa_id,
        id=dados.id,
        vendedor_usuario_id=contexto.usuario_id,
        cliente_id=dados.cliente_id,
        cliente_novo=dados.cliente_novo.model_dump() if dados.cliente_novo else None,
        itens=[item.model_dump() for item in dados.itens],
        pagamentos=[pagamento.model_dump() for pagamento in dados.pagamentos],
        ocorrido_em=dados.ocorrido_em,
        limite_desconto_percentual=contexto.limite_desconto_percentual,
        pode_exceder_limite=PERMISSAO_DESCONTO_LIVRE in contexto.permissoes,
    )
    db.commit()
    return _saida(db, venda)


@router.get("/vendas/{venda_id}", response_model=VendaSaida)
def obter_venda(
    venda_id: uuid.UUID,
    contexto: Contexto = Depends(requer_permissao("vendas.ver")),
    db: Session = Depends(get_db),
):
    venda = service.obter_venda(db, contexto.empresa_id, venda_id)
    return _saida(db, venda)


@router.patch("/vendas/{venda_id}/cliente", response_model=VendaSaida)
def atualizar_cliente_da_venda(
    venda_id: uuid.UUID,
    dados: AtualizarClienteEntrada,
    contexto: Contexto = Depends(requer_permissao("vendas.registrar")),
    db: Session = Depends(get_db),
):
    venda = service.atualizar_cliente_da_venda(
        db,
        contexto.empresa_id,
        venda_id,
        cliente_id=dados.cliente_id,
        cliente_novo=dados.cliente_novo.model_dump() if dados.cliente_novo else None,
    )
    db.commit()
    return _saida(db, venda)


@router.post(
    "/vendas/{venda_id}/itens", response_model=VendaSaida, status_code=status.HTTP_201_CREATED
)
def adicionar_item(
    venda_id: uuid.UUID,
    dados: ItemVendaEntrada,
    contexto: Contexto = Depends(requer_permissao("vendas.registrar")),
    db: Session = Depends(get_db),
):
    service.adicionar_item(
        db,
        contexto.empresa_id,
        venda_id,
        produto_id=dados.produto_id,
        quantidade=dados.quantidade,
        unidade_id=dados.unidade_id,
        desconto_percentual=dados.desconto_percentual,
        limite_desconto_percentual=contexto.limite_desconto_percentual,
        pode_exceder_limite=PERMISSAO_DESCONTO_LIVRE in contexto.permissoes,
    )
    db.commit()
    venda = service.obter_venda(db, contexto.empresa_id, venda_id)
    return _saida(db, venda)


@router.delete("/vendas/{venda_id}/itens/{item_id}", response_model=VendaSaida)
def remover_item(
    venda_id: uuid.UUID,
    item_id: uuid.UUID,
    contexto: Contexto = Depends(requer_permissao("vendas.registrar")),
    db: Session = Depends(get_db),
):
    service.remover_item(db, contexto.empresa_id, venda_id, item_id)
    db.commit()
    venda = service.obter_venda(db, contexto.empresa_id, venda_id)
    return _saida(db, venda)


@router.post("/vendas/{venda_id}/fechar", response_model=VendaSaida)
def fechar_venda(
    venda_id: uuid.UUID,
    dados: FecharVendaEntrada,
    contexto: Contexto = Depends(requer_permissao("vendas.registrar")),
    db: Session = Depends(get_db),
):
    venda = service.fechar_venda(
        db,
        contexto.empresa_id,
        venda_id,
        pagamentos=[pagamento.model_dump() for pagamento in dados.pagamentos],
    )
    db.commit()
    return _saida(db, venda)


@router.post("/vendas/{venda_id}/cancelar", response_model=VendaSaida)
def cancelar_venda(
    venda_id: uuid.UUID,
    contexto: Contexto = Depends(requer_permissao("vendas.registrar")),
    db: Session = Depends(get_db),
):
    venda = service.cancelar_venda(
        db,
        contexto.empresa_id,
        venda_id,
        pode_cancelar_fechada="vendas.cancelar" in contexto.permissoes,
    )
    db.commit()
    return _saida(db, venda)

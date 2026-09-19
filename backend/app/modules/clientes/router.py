"""Rotas de clientes."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencias import Contexto, requer_permissao
from app.modules.clientes import service
from app.modules.clientes.schemas import (
    ClienteAtualizacao,
    ClienteEntrada,
    ClienteSaida,
    CompraExportada,
    ExportacaoClienteSaida,
    MesclarClientesEntrada,
    MetricasClienteSaida,
)
from app.modules.vendas import service as vendas_service

router = APIRouter(tags=["clientes"])


@router.get("/clientes", response_model=list[ClienteSaida])
def listar_clientes(
    termo: str | None = Query(default=None, max_length=60),
    limite: int = Query(default=50, ge=1, le=200),
    deslocamento: int = Query(default=0, ge=0),
    contexto: Contexto = Depends(requer_permissao("clientes.ver")),
    db: Session = Depends(get_db),
):
    return service.listar_clientes(
        db, contexto.empresa_id, termo=termo, limite=limite, deslocamento=deslocamento
    )


@router.post("/clientes", response_model=ClienteSaida, status_code=status.HTTP_201_CREATED)
def criar_cliente(
    dados: ClienteEntrada,
    contexto: Contexto = Depends(requer_permissao("clientes.editar")),
    db: Session = Depends(get_db),
):
    cliente = service.criar_cliente(db, contexto.empresa_id, **dados.model_dump())
    db.commit()
    return cliente


@router.get("/clientes/{cliente_id}", response_model=ClienteSaida)
def obter_cliente(
    cliente_id: uuid.UUID,
    contexto: Contexto = Depends(requer_permissao("clientes.ver")),
    db: Session = Depends(get_db),
):
    return service.obter_cliente(db, contexto.empresa_id, cliente_id)


@router.patch("/clientes/{cliente_id}", response_model=ClienteSaida)
def atualizar_cliente(
    cliente_id: uuid.UUID,
    dados: ClienteAtualizacao,
    contexto: Contexto = Depends(requer_permissao("clientes.editar")),
    db: Session = Depends(get_db),
):
    cliente = service.atualizar_cliente(
        db, contexto.empresa_id, cliente_id, dados.model_dump(exclude_unset=True)
    )
    db.commit()
    return cliente


@router.get("/clientes/{cliente_id}/metricas", response_model=MetricasClienteSaida)
def obter_metricas_do_cliente(
    cliente_id: uuid.UUID,
    contexto: Contexto = Depends(requer_permissao("clientes.ver")),
    db: Session = Depends(get_db),
):
    service.obter_cliente(db, contexto.empresa_id, cliente_id)
    metricas = vendas_service.metricas_do_cliente(db, contexto.empresa_id, cliente_id)
    return MetricasClienteSaida(**metricas.__dict__)


@router.get("/clientes/{cliente_id}/exportar", response_model=ExportacaoClienteSaida)
def exportar_dados_do_cliente(
    cliente_id: uuid.UUID,
    contexto: Contexto = Depends(requer_permissao("clientes.editar")),
    db: Session = Depends(get_db),
):
    cliente = service.obter_cliente(db, contexto.empresa_id, cliente_id)
    vendas = vendas_service.listar_vendas(
        db, contexto.empresa_id, cliente_id=cliente_id, limite=1000
    )
    return ExportacaoClienteSaida(
        id=cliente.id,
        nome=cliente.nome,
        telefone=cliente.telefone,
        email=cliente.email,
        cpf=cliente.cpf,
        data_nascimento=cliente.data_nascimento,
        endereco=cliente.endereco,
        consentimento_marketing=cliente.consentimento_marketing,
        consentimento_em=cliente.consentimento_em,
        origem=cliente.origem,
        compras=[
            CompraExportada(numero=venda.numero, ocorrido_em=venda.ocorrido_em, total=venda.total)
            for venda in vendas
        ],
    )


@router.post("/clientes/{cliente_id}/mesclar", response_model=ClienteSaida)
def mesclar_clientes(
    cliente_id: uuid.UUID,
    dados: MesclarClientesEntrada,
    contexto: Contexto = Depends(requer_permissao("clientes.editar")),
    db: Session = Depends(get_db),
):
    cliente = service.mesclar_clientes(
        db, contexto.empresa_id, cliente_id=cliente_id, duplicado_id=dados.duplicado_id
    )
    vendas_service.reatribuir_cliente(
        db, contexto.empresa_id, de_cliente_id=dados.duplicado_id, para_cliente_id=cliente_id
    )
    db.commit()
    return cliente


@router.post("/clientes/{cliente_id}/anonimizar", response_model=ClienteSaida)
def anonimizar_cliente(
    cliente_id: uuid.UUID,
    contexto: Contexto = Depends(requer_permissao("clientes.editar")),
    db: Session = Depends(get_db),
):
    cliente = service.anonimizar_cliente(db, contexto.empresa_id, cliente_id)
    db.commit()
    return cliente

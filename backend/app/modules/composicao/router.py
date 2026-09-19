"""Rotas de composição: componentes de kits e montagem."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencias import Contexto, requer_permissao
from app.modules.composicao import service
from app.modules.composicao.schemas import ComponenteEntrada, ComponenteSaida, MontagemEntrada
from app.modules.estoque.schemas import MovimentoSaida

router = APIRouter(tags=["composicao"])


@router.get("/produtos/{produto_id}/componentes", response_model=list[ComponenteSaida])
def listar_componentes(
    produto_id: uuid.UUID,
    contexto: Contexto = Depends(requer_permissao("produtos.ver")),
    db: Session = Depends(get_db),
):
    return service.listar_componentes(db, contexto.empresa_id, produto_id)


@router.post(
    "/produtos/{produto_id}/componentes",
    response_model=ComponenteSaida,
    status_code=status.HTTP_201_CREATED,
)
def adicionar_componente(
    produto_id: uuid.UUID,
    dados: ComponenteEntrada,
    contexto: Contexto = Depends(requer_permissao("produtos.editar")),
    db: Session = Depends(get_db),
):
    componente = service.adicionar_componente(db, contexto.empresa_id, produto_id, **dados.model_dump())
    db.commit()
    return componente


@router.delete("/produtos/{produto_id}/componentes/{componente_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_componente(
    produto_id: uuid.UUID,
    componente_id: uuid.UUID,
    contexto: Contexto = Depends(requer_permissao("produtos.editar")),
    db: Session = Depends(get_db),
):
    service.remover_componente(db, contexto.empresa_id, produto_id, componente_id)
    db.commit()


@router.post(
    "/produtos/{produto_id}/montagens",
    response_model=MovimentoSaida,
    status_code=status.HTTP_201_CREATED,
)
def montar(
    produto_id: uuid.UUID,
    dados: MontagemEntrada,
    contexto: Contexto = Depends(requer_permissao("estoque.movimentar")),
    db: Session = Depends(get_db),
):
    movimento = service.montar(db, contexto.empresa_id, produto_id, **dados.model_dump())
    db.commit()
    return movimento

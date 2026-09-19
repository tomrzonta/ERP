"""Regras de negócio de composição: componentes de um kit, e a montagem.

Kit tem saldo próprio de verdade, como qualquer produto com controle de
estoque. Montar dá baixa nos componentes (na quantidade exata, com a perda)
e credita o kit, pelo módulo de estoque — composição nunca mexe direto nas
tabelas de estoque nem de produtos.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import Conflito, NaoEncontrado, RegraDeNegocio
from app.modules.assinaturas import service as assinaturas_service
from app.modules.assinaturas.regras import Recurso
from app.modules.composicao.models import ComponenteComposto
from app.modules.composicao.repository import ComponenteRepositorio
from app.modules.estoque import service as estoque_service
from app.modules.estoque.models import MovimentoEstoque
from app.modules.produtos import service as produtos_service
from app.modules.produtos.models import TipoProduto
from app.shared.quantidade import to_custo, to_quantidade


def _cria_ciclo(
    db: Session, empresa_id: uuid.UUID, produto_composto_id: uuid.UUID, componente_id: uuid.UUID
) -> bool:
    """True se produto_composto_id já aparece, direta ou indiretamente, sob componente_id."""
    repo = ComponenteRepositorio(db, empresa_id)
    visitados: set[uuid.UUID] = set()
    pilha = [componente_id]
    while pilha:
        atual = pilha.pop()
        if atual == produto_composto_id:
            return True
        if atual in visitados:
            continue
        visitados.add(atual)
        pilha.extend(item.componente_id for item in repo.do_composto(atual))
    return False


def adicionar_componente(
    db: Session,
    empresa_id: uuid.UUID,
    produto_composto_id: uuid.UUID,
    *,
    componente_id: uuid.UUID,
    quantidade: Decimal,
    perda_percentual: Decimal = Decimal("0"),
) -> ComponenteComposto:
    if componente_id == produto_composto_id:
        raise RegraDeNegocio("Um produto não pode ser componente de si mesmo.")
    if quantidade <= 0:
        raise RegraDeNegocio("A quantidade do componente precisa ser maior que zero.")
    if perda_percentual < 0 or perda_percentual >= 100:
        raise RegraDeNegocio("A perda percentual precisa estar entre 0 e 100.")

    composto = produtos_service.obter_produto(db, empresa_id, produto_composto_id)
    if composto.tipo is not TipoProduto.KIT:
        raise RegraDeNegocio("Só um kit pode ter componentes.")

    componente = produtos_service.obter_produto(db, empresa_id, componente_id)

    if componente.tipo is not TipoProduto.SIMPLES:
        assinaturas_service.exigir_recurso(db, empresa_id, Recurso.COMPOSTO_ANINHADO)
        if _cria_ciclo(db, empresa_id, produto_composto_id, componente_id):
            raise RegraDeNegocio(
                "Essa composição criaria um ciclo: um produto dependendo dele mesmo."
            )

    if not componente.controla_estoque:
        raise RegraDeNegocio("O componente precisa controlar estoque.")

    if perda_percentual > 0:
        assinaturas_service.exigir_recurso(db, empresa_id, Recurso.PERDA_NA_COMPOSICAO)

    repo = ComponenteRepositorio(db, empresa_id)
    if repo.existente(produto_composto_id, componente_id) is not None:
        raise Conflito("Esse produto já é componente desta composição.")

    return repo.adicionar(
        ComponenteComposto(
            produto_composto_id=produto_composto_id,
            componente_id=componente_id,
            quantidade=to_quantidade(quantidade),
            perda_percentual=perda_percentual,
        )
    )


def remover_componente(
    db: Session, empresa_id: uuid.UUID, produto_composto_id: uuid.UUID, componente_id: uuid.UUID
) -> None:
    repo = ComponenteRepositorio(db, empresa_id)
    componente = repo.existente(produto_composto_id, componente_id)
    if componente is None:
        raise NaoEncontrado("Componente não encontrado nesta composição.")
    db.delete(componente)
    db.flush()


def listar_componentes(
    db: Session, empresa_id: uuid.UUID, produto_composto_id: uuid.UUID
) -> list[ComponenteComposto]:
    produtos_service.obter_produto(db, empresa_id, produto_composto_id)
    return ComponenteRepositorio(db, empresa_id).do_composto(produto_composto_id)


# --- montagem ---


def montar(
    db: Session,
    empresa_id: uuid.UUID,
    produto_kit_id: uuid.UUID,
    *,
    quantidade: Decimal,
    ocorrido_em: datetime | None = None,
    origem: str | None = None,
    id: uuid.UUID | None = None,
) -> MovimentoEstoque:
    if quantidade <= 0:
        raise RegraDeNegocio("A quantidade montada precisa ser maior que zero.")

    if id is not None:
        existente = estoque_service.obter_movimento(db, empresa_id, id)
        if existente is not None:
            return existente

    kit = produtos_service.obter_produto(db, empresa_id, produto_kit_id)
    if kit.tipo is not TipoProduto.KIT:
        raise RegraDeNegocio("Só um kit pode ser montado.")

    componentes = listar_componentes(db, empresa_id, produto_kit_id)
    if not componentes:
        raise RegraDeNegocio("Este kit não tem componentes cadastrados.")

    quantidade_montada = to_quantidade(quantidade)

    custo_total = Decimal("0")
    for item in componentes:
        consumo = to_quantidade(
            item.quantidade
            * quantidade_montada
            * (Decimal("1") + item.perda_percentual / Decimal("100"))
        )
        movimento_consumo = estoque_service.consumir_para_montagem(
            db, empresa_id, item.componente_id, quantidade=consumo
        )
        custo_total += consumo * (movimento_consumo.custo_unitario or Decimal("0"))

    custo_unitario_montagem = to_custo(custo_total / quantidade_montada)

    return estoque_service.produzir_por_montagem(
        db,
        empresa_id,
        produto_kit_id,
        quantidade=quantidade_montada,
        custo_unitario=custo_unitario_montagem,
        ocorrido_em=ocorrido_em,
        origem=origem,
        id=id,
    )

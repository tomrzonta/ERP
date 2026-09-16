"""Motor de planos: assinatura, plano efetivo, recursos e limites."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import LimiteDoPlano, RecursoDoPlano
from app.modules.assinaturas import repository
from app.modules.assinaturas.models import Assinatura, Plano, StatusAssinatura, TipoRegra
from app.modules.assinaturas.regras import (
    DIAS_TRIAL,
    PLANO_PRO,
    Limite,
    Recurso,
    codigo_plano_efetivo,
)


def _agora(agora: datetime | None) -> datetime:
    return agora or datetime.now(UTC)


def _plano_obrigatorio(db: Session, codigo: str) -> Plano:
    plano = repository.plano_por_codigo(db, codigo)
    if plano is None:
        raise RuntimeError(f"Plano '{codigo}' não cadastrado. As migrações foram aplicadas?")
    return plano


def criar_assinatura_trial(
    db: Session, empresa_id: uuid.UUID, agora: datetime | None = None
) -> Assinatura:
    """Empresa nova começa com o Pro em trial (teste reverso)."""
    inicio = _agora(agora)
    assinatura = Assinatura(
        empresa_id=empresa_id,
        plano_id=_plano_obrigatorio(db, PLANO_PRO).id,
        status=StatusAssinatura.TRIAL,
        trial_termina_em=inicio + timedelta(days=DIAS_TRIAL),
    )
    db.add(assinatura)
    db.flush()
    return assinatura


def plano_efetivo(db: Session, empresa_id: uuid.UUID, agora: datetime | None = None) -> Plano:
    assinatura = repository.assinatura_da_empresa(db, empresa_id)
    if assinatura is None:
        raise RuntimeError(f"Empresa {empresa_id} sem assinatura.")

    contratado = repository.plano_por_id(db, assinatura.plano_id)
    codigo = codigo_plano_efetivo(
        status=assinatura.status,
        codigo_contratado=contratado.codigo,
        agora=_agora(agora),
        trial_termina_em=assinatura.trial_termina_em,
        periodo_atual_termina_em=assinatura.periodo_atual_termina_em,
        carencia_termina_em=assinatura.carencia_termina_em,
    )
    return contratado if codigo == contratado.codigo else _plano_obrigatorio(db, codigo)


def tem_recurso(
    db: Session, empresa_id: uuid.UUID, recurso: Recurso, agora: datetime | None = None
) -> bool:
    plano = plano_efetivo(db, empresa_id, agora)
    regra = repository.regra(db, plano.id, recurso.value)
    return regra is not None and regra.tipo == TipoRegra.RECURSO


def exigir_recurso(
    db: Session, empresa_id: uuid.UUID, recurso: Recurso, agora: datetime | None = None
) -> None:
    if not tem_recurso(db, empresa_id, recurso, agora):
        raise RecursoDoPlano(f"Recurso não incluído no seu plano: {recurso.value}.")


def valor_do_limite(
    db: Session, empresa_id: uuid.UUID, limite: Limite, agora: datetime | None = None
) -> int | None:
    """Valor do limite no plano efetivo. None significa ilimitado."""
    plano = plano_efetivo(db, empresa_id, agora)
    regra = repository.regra(db, plano.id, limite.value)
    if regra is None or regra.tipo != TipoRegra.LIMITE:
        # Todo limite precisa estar cadastrado em todo plano
        raise RuntimeError(f"Limite '{limite.value}' não cadastrado no plano '{plano.codigo}'.")
    return regra.valor


def verificar_limite(
    db: Session,
    empresa_id: uuid.UUID,
    limite: Limite,
    uso_atual: int,
    agora: datetime | None = None,
) -> None:
    """Impede criar mais um item quando o uso atual já atingiu o limite."""
    valor = valor_do_limite(db, empresa_id, limite, agora)
    if valor is not None and uso_atual >= valor:
        raise LimiteDoPlano(f"Limite do plano atingido: {limite.value} ({valor}).")

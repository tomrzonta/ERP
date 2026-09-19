"""Catálogo de recursos e limites, e a regra de plano efetivo.

Recursos e limites são enums para evitar erros de digitação: o código
nunca pergunta por uma string solta como "cupons".
"""

from datetime import datetime
from enum import StrEnum

from app.modules.assinaturas.models import StatusAssinatura

PLANO_BASE = "base"
PLANO_PRO = "pro"
DIAS_TRIAL = 14


class Recurso(StrEnum):
    CUSTOS_ADICIONAIS = "custos_adicionais"
    COMPOSTO_ANINHADO = "composto_aninhado"
    PAPEIS_EDITAVEIS = "papeis_editaveis"
    MARGEM_AVANCADA = "margem_avancada"
    ALERTAS = "alertas"
    MARKETPLACES = "marketplaces"
    DOMINIO_PROPRIO = "dominio_proprio"
    MARGEM_POR_CANAL = "margem_por_canal"
    CUPONS = "cupons"
    FIDELIDADE = "fidelidade"
    SEGMENTACAO_CLIENTES = "segmentacao_clientes"
    PERDA_NA_COMPOSICAO = "perda_na_composicao"
    CONTAS_PAGAR_RECEBER = "contas_pagar_receber"
    RELATORIOS_CLIENTES = "relatorios_clientes"
    EXPORTACAO_RELATORIOS = "exportacao_relatorios"


class Limite(StrEnum):
    MAX_PRODUTOS_SIMPLES = "max_produtos_simples"
    MAX_COMPOSTOS = "max_compostos"
    MAX_USUARIOS = "max_usuarios"
    MAX_CAIXAS_OFFLINE = "max_caixas_offline"
    MAX_PRODUTOS_VITRINE = "max_produtos_vitrine"


def codigo_plano_efetivo(
    *,
    status: StatusAssinatura,
    codigo_contratado: str,
    agora: datetime,
    trial_termina_em: datetime | None,
    periodo_atual_termina_em: datetime | None,
    carencia_termina_em: datetime | None,
) -> str:
    """Qual plano vale neste momento, considerando trial, carência e cancelamento."""
    if status == StatusAssinatura.TRIAL:
        if trial_termina_em and agora < trial_termina_em:
            return PLANO_PRO
        return PLANO_BASE

    if status == StatusAssinatura.ATIVA:
        return codigo_contratado

    if status == StatusAssinatura.INADIMPLENTE:
        if carencia_termina_em and agora < carencia_termina_em:
            return codigo_contratado
        return PLANO_BASE

    # Cancelada: vale o que foi pago até o fim do período
    if periodo_atual_termina_em and agora < periodo_atual_termina_em:
        return codigo_contratado
    return PLANO_BASE

from datetime import UTC, datetime, timedelta

from app.modules.assinaturas.models import StatusAssinatura
from app.modules.assinaturas.regras import PLANO_BASE, PLANO_PRO, codigo_plano_efetivo

AGORA = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)
ANTES = AGORA - timedelta(days=1)
DEPOIS = AGORA + timedelta(days=1)


def efetivo(status, **datas):
    return codigo_plano_efetivo(
        status=status,
        codigo_contratado=PLANO_PRO,
        agora=AGORA,
        trial_termina_em=datas.get("trial"),
        periodo_atual_termina_em=datas.get("periodo"),
        carencia_termina_em=datas.get("carencia"),
    )


def test_trial_em_andamento_vale_pro():
    assert efetivo(StatusAssinatura.TRIAL, trial=DEPOIS) == PLANO_PRO


def test_trial_encerrado_cai_para_base():
    assert efetivo(StatusAssinatura.TRIAL, trial=ANTES) == PLANO_BASE


def test_assinatura_ativa_vale_o_contratado():
    assert efetivo(StatusAssinatura.ATIVA) == PLANO_PRO


def test_inadimplente_dentro_da_carencia_mantem_o_plano():
    assert efetivo(StatusAssinatura.INADIMPLENTE, carencia=DEPOIS) == PLANO_PRO


def test_inadimplente_apos_carencia_cai_para_base():
    assert efetivo(StatusAssinatura.INADIMPLENTE, carencia=ANTES) == PLANO_BASE


def test_cancelada_vale_ate_o_fim_do_periodo_pago():
    assert efetivo(StatusAssinatura.CANCELADA, periodo=DEPOIS) == PLANO_PRO
    assert efetivo(StatusAssinatura.CANCELADA, periodo=ANTES) == PLANO_BASE

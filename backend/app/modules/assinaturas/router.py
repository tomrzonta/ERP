"""Rotas da assinatura: plano efetivo e uso dos limites.

Compõe os services de outros módulos só aqui, no router, pra não criar
import circular (produtos e financeiro já importam o service de assinaturas).
"""

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.assinaturas import service
from app.modules.assinaturas.regras import Limite
from app.modules.assinaturas.schemas import UsoDoLimiteSaida, UsoSaida
from app.modules.auth.dependencias import Contexto, requer_permissao
from app.modules.produtos import service as produtos_service
from app.modules.produtos.models import TipoProduto
from app.shared.money import to_money

router = APIRouter(prefix="/assinatura", tags=["assinatura"])


@router.get("/uso", response_model=UsoSaida)
def uso_dos_limites(
    contexto: Contexto = Depends(requer_permissao("assinatura.ver")),
    db: Session = Depends(get_db),
):
    """Quanto de cada limite (com contagem de verdade) a empresa já usou.
    Só entram os limites que o sistema realmente aplica hoje."""
    itens = (
        (
            Limite.MAX_PRODUTOS_SIMPLES,
            "Produtos",
            produtos_service.contar_por_tipo(db, contexto.empresa_id, TipoProduto.SIMPLES),
        ),
        (
            Limite.MAX_COMPOSTOS,
            "Kits",
            produtos_service.contar_por_tipo(db, contexto.empresa_id, TipoProduto.KIT),
        ),
    )
    limites = []
    for limite, rotulo, usado in itens:
        teto = service.valor_do_limite(db, contexto.empresa_id, limite)
        limites.append(
            UsoDoLimiteSaida(
                chave=limite.value,
                rotulo=rotulo,
                usado=usado,
                limite=teto,
                percentual=to_money(Decimal(usado) / Decimal(teto) * 100) if teto else None,
            )
        )
    plano = service.plano_efetivo(db, contexto.empresa_id)
    return UsoSaida(plano=plano.codigo, limites=limites)

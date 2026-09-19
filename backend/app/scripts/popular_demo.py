"""Popula uma empresa com dados de demonstração (só desenvolvimento/staging).

Cria produtos, insumos, um kit, clientes, estoque, vendas espalhadas pelos
últimos dias (com descontos, formas de pagamento variadas e alguns
cancelamentos), consumo de insumos, alertas de estoque e contas a pagar/receber
— o suficiente pra ver o Painel e os relatórios com números.

Uso:
    docker compose exec backend python -m app.scripts.popular_demo --email voce@exemplo.com

Recusa rodar em produção e não roda duas vezes na mesma empresa (os produtos
de demonstração têm SKU `DEMO-...`).
"""

import argparse
import random
import sys
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core import models_registry  # noqa: F401  (registra todos os models)
from app.core.config import settings
from app.core.database import SessionLocal
from app.modules.acesso.models import Membro
from app.modules.clientes import service as clientes_service
from app.modules.composicao import service as composicao_service
from app.modules.estoque import service as estoque_service
from app.modules.financeiro import service as financeiro_service
from app.modules.financeiro.models import TipoConta
from app.modules.produtos import service as produtos_service
from app.modules.produtos.models import TipoProduto
from app.modules.produtos.repository import ProdutoRepositorio
from app.modules.usuarios import service as usuarios_service
from app.modules.vendas import service as vendas_service
from app.modules.vendas.models import FormaPagamento

BRASILIA = timezone(timedelta(hours=-3))

# (nome, preço de venda, custo)
PRODUTOS = [
    ("Vaso cerâmica P", "39.90", "14.00"),
    ("Vaso cerâmica G", "79.90", "31.00"),
    ("Cachepô trançado", "54.90", "19.50"),
    ("Suculenta mista", "12.90", "4.20"),
    ("Terra vegetal 2 kg", "18.00", "7.50"),
    ("Regador inox", "64.00", "28.00"),
    ("Kit jardinagem básico", "89.90", "0"),  # kit: custo vem da montagem
]
INSUMOS = [
    ("Argila", "kg", "6.50", "300"),
    ("Filamento PLA", "g", "0.11", "20000"),
    ("Tinta esmaltada", "ml", "0.09", "8000"),
]
CLIENTES = ["Ana Souza", "Bruno Lima", "Carla Dias", "Daniel Prado", "Elisa Nunes",
            "Fábio Reis", "Gabi Torres", "Heitor Melo"]  # fmt: skip
FORMAS = [FormaPagamento.DINHEIRO, FormaPagamento.PIX, FormaPagamento.CARTAO_CREDITO,
          FormaPagamento.CARTAO_DEBITO]  # fmt: skip
PESOS_FORMAS = [2, 4, 4, 3]


def _empresa_e_usuario(db, email: str):
    usuario = usuarios_service.por_email(db, email)
    if usuario is None:
        sys.exit(f"Nenhum usuário com o e-mail {email}.")
    membro = db.scalar(select(Membro).where(Membro.usuario_id == usuario.id))
    if membro is None:
        sys.exit("Esse usuário não pertence a nenhuma empresa.")
    return membro.empresa_id, usuario.id


def popular(db, empresa_id, usuario_id, dias: int, semente: int) -> dict[str, int]:
    rng = random.Random(semente)
    repo = ProdutoRepositorio(db, empresa_id)
    if repo.sku_em_uso("DEMO-001"):
        sys.exit("Esta empresa já tem dados de demonstração.")

    # --- catálogo --------------------------------------------------------
    produtos = []
    for indice, (nome, preco, custo) in enumerate(PRODUTOS, start=1):
        eh_kit = nome.startswith("Kit")
        produtos.append(
            produtos_service.criar_produto(
                db,
                empresa_id,
                nome=nome,
                sku=f"DEMO-{indice:03d}",
                tipo=TipoProduto.KIT if eh_kit else TipoProduto.SIMPLES,
                unidade_codigo="un",
                preco_venda=Decimal(preco),
                custo=Decimal(custo),
                vendavel=True,
            )
        )
    insumos = []
    for indice, (nome, unidade, custo, quantidade) in enumerate(INSUMOS, start=1):
        insumo = produtos_service.criar_produto(
            db,
            empresa_id,
            nome=nome,
            sku=f"DEMO-I{indice:02d}",
            unidade_codigo=unidade,
            vendavel=False,
            insumo=True,
            custo=Decimal(custo),
        )
        estoque_service.registrar_entrada(
            db, empresa_id, insumo.id, quantidade=Decimal(quantidade), custo_unitario=Decimal(custo)
        )
        insumos.append(insumo)

    simples = [p for p in produtos if p.tipo is TipoProduto.SIMPLES]
    kit = next(p for p in produtos if p.tipo is TipoProduto.KIT)
    for produto, (_, _, custo) in zip(produtos, PRODUTOS, strict=True):
        if produto.tipo is TipoProduto.SIMPLES:
            estoque_service.registrar_entrada(
                db, empresa_id, produto.id, quantidade=Decimal("600"), custo_unitario=Decimal(custo)
            )

    # --- kit com componentes, montagens e uma perda por contagem -----------
    argila, pla, tinta = insumos
    for componente, quantidade, perda in ((argila, "0.8", "5"), (pla, "120", "3"), (tinta, "40", "0")):
        composicao_service.adicionar_componente(
            db, empresa_id, kit.id, componente_id=componente.id,
            quantidade=Decimal(quantidade), perda_percentual=Decimal(perda),
        )  # fmt: skip
    for _ in range(6):  # 90 kits: 6 montagens de 15
        composicao_service.montar(db, empresa_id, kit.id, quantidade=Decimal("15"))
    estoque_service.registrar_ajuste(  # contagem menor que o saldo: "perda"
        db, empresa_id, pla.id, quantidade_contada=Decimal("8800"), origem="Contagem de inventário"
    )

    # --- clientes ----------------------------------------------------------
    clientes = [
        clientes_service.criar_cliente(db, empresa_id, nome=nome, telefone=f"1199{rng.randint(1000000, 9999999)}")
        for nome in CLIENTES
    ]  # fmt: skip

    # --- vendas nos últimos dias ------------------------------------------
    hoje = datetime.now(BRASILIA).replace(hour=0, minute=0, second=0, microsecond=0)
    fechadas = canceladas = 0
    for deslocamento in range(dias - 1, -1, -1):
        dia = hoje - timedelta(days=deslocamento)
        fim_de_semana = dia.weekday() >= 5
        for _ in range(rng.randint(2, 9) + (3 if fim_de_semana else 0)):
            momento = (dia + timedelta(hours=rng.randint(9, 19), minutes=rng.randint(0, 59))).astimezone(UTC)
            if momento > datetime.now(UTC):
                continue
            cliente = rng.choice(clientes) if rng.random() < 0.6 else None
            venda = vendas_service.abrir_venda(
                db, empresa_id, vendedor_usuario_id=usuario_id,
                cliente_id=cliente.id if cliente else None, ocorrido_em=momento,
            )  # fmt: skip
            escolhidos = rng.sample(simples, rng.randint(1, 3))
            if rng.random() < 0.12:  # o kit tem pouco estoque, então vende menos
                escolhidos.append(kit)
            for produto in escolhidos:
                desconto = Decimal(rng.choice([5, 10, 15])) if rng.random() < 0.2 else Decimal("0")
                vendas_service.adicionar_item(
                    db, empresa_id, venda.id, produto_id=produto.id,
                    quantidade=Decimal(rng.randint(1, 3)), desconto_percentual=desconto,
                )  # fmt: skip
            if rng.random() < 0.06:
                vendas_service.cancelar_venda(db, empresa_id, venda.id)
                canceladas += 1
                continue
            if rng.random() < 0.15:  # pagamento dividido
                a, b = rng.sample(FORMAS, 2)
                metade = (venda.total / 2).quantize(Decimal("0.01"))
                pagamentos = [{"forma": a, "valor": metade}, {"forma": b, "valor": venda.total - metade}]
            else:
                pagamentos = [{"forma": rng.choices(FORMAS, PESOS_FORMAS)[0], "valor": venda.total}]
            vendas_service.fechar_venda(db, empresa_id, venda.id, pagamentos=pagamentos)
            fechadas += 1

    # --- alertas de estoque ------------------------------------------------
    produtos_service.atualizar_produto(
        db, empresa_id, simples[3].id, {"estoque_minimo": Decimal("9999")}
    )  # suculenta: sempre abaixo do mínimo
    estoque_service.registrar_saida(  # regador: fica negativo
        db, empresa_id, simples[5].id,
        quantidade=estoque_service.obter_saldo(db, empresa_id, simples[5].id).fisico + Decimal("3"),
        origem="Venda sincronizada depois do fato",
    )  # fmt: skip

    # --- contas a pagar e a receber ---------------------------------------
    hoje_data = vendas_service.hoje()
    contas = [
        (TipoConta.PAGAR, "Aluguel da loja", "1800.00", -3, "Imobiliária Centro"),
        (TipoConta.PAGAR, "Energia elétrica", "312.40", 4, "Companhia de energia"),
        (TipoConta.PAGAR, "Fornecedor de argila", "950.00", 9, "Argilas do Vale"),
        (TipoConta.RECEBER, "Encomenda corporativa", "1250.00", 2, "Café Central"),
        (TipoConta.RECEBER, "Kits de festa", "640.00", 12, "Bruno Lima"),
    ]
    for tipo, descricao, valor, dias_ate, contraparte in contas:
        financeiro_service.criar_conta(
            db, empresa_id, usuario_id=usuario_id, tipo=tipo, descricao=descricao,
            valor=Decimal(valor), vencimento=hoje_data + timedelta(days=dias_ate), contraparte=contraparte,
        )  # fmt: skip

    return {"vendas_fechadas": fechadas, "vendas_canceladas": canceladas, "clientes": len(clientes)}


def main() -> None:
    if settings.is_production:
        sys.exit("Recusado: este script não roda em produção.")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--email", required=True, help="e-mail de um usuário da empresa alvo")
    parser.add_argument("--dias", type=int, default=45, help="quantos dias de histórico (padrão 45)")
    parser.add_argument("--semente", type=int, default=7, help="semente do gerador aleatório")
    args = parser.parse_args()

    with SessionLocal() as db:
        empresa_id, usuario_id = _empresa_e_usuario(db, args.email)
        resultado = popular(db, empresa_id, usuario_id, args.dias, args.semente)
        db.commit()
    print("Dados de demonstração criados:", resultado)


if __name__ == "__main__":
    main()

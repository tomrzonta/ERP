"""Regras de negócio de estoque: entradas, saídas, ajustes e reservas.

O saldo físico e o reservado ficam em `saldos_estoque` (cache travado com
SELECT FOR UPDATE a cada escrita); a verdade histórica é a sequência de
`movimentacoes_estoque`. O custo médio é responsabilidade do módulo de
produtos — aqui calculamos o novo valor e pedimos para ele gravar.

Todo `registrar_*`/`reservar`/`liberar_reserva` aceita um `id` opcional
vindo do cliente (sincronização offline): se um movimento com esse id já
existir na empresa, ele é devolvido sem reprocessar nada.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import RegraDeNegocio
from app.modules.estoque.models import MovimentoEstoque, SaldoEstoque, TipoMovimento
from app.modules.estoque.repository import MovimentoRepositorio, SaldoRepositorio
from app.modules.produtos import service as produtos_service
from app.modules.produtos.models import Produto
from app.modules.produtos.repository import ProdutoRepositorio
from app.shared.money import to_money
from app.shared.quantidade import to_custo, to_quantidade


@dataclass(frozen=True)
class SaldoDoProduto:
    produto: Produto
    fisico: Decimal
    reservado: Decimal

    @property
    def disponivel(self) -> Decimal:
        return self.fisico - self.reservado


def _produto_com_estoque(db: Session, empresa_id: uuid.UUID, produto_id: uuid.UUID) -> Produto:
    produto = produtos_service.obter_produto(db, empresa_id, produto_id)
    if not produto.controla_estoque:
        raise RegraDeNegocio("Este produto não controla estoque.")
    return produto


def _movimento_existente(
    repo_movimentos: MovimentoRepositorio, id: uuid.UUID | None
) -> MovimentoEstoque | None:
    if id is None:
        return None
    return repo_movimentos.obter(id)


def obter_movimento(
    db: Session, empresa_id: uuid.UUID, movimento_id: uuid.UUID
) -> MovimentoEstoque | None:
    return MovimentoRepositorio(db, empresa_id).obter(movimento_id)


def _registrar(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    produto_id: uuid.UUID,
    tipo: TipoMovimento,
    quantidade: Decimal,
    custo_unitario: Decimal | None = None,
    ocorrido_em: datetime | None = None,
    origem: str | None = None,
    id: uuid.UUID | None = None,
) -> MovimentoEstoque:
    movimento = MovimentoEstoque(
        produto_id=produto_id,
        tipo=tipo,
        quantidade=quantidade,
        custo_unitario=custo_unitario,
        origem=(origem or "").strip() or None,
        ocorrido_em=ocorrido_em if ocorrido_em is not None else datetime.now(UTC),
    )
    if id is not None:
        movimento.id = id
    return MovimentoRepositorio(db, empresa_id).adicionar(movimento)


# --- helpers compartilhados de entrada/saída (usados também pela montagem) ---


def _entrada(
    db: Session,
    empresa_id: uuid.UUID,
    produto: Produto,
    *,
    tipo: TipoMovimento,
    quantidade_base: Decimal,
    custo_base: Decimal,
    ocorrido_em: datetime | None = None,
    origem: str | None = None,
    id: uuid.UUID | None = None,
) -> MovimentoEstoque:
    saldo = SaldoRepositorio(db, empresa_id).travar_ou_criar(produto.id)

    saldo_anterior = saldo.fisico
    if saldo_anterior <= 0:
        novo_custo_medio = custo_base
    else:
        novo_custo_medio = to_custo(
            (saldo_anterior * produto.custo_medio + quantidade_base * custo_base)
            / (saldo_anterior + quantidade_base)
        )
    saldo.fisico = saldo_anterior + quantidade_base

    produtos_service.registrar_custo(
        db,
        empresa_id,
        produto.id,
        custo_medio=novo_custo_medio,
        custo_ultima_compra=custo_base if tipo is TipoMovimento.ENTRADA else None,
    )

    return _registrar(
        db,
        empresa_id,
        produto_id=produto.id,
        tipo=tipo,
        quantidade=quantidade_base,
        custo_unitario=custo_base,
        ocorrido_em=ocorrido_em,
        origem=origem,
        id=id,
    )


def _saida(
    db: Session,
    empresa_id: uuid.UUID,
    produto: Produto,
    *,
    tipo: TipoMovimento,
    quantidade_base: Decimal,
    ocorrido_em: datetime | None = None,
    origem: str | None = None,
    id: uuid.UUID | None = None,
) -> MovimentoEstoque:
    saldo = SaldoRepositorio(db, empresa_id).travar_ou_criar(produto.id)
    saldo.fisico = saldo.fisico - quantidade_base

    return _registrar(
        db,
        empresa_id,
        produto_id=produto.id,
        tipo=tipo,
        quantidade=-quantidade_base,
        # Saída grava o custo vigente e não mexe na média.
        custo_unitario=produto.custo_medio,
        ocorrido_em=ocorrido_em,
        origem=origem,
        id=id,
    )


# --- entrada ---


def registrar_entrada(
    db: Session,
    empresa_id: uuid.UUID,
    produto_id: uuid.UUID,
    *,
    quantidade: Decimal,
    custo_unitario: Decimal,
    unidade_id: uuid.UUID | None = None,
    ocorrido_em: datetime | None = None,
    origem: str | None = None,
    id: uuid.UUID | None = None,
) -> MovimentoEstoque:
    if quantidade <= 0:
        raise RegraDeNegocio("A quantidade da entrada precisa ser maior que zero.")
    if custo_unitario < 0:
        raise RegraDeNegocio("O custo da entrada não pode ser negativo.")

    repo_movimentos = MovimentoRepositorio(db, empresa_id)
    existente = _movimento_existente(repo_movimentos, id)
    if existente is not None:
        return existente

    produto = _produto_com_estoque(db, empresa_id, produto_id)

    quantidade_base = to_quantidade(quantidade)
    custo_base = to_custo(custo_unitario)
    if unidade_id is not None:
        # Compra em unidade alternativa (ex.: 1 rolo = 1000 g): o fator já é
        # relativo à unidade de estoque do produto.
        unidade = produtos_service.obter_unidade_para_compra(db, empresa_id, produto_id, unidade_id)
        quantidade_base = to_quantidade(quantidade * unidade.fator)
        custo_base = to_custo(custo_unitario / unidade.fator)

    return _entrada(
        db,
        empresa_id,
        produto,
        tipo=TipoMovimento.ENTRADA,
        quantidade_base=quantidade_base,
        custo_base=custo_base,
        ocorrido_em=ocorrido_em,
        origem=origem,
        id=id,
    )


def produzir_por_montagem(
    db: Session,
    empresa_id: uuid.UUID,
    produto_id: uuid.UUID,
    *,
    quantidade: Decimal,
    custo_unitario: Decimal,
    ocorrido_em: datetime | None = None,
    origem: str | None = None,
    id: uuid.UUID | None = None,
) -> MovimentoEstoque:
    """Entrada do kit ao final de uma montagem (módulo composição)."""
    produto = _produto_com_estoque(db, empresa_id, produto_id)
    return _entrada(
        db,
        empresa_id,
        produto,
        tipo=TipoMovimento.MONTAGEM,
        quantidade_base=to_quantidade(quantidade),
        custo_base=to_custo(custo_unitario),
        ocorrido_em=ocorrido_em,
        origem=origem,
        id=id,
    )


# --- saída ---


def registrar_saida(
    db: Session,
    empresa_id: uuid.UUID,
    produto_id: uuid.UUID,
    *,
    quantidade: Decimal,
    ocorrido_em: datetime | None = None,
    origem: str | None = None,
    id: uuid.UUID | None = None,
) -> MovimentoEstoque:
    if quantidade <= 0:
        raise RegraDeNegocio("A quantidade da saída precisa ser maior que zero.")

    repo_movimentos = MovimentoRepositorio(db, empresa_id)
    existente = _movimento_existente(repo_movimentos, id)
    if existente is not None:
        return existente

    produto = _produto_com_estoque(db, empresa_id, produto_id)
    quantidade_base = to_quantidade(quantidade)

    return _saida(
        db,
        empresa_id,
        produto,
        tipo=TipoMovimento.SAIDA,
        quantidade_base=quantidade_base,
        ocorrido_em=ocorrido_em,
        origem=origem,
        id=id,
    )


def consumir_para_montagem(
    db: Session, empresa_id: uuid.UUID, produto_id: uuid.UUID, *, quantidade: Decimal
) -> MovimentoEstoque:
    """Saída de um componente durante uma montagem (módulo composição)."""
    produto = _produto_com_estoque(db, empresa_id, produto_id)
    return _saida(
        db,
        empresa_id,
        produto,
        tipo=TipoMovimento.MONTAGEM,
        quantidade_base=to_quantidade(quantidade),
    )


# --- ajuste ---


def registrar_ajuste(
    db: Session,
    empresa_id: uuid.UUID,
    produto_id: uuid.UUID,
    *,
    quantidade_contada: Decimal,
    ocorrido_em: datetime | None = None,
    origem: str | None = None,
    id: uuid.UUID | None = None,
) -> MovimentoEstoque | None:
    if quantidade_contada < 0:
        raise RegraDeNegocio("A quantidade contada não pode ser negativa.")

    repo_movimentos = MovimentoRepositorio(db, empresa_id)
    existente = _movimento_existente(repo_movimentos, id)
    if existente is not None:
        return existente

    produto = _produto_com_estoque(db, empresa_id, produto_id)
    contada = to_quantidade(quantidade_contada)

    saldo = SaldoRepositorio(db, empresa_id).travar_ou_criar(produto_id)
    delta = contada - saldo.fisico
    if delta == 0:
        return None

    saldo.fisico = contada

    return _registrar(
        db,
        empresa_id,
        produto_id=produto_id,
        tipo=TipoMovimento.AJUSTE,
        quantidade=delta,
        # Ajuste não tem preço de compra novo: grava o custo vigente e não
        # recalcula a média, seja o delta positivo ou negativo.
        custo_unitario=produto.custo_medio,
        ocorrido_em=ocorrido_em,
        origem=origem,
        id=id,
    )


# --- estorno ---


def estornar_saida(
    db: Session,
    empresa_id: uuid.UUID,
    produto_id: uuid.UUID,
    *,
    quantidade: Decimal,
    custo_unitario: Decimal,
    ocorrido_em: datetime | None = None,
    origem: str | None = None,
    id: uuid.UUID | None = None,
) -> MovimentoEstoque:
    """Cancelamento de uma venda já fechada: credita de volta a quantidade
    debitada, com o custo que aquela saída registrou. Não recalcula a
    média — mesma lógica do ajuste, só que sempre creditando."""
    if quantidade <= 0:
        raise RegraDeNegocio("A quantidade estornada precisa ser maior que zero.")

    repo_movimentos = MovimentoRepositorio(db, empresa_id)
    existente = _movimento_existente(repo_movimentos, id)
    if existente is not None:
        return existente

    _produto_com_estoque(db, empresa_id, produto_id)
    quantidade_base = to_quantidade(quantidade)

    saldo = SaldoRepositorio(db, empresa_id).travar_ou_criar(produto_id)
    saldo.fisico = saldo.fisico + quantidade_base

    return _registrar(
        db,
        empresa_id,
        produto_id=produto_id,
        tipo=TipoMovimento.ESTORNO,
        quantidade=quantidade_base,
        custo_unitario=to_custo(custo_unitario),
        ocorrido_em=ocorrido_em,
        origem=origem,
        id=id,
    )


# --- reserva ---


def reservar(
    db: Session,
    empresa_id: uuid.UUID,
    produto_id: uuid.UUID,
    *,
    quantidade: Decimal,
    ocorrido_em: datetime | None = None,
    origem: str | None = None,
    id: uuid.UUID | None = None,
) -> MovimentoEstoque:
    if quantidade <= 0:
        raise RegraDeNegocio("A quantidade reservada precisa ser maior que zero.")

    repo_movimentos = MovimentoRepositorio(db, empresa_id)
    existente = _movimento_existente(repo_movimentos, id)
    if existente is not None:
        return existente

    _produto_com_estoque(db, empresa_id, produto_id)
    quantidade_base = to_quantidade(quantidade)

    saldo = SaldoRepositorio(db, empresa_id).travar_ou_criar(produto_id)
    if saldo.disponivel < quantidade_base:
        raise RegraDeNegocio("Estoque disponível insuficiente para reservar.")
    saldo.reservado = saldo.reservado + quantidade_base

    return _registrar(
        db,
        empresa_id,
        produto_id=produto_id,
        tipo=TipoMovimento.RESERVA,
        quantidade=quantidade_base,
        ocorrido_em=ocorrido_em,
        origem=origem,
        id=id,
    )


def liberar_reserva(
    db: Session,
    empresa_id: uuid.UUID,
    produto_id: uuid.UUID,
    *,
    quantidade: Decimal,
    ocorrido_em: datetime | None = None,
    origem: str | None = None,
    id: uuid.UUID | None = None,
) -> MovimentoEstoque:
    if quantidade <= 0:
        raise RegraDeNegocio("A quantidade liberada precisa ser maior que zero.")

    repo_movimentos = MovimentoRepositorio(db, empresa_id)
    existente = _movimento_existente(repo_movimentos, id)
    if existente is not None:
        return existente

    _produto_com_estoque(db, empresa_id, produto_id)
    quantidade_base = to_quantidade(quantidade)

    saldo = SaldoRepositorio(db, empresa_id).travar_ou_criar(produto_id)
    if quantidade_base > saldo.reservado:
        raise RegraDeNegocio("Não é possível liberar mais do que o reservado.")
    saldo.reservado = saldo.reservado - quantidade_base

    return _registrar(
        db,
        empresa_id,
        produto_id=produto_id,
        tipo=TipoMovimento.LIBERACAO,
        quantidade=-quantidade_base,
        ocorrido_em=ocorrido_em,
        origem=origem,
        id=id,
    )


# --- consultas ---


def obter_saldo(db: Session, empresa_id: uuid.UUID, produto_id: uuid.UUID) -> SaldoEstoque:
    produtos_service.obter_produto(db, empresa_id, produto_id)
    saldo = SaldoRepositorio(db, empresa_id).por_produto(produto_id)
    if saldo is not None:
        return saldo
    return SaldoEstoque(
        empresa_id=empresa_id, produto_id=produto_id, fisico=Decimal("0"), reservado=Decimal("0")
    )


def listar_saldos(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    termo: str | None = None,
    limite: int = 50,
    deslocamento: int = 0,
) -> list[SaldoDoProduto]:
    """Saldo de todos os produtos com controle de estoque, mesmo sem nenhum movimento ainda."""
    produtos = ProdutoRepositorio(db, empresa_id).buscar(
        termo=termo,
        apenas_com_controle_de_estoque=True,
        limite=limite,
        deslocamento=deslocamento,
    )
    saldos = SaldoRepositorio(db, empresa_id).mapa_por_produtos([p.id for p in produtos])
    return [
        SaldoDoProduto(
            produto=produto,
            fisico=(saldos[produto.id].fisico if produto.id in saldos else Decimal("0")),
            reservado=(saldos[produto.id].reservado if produto.id in saldos else Decimal("0")),
        )
        for produto in produtos
    ]


def listar_movimentos(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    produto_id: uuid.UUID | None = None,
    tipo: TipoMovimento | None = None,
    limite: int = 50,
    deslocamento: int = 0,
) -> list[MovimentoEstoque]:
    return MovimentoRepositorio(db, empresa_id).buscar(
        produto_id=produto_id, tipo=tipo, limite=limite, deslocamento=deslocamento
    )


@dataclass(frozen=True)
class AlertaDeEstoque:
    produto: Produto
    tipo: str  # "negativo" | "baixo"
    fisico: Decimal
    disponivel: Decimal
    estoque_minimo: Decimal | None


def alertas_de_estoque(db: Session, empresa_id: uuid.UUID) -> list[AlertaDeEstoque]:
    """Produtos com saldo físico negativo (vendas sincronizadas depois do
    fato) e produtos com disponível no estoque mínimo ou abaixo dele.
    Negativos primeiro; dentro de cada grupo, o mais crítico antes."""
    alertas: list[AlertaDeEstoque] = []
    pagina = 200
    deslocamento = 0
    while True:
        saldos = listar_saldos(db, empresa_id, limite=pagina, deslocamento=deslocamento)
        for item in saldos:
            minimo = item.produto.estoque_minimo
            if item.fisico < 0:
                tipo = "negativo"
            elif minimo is not None and item.disponivel <= minimo:
                tipo = "baixo"
            else:
                continue
            alertas.append(AlertaDeEstoque(item.produto, tipo, item.fisico, item.disponivel, minimo))
        if len(saldos) < pagina:
            break
        deslocamento += pagina
    alertas.sort(key=lambda a: (a.tipo != "negativo", a.disponivel))
    return alertas


@dataclass(frozen=True)
class ConsumoDeInsumo:
    produto: Produto
    consumido_em_montagens: Decimal
    custo_das_montagens: Decimal
    baixado_por_ajuste: Decimal
    custo_dos_ajustes: Decimal

    @property
    def custo_total(self) -> Decimal:
        return self.custo_das_montagens + self.custo_dos_ajustes


def consumo_de_insumos(
    db: Session, empresa_id: uuid.UUID, *, inicio: date, fim: date
) -> list[ConsumoDeInsumo]:
    """Consumo de insumos no período (dias em horário de Brasília):
    o que as montagens consumiram e o que saiu por ajuste de contagem para
    baixo (perda ou divergência de inventário). Só produtos marcados como
    insumo. A perda percentual da composição não aparece à parte: ela já
    está somada no consumo da montagem. Maior custo primeiro."""
    if fim < inicio:
        raise RegraDeNegocio("A data final não pode ser anterior à inicial.")
    if (fim - inicio).days >= 366:
        raise RegraDeNegocio("O período máximo é de um ano.")

    fuso = timezone(timedelta(hours=-3))
    de = datetime.combine(inicio, time.min, tzinfo=fuso)
    ate = datetime.combine(fim + timedelta(days=1), time.min, tzinfo=fuso)

    itens: list[ConsumoDeInsumo] = []
    for produto_id, q_mont, c_mont, q_aj, c_aj in MovimentoRepositorio(
        db, empresa_id
    ).consumo_e_perdas(de, ate):
        if q_mont == 0 and q_aj == 0:
            continue  # só teve entrada de ajuste ou montagem que produziu o item
        produto = ProdutoRepositorio(db, empresa_id).obter_ou_erro(produto_id)
        if not produto.insumo:
            continue
        itens.append(
            ConsumoDeInsumo(
                produto,
                to_quantidade(q_mont),
                to_money(c_mont),
                to_quantidade(q_aj),
                to_money(c_aj),
            )
        )
    itens.sort(key=lambda i: (i.custo_total, i.consumido_em_montagens), reverse=True)
    return itens

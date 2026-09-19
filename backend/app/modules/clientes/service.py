"""Regras de negócio de clientes."""

import re
import uuid
from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import RegraDeNegocio
from app.modules.clientes.models import Cliente, OrigemCliente
from app.modules.clientes.repository import ClienteRepositorio


def _cpf_valido(cpf: str) -> str:
    digitos = re.sub(r"\D", "", cpf)
    if len(digitos) != 11:
        raise RegraDeNegocio("CPF precisa ter 11 dígitos.")
    return digitos


def criar_cliente(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    nome: str,
    telefone: str | None = None,
    email: str | None = None,
    cpf: str | None = None,
    data_nascimento: date | None = None,
    endereco: str | None = None,
    consentimento_marketing: bool = False,
    origem: OrigemCliente = OrigemCliente.BALCAO,
    id: uuid.UUID | None = None,
) -> Cliente:
    repo = ClienteRepositorio(db, empresa_id)

    # Aceita o id do dispositivo (cadastro no PDV offline): reenviar o mesmo
    # não duplica, só devolve o cliente já existente.
    if id is not None:
        existente = repo.obter(id)
        if existente is not None:
            return existente

    cliente = Cliente(
        nome=nome.strip(),
        telefone=(telefone or "").strip() or None,
        email=(email or "").strip() or None,
        cpf=_cpf_valido(cpf) if cpf else None,
        data_nascimento=data_nascimento,
        endereco=(endereco or "").strip() or None,
        consentimento_marketing=consentimento_marketing,
        consentimento_em=datetime.now(UTC) if consentimento_marketing else None,
        origem=origem,
    )
    if id is not None:
        cliente.id = id
    return repo.adicionar(cliente)


def obter_cliente(db: Session, empresa_id: uuid.UUID, cliente_id: uuid.UUID) -> Cliente:
    return ClienteRepositorio(db, empresa_id).obter_ou_erro(cliente_id)


def listar_clientes(
    db: Session,
    empresa_id: uuid.UUID,
    *,
    termo: str | None = None,
    limite: int = 50,
    deslocamento: int = 0,
) -> list[Cliente]:
    return ClienteRepositorio(db, empresa_id).buscar(
        termo=termo, limite=limite, deslocamento=deslocamento
    )


def atualizar_cliente(
    db: Session, empresa_id: uuid.UUID, cliente_id: uuid.UUID, campos: dict
) -> Cliente:
    repo = ClienteRepositorio(db, empresa_id)
    cliente = repo.obter_ou_erro(cliente_id)

    if cliente.anonimizado_em is not None:
        raise RegraDeNegocio("Cliente anonimizado não pode ser editado.")

    if campos.get("cpf"):
        campos["cpf"] = _cpf_valido(campos["cpf"])

    if "consentimento_marketing" in campos:
        campos["consentimento_em"] = datetime.now(UTC) if campos["consentimento_marketing"] else None

    for campo, valor in campos.items():
        setattr(cliente, campo, valor)

    db.flush()
    return cliente


def mesclar_clientes(
    db: Session, empresa_id: uuid.UUID, *, cliente_id: uuid.UUID, duplicado_id: uuid.UUID
) -> Cliente:
    """Une o cadastro `duplicado_id` no `cliente_id` (o sobrevivente).

    Preenche no sobrevivente só os campos que ele não tinha; as vendas do
    duplicado são reatribuídas por quem chama (módulo vendas, pra evitar
    import circular). O duplicado nunca é excluído — fica marcado como
    mesclado e some da listagem.
    """
    if cliente_id == duplicado_id:
        raise RegraDeNegocio("Não é possível mesclar um cliente com ele mesmo.")

    repo = ClienteRepositorio(db, empresa_id)
    cliente = repo.obter_ou_erro(cliente_id)
    duplicado = repo.obter_ou_erro(duplicado_id)

    if cliente.mesclado_com_id is not None:
        raise RegraDeNegocio("Este cliente já foi mesclado em outro cadastro.")
    if duplicado.mesclado_com_id is not None:
        raise RegraDeNegocio("O cliente duplicado já foi mesclado em outro cadastro.")

    if not cliente.telefone and duplicado.telefone:
        cliente.telefone = duplicado.telefone
    if not cliente.email and duplicado.email:
        cliente.email = duplicado.email
    if not cliente.cpf and duplicado.cpf:
        cliente.cpf = duplicado.cpf
    if not cliente.data_nascimento and duplicado.data_nascimento:
        cliente.data_nascimento = duplicado.data_nascimento
    if not cliente.endereco and duplicado.endereco:
        cliente.endereco = duplicado.endereco
    if not cliente.consentimento_marketing and duplicado.consentimento_marketing:
        cliente.consentimento_marketing = True
        cliente.consentimento_em = duplicado.consentimento_em or datetime.now(UTC)

    duplicado.mesclado_com_id = cliente.id

    db.flush()
    return cliente


def anonimizar_cliente(db: Session, empresa_id: uuid.UUID, cliente_id: uuid.UUID) -> Cliente:
    """LGPD: apaga os dados pessoais, mas mantém o registro (e o vínculo com
    as vendas dele) para as métricas e o histórico continuarem batendo."""
    cliente = ClienteRepositorio(db, empresa_id).obter_ou_erro(cliente_id)
    if cliente.anonimizado_em is not None:
        raise RegraDeNegocio("Este cliente já foi anonimizado.")

    cliente.nome = "Cliente anonimizado"
    cliente.telefone = None
    cliente.email = None
    cliente.cpf = None
    cliente.data_nascimento = None
    cliente.endereco = None
    cliente.consentimento_marketing = False
    cliente.consentimento_em = None
    cliente.anonimizado_em = datetime.now(UTC)

    db.flush()
    return cliente

import uuid

import pytest

from app.core.exceptions import NaoEncontrado, RegraDeNegocio
from app.modules.clientes import service
from app.modules.clientes.models import OrigemCliente
from app.modules.clientes.repository import ClienteRepositorio
from app.modules.empresas.service import criar_empresa_com_padroes
from app.modules.usuarios.models import Usuario


def criar_empresa(db):
    usuario = Usuario(nome="Dona", email=f"{uuid.uuid4().hex[:8]}@exemplo.com", senha_hash="x")
    db.add(usuario)
    db.flush()
    criada = criar_empresa_com_padroes(
        db, nome_fantasia=f"Loja {uuid.uuid4().hex[:6]}", usuario_dono_id=usuario.id
    )
    return criada.empresa.id


def test_cria_cliente_com_dados_minimos(db):
    empresa_id = criar_empresa(db)

    cliente = service.criar_cliente(db, empresa_id, nome="Maria")

    assert cliente.nome == "Maria"
    assert cliente.origem is OrigemCliente.BALCAO
    assert cliente.consentimento_marketing is False
    assert cliente.consentimento_em is None


def test_consentimento_marketing_grava_a_data(db):
    empresa_id = criar_empresa(db)

    cliente = service.criar_cliente(
        db, empresa_id, nome="Maria", consentimento_marketing=True
    )

    assert cliente.consentimento_em is not None


def test_cpf_invalido_e_rejeitado(db):
    empresa_id = criar_empresa(db)

    with pytest.raises(RegraDeNegocio):
        service.criar_cliente(db, empresa_id, nome="Maria", cpf="123")


def test_reenviar_o_mesmo_id_nao_duplica(db):
    empresa_id = criar_empresa(db)
    id_do_dispositivo = uuid.uuid4()

    primeiro = service.criar_cliente(
        db, empresa_id, id=id_do_dispositivo, nome="Maria", telefone="11999990000"
    )
    segundo = service.criar_cliente(
        db, empresa_id, id=id_do_dispositivo, nome="Maria", telefone="11999990000"
    )

    assert primeiro.id == segundo.id
    assert ClienteRepositorio(db, empresa_id).buscar() == [primeiro]


def test_busca_por_termo(db):
    empresa_id = criar_empresa(db)
    service.criar_cliente(db, empresa_id, nome="Maria Silva", telefone="11988887777")
    service.criar_cliente(db, empresa_id, nome="João Souza", telefone="11977776666")

    encontrados = service.listar_clientes(db, empresa_id, termo="maria")

    assert {c.nome for c in encontrados} == {"Maria Silva"}


def test_atualiza_dados_do_cliente(db):
    empresa_id = criar_empresa(db)
    cliente = service.criar_cliente(db, empresa_id, nome="Maria")

    atualizado = service.atualizar_cliente(
        db, empresa_id, cliente.id, {"telefone": "11999990000", "consentimento_marketing": True}
    )

    assert atualizado.telefone == "11999990000"
    assert atualizado.consentimento_marketing is True
    assert atualizado.consentimento_em is not None


def test_cliente_de_outra_empresa_nao_e_encontrado(db):
    primeira = criar_empresa(db)
    segunda = criar_empresa(db)
    cliente = service.criar_cliente(db, primeira, nome="Maria")

    assert ClienteRepositorio(db, segunda).buscar() == []
    with pytest.raises(NaoEncontrado):
        service.obter_cliente(db, segunda, cliente.id)


def test_mesclar_preenche_so_os_campos_vazios_do_sobrevivente(db):
    empresa_id = criar_empresa(db)
    sobrevivente = service.criar_cliente(db, empresa_id, nome="Maria Silva", telefone="11999990000")
    duplicado = service.criar_cliente(
        db, empresa_id, nome="Maria S.", telefone="11988887777", email="maria@exemplo.com"
    )

    mesclado = service.mesclar_clientes(
        db, empresa_id, cliente_id=sobrevivente.id, duplicado_id=duplicado.id
    )

    # Telefone já existia no sobrevivente: não é sobrescrito.
    assert mesclado.telefone == "11999990000"
    # E-mail só existia no duplicado: é herdado.
    assert mesclado.email == "maria@exemplo.com"


def test_mesclar_reune_consentimento_de_marketing(db):
    empresa_id = criar_empresa(db)
    sobrevivente = service.criar_cliente(db, empresa_id, nome="Maria")
    duplicado = service.criar_cliente(
        db, empresa_id, nome="Maria S.", consentimento_marketing=True
    )

    mesclado = service.mesclar_clientes(
        db, empresa_id, cliente_id=sobrevivente.id, duplicado_id=duplicado.id
    )

    assert mesclado.consentimento_marketing is True
    assert mesclado.consentimento_em is not None


def test_duplicado_mesclado_some_da_listagem(db):
    empresa_id = criar_empresa(db)
    sobrevivente = service.criar_cliente(db, empresa_id, nome="Maria")
    duplicado = service.criar_cliente(db, empresa_id, nome="Maria S.")

    service.mesclar_clientes(
        db, empresa_id, cliente_id=sobrevivente.id, duplicado_id=duplicado.id
    )

    nomes = {c.nome for c in service.listar_clientes(db, empresa_id)}
    assert nomes == {"Maria"}


def test_nao_pode_mesclar_cliente_com_ele_mesmo(db):
    empresa_id = criar_empresa(db)
    cliente = service.criar_cliente(db, empresa_id, nome="Maria")

    with pytest.raises(RegraDeNegocio):
        service.mesclar_clientes(db, empresa_id, cliente_id=cliente.id, duplicado_id=cliente.id)


def test_nao_pode_mesclar_duplicado_ja_mesclado(db):
    empresa_id = criar_empresa(db)
    a = service.criar_cliente(db, empresa_id, nome="A")
    b = service.criar_cliente(db, empresa_id, nome="B")
    c = service.criar_cliente(db, empresa_id, nome="C")
    service.mesclar_clientes(db, empresa_id, cliente_id=a.id, duplicado_id=b.id)

    with pytest.raises(RegraDeNegocio):
        service.mesclar_clientes(db, empresa_id, cliente_id=c.id, duplicado_id=b.id)


def test_anonimizar_apaga_dados_pessoais_mas_mantem_o_registro(db):
    empresa_id = criar_empresa(db)
    cliente = service.criar_cliente(
        db, empresa_id, nome="Maria", telefone="11999990000", email="maria@exemplo.com", cpf="11144477735"
    )

    anonimizado = service.anonimizar_cliente(db, empresa_id, cliente.id)

    assert anonimizado.nome == "Cliente anonimizado"
    assert anonimizado.telefone is None
    assert anonimizado.email is None
    assert anonimizado.cpf is None
    assert anonimizado.anonimizado_em is not None
    assert ClienteRepositorio(db, empresa_id).obter(cliente.id) is not None


def test_nao_pode_editar_cliente_anonimizado(db):
    empresa_id = criar_empresa(db)
    cliente = service.criar_cliente(db, empresa_id, nome="Maria")
    service.anonimizar_cliente(db, empresa_id, cliente.id)

    with pytest.raises(RegraDeNegocio):
        service.atualizar_cliente(db, empresa_id, cliente.id, {"nome": "Outro nome"})


def test_nao_pode_anonimizar_duas_vezes(db):
    empresa_id = criar_empresa(db)
    cliente = service.criar_cliente(db, empresa_id, nome="Maria")
    service.anonimizar_cliente(db, empresa_id, cliente.id)

    with pytest.raises(RegraDeNegocio):
        service.anonimizar_cliente(db, empresa_id, cliente.id)

import uuid

import pytest

from app.core.exceptions import PermissaoNegada
from app.modules.auth.dependencias import Contexto, requer_permissao
from app.modules.empresas.service import criar_empresa_com_padroes
from app.modules.usuarios.service import por_email

API = "/api/v1/auth"
SENHA = "senha-forte-123"


def email_unico() -> str:
    return f"pessoa-{uuid.uuid4().hex[:8]}@exemplo.com"


def cadastrar(cliente, email=None, nome_empresa="Minha Loja"):
    resposta = cliente.post(
        f"{API}/cadastro",
        json={
            "nome": "Maria",
            "email": email or email_unico(),
            "senha": SENHA,
            "nome_empresa": nome_empresa,
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def cabecalho(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


def test_cadastro_entra_na_empresa_como_dono_no_trial(cliente):
    dados = cadastrar(cliente)
    assert dados["empresa_ativa_id"]

    eu = cliente.get(f"{API}/eu", headers=cabecalho(dados["tokens"]["access_token"]))
    assert eu.status_code == 200, eu.text
    corpo = eu.json()
    assert corpo["papel"] == "Dono"
    assert corpo["plano"] == "pro"
    assert "papeis.gerenciar" in corpo["permissoes"]


def test_email_normalizado_e_duplicado_recusado(cliente):
    email = email_unico()
    cadastrar(cliente, email=email.upper())
    resposta = cliente.post(
        f"{API}/cadastro",
        json={"nome": "Outra", "email": email, "senha": SENHA, "nome_empresa": "Outra Loja"},
    )
    assert resposta.status_code == 409


def test_senha_curta_recusada(cliente):
    resposta = cliente.post(
        f"{API}/cadastro",
        json={"nome": "Maria", "email": email_unico(), "senha": "123", "nome_empresa": "Loja"},
    )
    assert resposta.status_code == 422


def test_login_com_senha_errada_ou_email_inexistente_tem_mesma_resposta(cliente):
    email = email_unico()
    cadastrar(cliente, email=email)

    errada = cliente.post(f"{API}/login", json={"email": email, "senha": "outra-senha"})
    inexistente = cliente.post(f"{API}/login", json={"email": email_unico(), "senha": SENHA})

    assert errada.status_code == inexistente.status_code == 401
    assert errada.json() == inexistente.json()


def test_login_com_uma_empresa_entra_direto(cliente):
    email = email_unico()
    cadastrar(cliente, email=email)
    resposta = cliente.post(f"{API}/login", json={"email": email, "senha": SENHA})
    assert resposta.status_code == 200
    assert resposta.json()["empresa_ativa_id"]


def test_sem_token_e_token_invalido_sao_recusados(cliente):
    assert cliente.get(f"{API}/eu").status_code == 401
    assert cliente.get(f"{API}/eu", headers=cabecalho("abc.def.ghi")).status_code == 401


def test_renovar_troca_token_e_reuso_revoga_a_sessao(cliente):
    tokens = cadastrar(cliente)["tokens"]

    primeira = cliente.post(f"{API}/renovar", json={"refresh_token": tokens["refresh_token"]})
    assert primeira.status_code == 200
    novo_refresh = primeira.json()["refresh_token"]
    assert novo_refresh != tokens["refresh_token"]

    # Reapresentar o token antigo derruba a sessão inteira
    reuso = cliente.post(f"{API}/renovar", json={"refresh_token": tokens["refresh_token"]})
    assert reuso.status_code == 401
    depois = cliente.post(f"{API}/renovar", json={"refresh_token": novo_refresh})
    assert depois.status_code == 401


def test_sair_invalida_o_token_de_acesso(cliente):
    access = cadastrar(cliente)["tokens"]["access_token"]
    assert cliente.post(f"{API}/sair", headers=cabecalho(access)).status_code == 204
    assert cliente.get(f"{API}/eu", headers=cabecalho(access)).status_code == 401


def test_sair_de_todos_derruba_todas_as_sessoes(cliente):
    email = email_unico()
    cadastro = cadastrar(cliente, email=email)
    outra = cliente.post(f"{API}/login", json={"email": email, "senha": SENHA}).json()

    access = cadastro["tokens"]["access_token"]
    assert cliente.post(f"{API}/sair-de-todos", headers=cabecalho(access)).status_code == 204

    outro_access = outra["tokens"]["access_token"]
    assert cliente.get(f"{API}/eu", headers=cabecalho(outro_access)).status_code == 401


def test_usuario_com_duas_empresas_precisa_escolher(cliente, db):
    email = email_unico()
    cadastrar(cliente, email=email, nome_empresa="Loja Um")
    usuario = por_email(db, email)
    segunda = criar_empresa_com_padroes(db, nome_fantasia="Loja Dois", usuario_dono_id=usuario.id)
    db.commit()

    login = cliente.post(f"{API}/login", json={"email": email, "senha": SENHA}).json()
    assert login["empresa_ativa_id"] is None
    assert len(login["empresas"]) == 2

    access = login["tokens"]["access_token"]
    sem_empresa = cliente.get(f"{API}/eu", headers=cabecalho(access))
    assert sem_empresa.status_code == 403
    assert sem_empresa.json()["erro"] == "empresa_nao_selecionada"

    troca = cliente.post(
        f"{API}/empresa-ativa",
        json={"empresa_id": str(segunda.empresa.id)},
        headers=cabecalho(access),
    )
    assert troca.status_code == 200
    novo_access = troca.json()["access_token"]

    eu = cliente.get(f"{API}/eu", headers=cabecalho(novo_access))
    assert eu.status_code == 200
    assert eu.json()["empresa"]["nome"] == "Loja Dois"

    # O token antigo, emitido antes da troca, deixa de valer
    assert cliente.get(f"{API}/empresas", headers=cabecalho(access)).status_code == 401


def test_nao_acessa_empresa_de_outra_pessoa(cliente):
    maria = cadastrar(cliente)
    joao = cadastrar(cliente)

    resposta = cliente.post(
        f"{API}/empresa-ativa",
        json={"empresa_id": maria["empresa_ativa_id"]},
        headers=cabecalho(joao["tokens"]["access_token"]),
    )
    assert resposta.status_code == 404


def test_requer_permissao_bloqueia_quem_nao_tem():
    contexto = Contexto(
        usuario_id=uuid.uuid4(),
        sessao_id=uuid.uuid4(),
        empresa_id=uuid.uuid4(),
        papel_id=uuid.uuid4(),
        papel_nome="Caixa",
        permissoes=frozenset({"membros.ver"}),
        limite_desconto_percentual=None,
    )
    assert requer_permissao("membros.ver")(contexto) is contexto
    with pytest.raises(PermissaoNegada):
        requer_permissao("papeis.gerenciar")(contexto)


def test_requer_permissao_com_codigo_inexistente_falha_na_definicao():
    with pytest.raises(ValueError):
        requer_permissao("nao.existe")

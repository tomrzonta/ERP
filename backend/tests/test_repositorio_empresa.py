import uuid

import pytest

from app.core.exceptions import NaoEncontrado
from app.modules.acesso.models import Papel
from app.modules.empresas.models import Empresa
from app.modules.usuarios.models import Usuario
from app.shared.repository import RepositorioDaEmpresa


class PapelRepositorio(RepositorioDaEmpresa[Papel]):
    modelo = Papel
    mensagem_nao_encontrado = "Papel não encontrado."


def criar_empresa(db) -> Empresa:
    empresa = Empresa(nome_fantasia="Loja", slug=f"loja-{uuid.uuid4().hex[:8]}")
    db.add(empresa)
    db.flush()
    return empresa


def test_obter_registro_de_outra_empresa_se_comporta_como_inexistente(db):
    empresa_a = criar_empresa(db)
    empresa_b = criar_empresa(db)

    papel_de_a = PapelRepositorio(db, empresa_a.id).adicionar(Papel(nome="Caixa"))

    repo_de_b = PapelRepositorio(db, empresa_b.id)
    assert repo_de_b.obter(papel_de_a.id) is None
    with pytest.raises(NaoEncontrado):
        repo_de_b.obter_ou_erro(papel_de_a.id)

    # Para a própria empresa, o mesmo registro aparece normalmente
    assert PapelRepositorio(db, empresa_a.id).obter(papel_de_a.id) is not None


def test_listar_e_contar_veem_apenas_a_propria_empresa(db):
    empresa_a = criar_empresa(db)
    empresa_b = criar_empresa(db)

    repo_a = PapelRepositorio(db, empresa_a.id)
    repo_b = PapelRepositorio(db, empresa_b.id)
    repo_a.adicionar(Papel(nome="Caixa"))
    repo_a.adicionar(Papel(nome="Estoquista"))
    repo_b.adicionar(Papel(nome="Caixa"))

    assert repo_a.contar() == 2
    assert repo_b.contar() == 1
    assert {papel.nome for papel in repo_b.listar()} == {"Caixa"}


def test_adicionar_preenche_a_empresa_do_repositorio(db):
    empresa = criar_empresa(db)
    papel = PapelRepositorio(db, empresa.id).adicionar(Papel(nome="Gerente"))
    assert papel.empresa_id == empresa.id


def test_adicionar_registro_de_outra_empresa_e_recusado(db):
    empresa_a = criar_empresa(db)
    empresa_b = criar_empresa(db)

    with pytest.raises(RuntimeError):
        PapelRepositorio(db, empresa_b.id).adicionar(
            Papel(empresa_id=empresa_a.id, nome="Caixa")
        )


def test_filtro_do_modulo_continua_restrito_a_empresa(db):
    empresa_a = criar_empresa(db)
    empresa_b = criar_empresa(db)
    PapelRepositorio(db, empresa_a.id).adicionar(Papel(nome="Caixa"))
    PapelRepositorio(db, empresa_b.id).adicionar(Papel(nome="Caixa"))

    repo_b = PapelRepositorio(db, empresa_b.id)
    consulta = repo_b.selecionar().where(Papel.nome == "Caixa")
    encontrados = list(db.scalars(consulta))

    assert len(encontrados) == 1
    assert encontrados[0].empresa_id == empresa_b.id


def test_repositorio_de_tabela_sem_empresa_falha_na_definicao():
    with pytest.raises(TypeError):

        class UsuarioRepositorio(RepositorioDaEmpresa[Usuario]):
            modelo = Usuario


def test_repositorio_sem_modelo_falha_na_definicao():
    with pytest.raises(TypeError):

        class SemModelo(RepositorioDaEmpresa[Papel]):
            pass

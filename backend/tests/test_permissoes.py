import pytest

from app.core.permissions import FORMATO_CODIGO, catalogo, validar_codigos
from app.modules.acesso.papeis_padrao import DONO, PAPEIS_PADRAO


def test_catalogo_carrega_com_codigos_validos():
    codigos = catalogo()
    assert codigos
    assert all(FORMATO_CODIGO.match(codigo) for codigo in codigos)


def test_papeis_padrao_usam_apenas_permissoes_do_catalogo():
    for papel in PAPEIS_PADRAO:
        validar_codigos(papel.permissoes)


def test_somente_o_dono_e_protegido():
    protegidos = [papel.codigo for papel in PAPEIS_PADRAO if papel.protegido]
    assert protegidos == [DONO]


def test_recusa_permissao_desconhecida():
    with pytest.raises(ValueError):
        validar_codigos({"membros.ver", "nao.existe"})

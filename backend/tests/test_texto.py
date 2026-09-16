from app.shared.texto import gerar_slug


def test_remove_acentos_e_simbolos():
    assert gerar_slug("Café & Cia") == "cafe-cia"


def test_nome_vazio_vira_loja():
    assert gerar_slug("  !!! ") == "loja"


def test_limita_tamanho_sem_hifen_no_final():
    slug = gerar_slug("a" * 49 + " bbbb")
    assert len(slug) <= 50
    assert not slug.endswith("-")

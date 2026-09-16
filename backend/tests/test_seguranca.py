from app.shared import seguranca


def test_mascara_senha_em_url_malformada(monkeypatch):
    monkeypatch.setattr(
        seguranca.settings,
        "database_url",
        "postgresql+psycopg://u:x@SenhaSecreta123@host:5432/db",
    )
    mensagem = "failed to resolve host 'SenhaSecreta123@host'"
    assert "SenhaSecreta123" not in seguranca.mascarar_segredos(mensagem)

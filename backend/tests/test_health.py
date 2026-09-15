from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_api_e_banco():
    resposta = client.get("/api/v1/health")
    assert resposta.status_code == 200
    assert resposta.json()["banco"] == "ok"

from propan.settings import get_settings
from propan.web.app import create_app


def _client(monkeypatch):
    monkeypatch.setenv("FT_ENGINE_PROFIT_URL", "")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    get_settings.cache_clear()
    app = create_app()
    app.testing = True
    return app.test_client()


def test_homepage(monkeypatch):
    client = _client(monkeypatch)
    response = client.get("/")
    assert response.status_code == 200
    assert "HAL 9000" in response.get_data(as_text=True)


def test_health_endpoint(monkeypatch):
    client = _client(monkeypatch)
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["profit"]["status"] == "disabled"
    assert payload["groq"]["status"] == "disabled"
    assert "thought" in payload
    assert payload["audio"]["available"] is False


def test_profit_disabled(monkeypatch):
    client = _client(monkeypatch)
    response = client.get("/api/profit")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "disabled"

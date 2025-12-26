from typer.testing import CliRunner

from propan.cli import app
from propan.settings import get_settings

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "HAL/Ouroboros" in result.stdout


def test_doctor_reports_missing_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("FT_ENGINE_PROFIT_URL", "")
    get_settings.cache_clear()

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 1
    assert "GROQ_API_KEY" in result.stdout

from pathlib import Path

from propan.settings import Settings, get_settings


def test_settings_parsing(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test")
    monkeypatch.setenv("HAL_VOICE", "fr-FR-Test")
    monkeypatch.setenv("HAL_SELF_IMPROVE", "true")
    monkeypatch.setenv("HAL_SELF_IMPROVE_EVERY", "9")
    monkeypatch.setenv("HAL_SPEECH_FILE", "custom.mp3")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("FT_ENGINE_PROFIT_URL", "")

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.groq_api_key == "test"
    assert settings.hal_voice == "fr-FR-Test"
    assert settings.hal_self_improve is True
    assert settings.hal_self_improve_every == 9
    assert settings.hal_speech_file.name == "custom.mp3"
    assert settings.log_level == "DEBUG"


def _resolve_alias(field) -> str:
    alias = field.validation_alias
    if isinstance(alias, str):
        return alias
    if hasattr(alias, "choices") and alias.choices:
        return alias.choices[0]
    return field.alias or field.name


def test_env_example_covers_settings():
    env_example = Path(__file__).resolve().parents[1] / ".env.example"
    content = env_example.read_text(encoding="utf-8")
    keys = {
        line.split("=", 1)[0].strip()
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    expected = {_resolve_alias(field) for field in Settings.model_fields.values()}
    assert expected <= keys

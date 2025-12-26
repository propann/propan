from propan.settings import get_settings


def test_settings_parsing(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test")
    monkeypatch.setenv("HAL_VOICE", "fr-FR-Test")
    monkeypatch.setenv("HAL_SELF_IMPROVE_EVERY", "9")
    monkeypatch.setenv("HAL_SPEECH_FILE", "custom.mp3")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("FT_ENGINE_PROFIT_URL", "")

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.groq_api_key == "test"
    assert settings.hal_voice == "fr-FR-Test"
    assert settings.hal_self_improve_every == 9
    assert settings.hal_speech_file.name == "custom.mp3"
    assert settings.log_level == "DEBUG"

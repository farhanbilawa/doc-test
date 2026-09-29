from src.utils.config import load_config


def test_ollama_environment_overrides_are_loaded(monkeypatch, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "ollama:\n  enabled: false\n  url: http://127.0.0.1:11434\n  model: lokal\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OLLAMA_ENABLED", "true")
    monkeypatch.setenv("OLLAMA_URL", "https://ollama.com")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen-cloud")
    monkeypatch.setenv("OLLAMA_API_KEY", "rahasia")

    ollama = load_config(config_file)["ollama"]

    assert ollama["enabled"] is True
    assert ollama["url"] == "https://ollama.com"
    assert ollama["model"] == "qwen-cloud"
    assert ollama["api_key"] == "rahasia"


def test_aivene_environment_overrides_are_loaded(monkeypatch, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("ai:\n  provider: ollama\n", encoding="utf-8")
    monkeypatch.setenv("AI_PROVIDER", "aivene")
    monkeypatch.setenv("AIVENE_ENABLED", "true")
    monkeypatch.setenv("AIVENE_BASE_URL", "https://api.aivene.com/v1")
    monkeypatch.setenv("AIVENE_MODEL", "gpt-6-astra")
    monkeypatch.setenv("AIVENE_API_KEY", "rahasia")

    config = load_config(config_file)

    assert config["ai"]["provider"] == "aivene"
    assert config["aivene"]["enabled"] is True
    assert config["aivene"]["base_url"] == "https://api.aivene.com/v1"
    assert config["aivene"]["model"] == "gpt-6-astra"
    assert config["aivene"]["api_key"] == "rahasia"

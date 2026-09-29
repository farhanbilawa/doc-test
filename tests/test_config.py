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

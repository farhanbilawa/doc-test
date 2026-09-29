from src.models import ValidationResult
from src.services.ollama_service import OllamaService


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_ollama_detects_configured_qwen(monkeypatch):
    monkeypatch.setattr(
        "src.services.ollama_service.requests.get",
        lambda *args, **kwargs: FakeResponse({"models": [{"name": "qwen3.5:4b"}]}),
    )
    service = OllamaService({"model": "qwen3.5:4b"})
    assert service.available_models() == ["qwen3.5:4b"]
    assert service.is_ready() is True


def test_ollama_uses_qwen_without_thinking_and_returns_indonesian(monkeypatch):
    captured = {}

    def fake_post(url, json, headers, timeout):
        captured.update({"url": url, "json": json, "headers": headers, "timeout": timeout})
        return FakeResponse({"response": "Anomali: tipe data berbeda."})

    monkeypatch.setattr("src.services.ollama_service.requests.post", fake_post)
    finding = ValidationResult(
        rule_id="R3", category="Tipe Data", object_name="model.kolom",
        expected="DATE", actual="STRING", status="FAIL",
        explanation="Berbeda.", evidence="QA=DATE; dbt=STRING",
    )
    service = OllamaService({"model": "qwen3.5:4b", "timeout_seconds": 60})

    assert service.explain(finding) == "Anomali: tipe data berbeda."
    assert captured["json"]["model"] == "qwen3.5:4b"
    assert captured["json"]["think"] is False
    assert "Bahasa Indonesia" in captured["json"]["prompt"]


def test_ollama_returns_structured_header_mapping(monkeypatch):
    captured = {}

    def fake_post(url, json, headers, timeout):
        captured.update({"json": json, "headers": headers})
        return FakeResponse({
            "response": '{"mappings":[{"source_header":"DTYPE","target_field":"expected_data_type","confidence":0.97,"reason":"Singkatan tipe data."}]}'
        })

    monkeypatch.setattr("src.services.ollama_service.requests.post", fake_post)
    service = OllamaService({"model": "qwen3.5:4b"})
    mappings = service.suggest_column_mapping({"DTYPE": ["BIGINT", "DATE"]})
    assert mappings[0]["target_field"] == "expected_data_type"
    assert captured["json"]["format"]["type"] == "object"
    assert captured["json"]["think"] is False


def test_ollama_sends_bearer_token_without_exposing_it_in_url(monkeypatch):
    captured = {}

    def fake_get(url, headers, timeout):
        captured.update({"url": url, "headers": headers, "timeout": timeout})
        return FakeResponse({"models": [{"name": "qwen-cloud"}]})

    monkeypatch.setattr("src.services.ollama_service.requests.get", fake_get)
    service = OllamaService({
        "url": "https://ollama.com",
        "model": "qwen-cloud",
        "api_key": "rahasia",
    })

    assert service.is_ready() is True
    assert captured["url"] == "https://ollama.com/api/tags"
    assert captured["headers"] == {"Authorization": "Bearer rahasia"}
    assert "rahasia" not in captured["url"]

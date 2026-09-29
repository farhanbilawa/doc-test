from src.services.ai_factory import create_ai_service, selected_ai_provider
from src.services.aivene_service import AiveneService


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_factory_selects_aivene_provider():
    config = {
        "ai": {"provider": "aivene"},
        "aivene": {"model": "gpt-6-astra", "api_key": "rahasia"},
    }

    service = create_ai_service(config)

    assert selected_ai_provider(config) == "aivene"
    assert isinstance(service, AiveneService)
    assert service.model == "gpt-6-astra"


def test_aivene_lists_models_with_bearer_token(monkeypatch):
    captured = {}

    def fake_get(url, headers, timeout):
        captured.update({"url": url, "headers": headers})
        return FakeResponse({"data": [{"id": "gpt-6-astra"}, {"id": "model-lain"}]})

    monkeypatch.setattr("src.services.aivene_service.requests.get", fake_get)
    service = AiveneService({"model": "gpt-6-astra", "api_key": "rahasia"})

    assert service.is_ready() is True
    assert captured["url"] == "https://api.aivene.com/v1/models"
    assert captured["headers"] == {"Authorization": "Bearer rahasia"}


def test_aivene_maps_headers_through_chat_completions(monkeypatch):
    captured = {}

    def fake_post(url, json, headers, timeout):
        captured.update({"url": url, "json": json, "headers": headers})
        return FakeResponse({
            "choices": [{
                "message": {
                    "content": '{"mappings":[{"source_header":"ASSET_SCOPE","target_field":"model_name","confidence":0.94}]}'
                }
            }]
        })

    monkeypatch.setattr("src.services.aivene_service.requests.post", fake_post)
    service = AiveneService({"model": "gpt-6-astra", "api_key": "rahasia"})

    mappings = service.suggest_column_mapping({"ASSET_SCOPE": ["dim_customer"]})

    assert mappings[0]["target_field"] == "model_name"
    assert captured["url"] == "https://api.aivene.com/v1/chat/completions"
    assert captured["json"]["model"] == "gpt-6-astra"
    assert captured["json"]["stream"] is False
    assert captured["headers"]["Authorization"] == "Bearer rahasia"
    assert captured["json"]["max_completion_tokens"] == 700
    assert service.last_error is None


def test_aivene_scales_mapping_output_budget_for_many_headers(monkeypatch):
    captured = {}

    def fake_post(url, json, headers, timeout):
        captured.update({"json": json})
        return FakeResponse({"choices": [{"message": {"content": '{"mappings":[]}'}}]})

    monkeypatch.setattr("src.services.aivene_service.requests.post", fake_post)
    service = AiveneService({"model": "gpt-6-astra", "api_key": "rahasia"})
    headers = {f"HEADER_{index}": [str(index)] for index in range(10)}

    service.suggest_column_mapping(headers)

    assert captured["json"]["max_completion_tokens"] == 1200

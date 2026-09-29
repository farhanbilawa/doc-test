from __future__ import annotations

import requests

from src.services.ollama_service import OllamaService


class AiveneService(OllamaService):
    """OpenAI-compatible Aivene client with the same interface as OllamaService."""

    provider_name = "Aivene"

    def __init__(self, config: dict):
        adapted = {
            "url": config.get("base_url", "https://api.aivene.com/v1"),
            "model": config.get("model", "gpt-6-astra"),
            "timeout_seconds": config.get("timeout_seconds", 120),
            "api_key": config.get("api_key", ""),
        }
        super().__init__(adapted)

    def available_models(self) -> list[str]:
        """Return model IDs from the OpenAI-compatible models endpoint."""
        self.last_error = None
        if not self.api_key:
            self.last_error = "AIVENE_API_KEY belum dikonfigurasi."
            return []
        try:
            response = requests.get(
                f"{self.url}/models",
                headers=self.headers,
                timeout=min(self.timeout, 10),
            )
            response.raise_for_status()
            items = response.json().get("data", [])
            return [
                str(item.get("id"))
                for item in items
                if isinstance(item, dict) and item.get("id")
            ]
        except requests.RequestException as exc:
            self._record_request_error(exc)
            return []
        except (ValueError, TypeError, AttributeError) as exc:
            self.last_error = f"Daftar model Aivene tidak dapat dibaca: {exc}"
            return []

    @staticmethod
    def _response_text(payload: dict) -> str:
        choices = payload.get("choices") or []
        if choices and isinstance(choices[0], dict):
            message = choices[0].get("message") or {}
            if isinstance(message, dict) and message.get("content"):
                return str(message["content"]).strip()
        return ""

    def _chat(self, prompt: str, *, options: dict, schema: dict | None = None, timeout: float) -> str:
        payload: dict = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        if "temperature" in options:
            payload["temperature"] = options["temperature"]
        if "num_predict" in options:
            payload["max_completion_tokens"] = options["num_predict"]

        response = requests.post(
            f"{self.url}/chat/completions",
            json=payload,
            headers={**self.headers, "Content-Type": "application/json"},
            timeout=timeout,
        )
        response.raise_for_status()
        return self._response_text(response.json())

from __future__ import annotations

from src.services.aivene_service import AiveneService
from src.services.ollama_service import OllamaService


def selected_ai_provider(config: dict) -> str:
    return str((config.get("ai") or {}).get("provider", "ollama")).strip().lower()


def ai_is_enabled(config: dict) -> bool:
    provider = selected_ai_provider(config)
    section = config.get(provider) or {}
    return bool(section.get("enabled", False))


def create_ai_service(config: dict) -> OllamaService:
    provider = selected_ai_provider(config)
    if provider == "aivene":
        return AiveneService(config.get("aivene") or {})
    if provider != "ollama":
        raise ValueError(f"Provider AI tidak didukung: {provider}")
    return OllamaService(config.get("ollama") or {})

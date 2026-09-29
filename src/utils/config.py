from __future__ import annotations

import os
from pathlib import Path

import yaml


def load_config(path: str | Path = "config.yaml") -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("config.yaml harus berisi mapping.")

    # Streamlit Community Cloud exposes root-level secrets as environment
    # variables.  This keeps local defaults in config.yaml while allowing a
    # deployment to select a reachable Ollama endpoint without committing
    # credentials to Git.
    ollama = data.setdefault("ollama", {})
    environment_mapping = {
        "OLLAMA_URL": "url",
        "OLLAMA_MODEL": "model",
        "OLLAMA_API_KEY": "api_key",
        "OLLAMA_TIMEOUT_SECONDS": "timeout_seconds",
    }
    for environment_name, config_name in environment_mapping.items():
        value = os.getenv(environment_name)
        if value:
            ollama[config_name] = value

    enabled = os.getenv("OLLAMA_ENABLED")
    if enabled:
        ollama["enabled"] = enabled.strip().lower() in {"1", "true", "yes", "on"}
    return data

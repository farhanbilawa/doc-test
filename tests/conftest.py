from __future__ import annotations

from pathlib import Path

import pytest

from src.parsers import parse_manifest
from src.utils.config import load_config


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def config():
    return load_config(ROOT / "config.yaml")


@pytest.fixture
def sample_project():
    return parse_manifest(ROOT / "sample_data" / "manifest.json")


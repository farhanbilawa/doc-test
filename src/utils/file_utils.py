from __future__ import annotations

import json
from pathlib import Path
from typing import BinaryIO

import yaml


class UserInputError(ValueError):
    """Readable error caused by an invalid user-supplied artifact."""


def read_bytes(source: bytes | BinaryIO | str | Path) -> bytes:
    if isinstance(source, bytes):
        return source
    if isinstance(source, (str, Path)):
        return Path(source).read_bytes()
    source.seek(0)
    return source.read()


def load_json(source: bytes | BinaryIO | str | Path) -> dict:
    try:
        data = json.loads(read_bytes(source).decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UserInputError(f"JSON tidak valid: {exc}") from exc
    if not isinstance(data, dict):
        raise UserInputError("JSON harus memiliki object pada tingkat teratas.")
    return data


def load_yaml(source: bytes | BinaryIO | str | Path) -> dict:
    try:
        data = yaml.safe_load(read_bytes(source).decode("utf-8-sig"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise UserInputError(f"YAML tidak valid: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise UserInputError("YAML harus memiliki mapping pada tingkat teratas.")
    return data


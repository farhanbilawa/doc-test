from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, BinaryIO, Iterable

from src.models import QARequirement
from src.utils.normalization import (
    canonical_header, clean_name, normalize_test_name, parse_bool, parse_int,
)


class QAParser(ABC):
    @abstractmethod
    def parse(
        self,
        source: bytes | BinaryIO | str | Path,
        header_mapping: dict[str, str] | None = None,
    ) -> list[QARequirement]:
        raise NotImplementedError


def requirements_from_rows(
    rows: Iterable[dict[Any, Any]],
    location: str,
    header_mapping: dict[str, str] | None = None,
) -> list[QARequirement]:
    requirements: list[QARequirement] = []
    active_model: str | None = None
    for index, raw_row in enumerate(rows, start=2):
        row: dict[str, Any] = {}
        for header, value in raw_row.items():
            header_text = str(header).strip()
            key = (header_mapping or {}).get(header_text) or canonical_header(header)
            if key:
                row[key] = value
        if not row:
            continue
        model = clean_name(row.get("model_name") or row.get("target_name"))
        if model:
            active_model = model
        column = clean_name(row.get("column_name"))
        test_name = normalize_test_name(clean_name(row.get("expected_test")))
        not_null = parse_bool(row.get("expected_not_null"))
        nullable = parse_bool(row.get("expected_nullable"))
        unique = parse_bool(row.get("expected_unique"))
        if test_name == "not_null":
            not_null = True
        elif test_name == "unique":
            unique = True
        requirement = QARequirement(
            object_type="column" if column else ("test" if test_name else "model"),
            model_name=active_model,
            source_name=clean_name(row.get("source_name")),
            target_name=clean_name(row.get("target_name")),
            column_name=column,
            expected_data_type=clean_name(row.get("expected_data_type")),
            expected_nullable=nullable,
            expected_not_null=not_null,
            expected_unique=unique,
            expected_row_count=parse_int(row.get("expected_row_count")),
            actual_row_count=parse_int(row.get("actual_row_count")),
            expected_test=test_name,
            qa_status=clean_name(row.get("qa_status")),
            complete_schema=parse_bool(row.get("complete_schema")) is True,
            raw_text=" | ".join(f"{k}: {v}" for k, v in raw_row.items() if clean_name(v)),
            source_location=f"{location}, baris {index}",
        )
        meaningful = any([
            requirement.model_name, requirement.column_name, requirement.expected_test,
            requirement.expected_row_count is not None, requirement.source_name,
        ])
        if meaningful:
            requirements.append(requirement)
    return requirements


def requirements_from_text(text: str, location: str) -> list[QARequirement]:
    """Parse common key/value and compact column definition patterns."""
    requirements: list[QARequirement] = []
    current_model: str | None = None
    complete_schema = bool(re.search(r"complete\s+schema\s*[:=]?\s*(yes|true|y|1)", text, re.I))
    model_pattern = re.compile(r"^\s*(?:model|table|target)\s*[:=]\s*([\w.\-]+)\s*$", re.I)
    row_pattern = re.compile(
        r"^\s*([A-Za-z_][\w]*)\s+([A-Za-z]+(?:\s*\([^)]*\))?)"
        r"(?:\s+(.*))?$", re.I,
    )
    for line_number, line in enumerate(text.splitlines(), start=1):
        line = line.strip(" \t|-")
        if not line:
            continue
        match = model_pattern.match(line)
        if match:
            current_model = match.group(1)
            requirements.append(QARequirement(
                object_type="model", model_name=current_model,
                complete_schema=complete_schema, raw_text=line,
                source_location=f"{location}, baris {line_number}",
            ))
            continue
        match = row_pattern.match(line)
        if not match or not current_model:
            continue
        column, data_type, modifiers = match.groups()
        modifier_text = modifiers or ""
        # Avoid interpreting prose/headings as column definitions.
        known_type = re.match(
            r"^(?:bigint|smallint|tinyint|int|integer|varchar|varchar2|char|string|text|"
            r"date|timestamp|datetime|decimal|numeric|number|float|double|real|boolean|bool)",
            data_type, re.I,
        )
        if not known_type:
            continue
        requirements.append(QARequirement(
            object_type="column", model_name=current_model, column_name=column,
            expected_data_type=data_type, expected_not_null=bool(re.search(r"not\s+null", modifier_text, re.I)),
            expected_unique=bool(re.search(r"\bunique\b", modifier_text, re.I)),
            complete_schema=complete_schema, raw_text=line,
            source_location=f"{location}, baris {line_number}",
        ))
    return requirements

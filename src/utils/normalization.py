from __future__ import annotations

import re
from typing import Any


ALIASES = {
    "table": "model_name", "model": "model_name", "model name": "model_name",
    "tbl obj": "model_name", "table object": "model_name",
    "target": "target_name", "target table": "target_name",
    "source": "source_name", "source table": "source_name",
    "column": "column_name", "field": "column_name", "column name": "column_name",
    "field nm": "column_name", "field name": "column_name",
    "data type": "expected_data_type", "datatype": "expected_data_type", "type": "expected_data_type",
    "target fmt": "expected_data_type", "target format": "expected_data_type",
    "nullable": "expected_nullable", "not null": "expected_not_null",
    "required flag": "expected_not_null",
    "unique": "expected_unique", "expected row count": "expected_row_count",
    "unique flag": "expected_unique", "expected rows": "expected_row_count",
    "actual row count": "actual_row_count", "test": "expected_test",
    "observed rows": "actual_row_count",
    "validation": "expected_test", "result": "qa_status", "status": "qa_status",
    "complete schema": "complete_schema", "full layout": "complete_schema",
}


def clean_name(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return None
    return text


def normalized_key(value: Any) -> str:
    text = clean_name(value) or ""
    text = re.sub(r"[_\-]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def canonical_header(value: Any) -> str | None:
    return ALIASES.get(normalized_key(value))


def parse_bool(value: Any) -> bool | None:
    text = normalized_key(value)
    if text in {"yes", "y", "true", "1", "required", "present", "pass", "not null", "unique"}:
        return True
    if text in {"no", "n", "false", "0", "optional", "absent", "nullable"}:
        return False
    return None


def parse_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        if isinstance(value, float) and value != value:
            return None
        return int(float(str(value).replace(",", "").strip()))
    except (ValueError, TypeError):
        return None


def normalize_test_name(value: str | None) -> str | None:
    text = normalized_key(value)
    if not text:
        return None
    if "not null" in text or "notnull" in text:
        return "not_null"
    if "unique" in text or "uniqueness" in text:
        return "unique"
    if "accepted value" in text:
        return "accepted_values"
    if "relationship" in text or "foreign key" in text:
        return "relationships"
    return text.replace(" ", "_")

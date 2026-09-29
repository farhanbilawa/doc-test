from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Status = Literal["PASS", "WARNING", "FAIL"]


class ValidationResult(BaseModel):
    rule_id: str
    category: str
    object_name: str
    expected: str
    actual: str
    status: Status
    explanation: str
    evidence: str
    source: str | None = None
    suggested_review: str | None = None


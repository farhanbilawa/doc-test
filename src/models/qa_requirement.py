from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class QARequirement(BaseModel):
    """Normalized requirement extracted from any supported QA document."""

    model_config = ConfigDict(extra="ignore")

    object_type: str = "column"
    model_name: str | None = None
    source_name: str | None = None
    target_name: str | None = None
    column_name: str | None = None
    expected_data_type: str | None = None
    expected_nullable: bool | None = None
    expected_unique: bool | None = None
    expected_not_null: bool | None = None
    expected_row_count: int | None = None
    actual_row_count: int | None = None
    expected_test: str | None = None
    qa_status: str | None = None
    complete_schema: bool = False
    raw_text: str | None = None
    source_location: str | None = None


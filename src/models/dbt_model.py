from __future__ import annotations

from pydantic import BaseModel, Field


class DBTColumn(BaseModel):
    name: str
    data_type: str | None = None
    tests: set[str] = Field(default_factory=set)
    description: str | None = None


class DBTTest(BaseModel):
    unique_id: str
    test_name: str
    model_name: str | None = None
    column_name: str | None = None


class DBTTestResult(BaseModel):
    unique_id: str
    test_name: str | None = None
    model_name: str | None = None
    column_name: str | None = None
    status: str
    failures: int | None = None
    execution_time: float | None = None


class DBTModel(BaseModel):
    unique_id: str
    name: str
    schema_name: str | None = None
    database: str | None = None
    relation_name: str | None = None
    columns: dict[str, DBTColumn] = Field(default_factory=dict)
    tests: list[DBTTest] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    source_dependencies: list[str] = Field(default_factory=list)


class DBTProject(BaseModel):
    models: dict[str, DBTModel] = Field(default_factory=dict)
    sources: dict[str, dict] = Field(default_factory=dict)
    test_results: dict[str, DBTTestResult] = Field(default_factory=dict)


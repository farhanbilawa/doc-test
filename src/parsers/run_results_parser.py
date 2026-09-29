from __future__ import annotations

from src.models import DBTProject, DBTTestResult
from src.utils.file_utils import load_json


def parse_run_results(source, project: DBTProject) -> DBTProject:
    data = load_json(source)
    for result in data.get("results") or []:
        if not isinstance(result, dict):
            continue
        unique_id = result.get("unique_id") or (result.get("node") or {}).get("unique_id")
        if not unique_id:
            continue
        test = next((test for model in project.models.values() for test in model.tests if test.unique_id == unique_id), None)
        execution_time = result.get("execution_time")
        project.test_results[unique_id] = DBTTestResult(
            unique_id=unique_id, test_name=test.test_name if test else None,
            model_name=test.model_name if test else None, column_name=test.column_name if test else None,
            status=str(result.get("status") or "unknown").lower(), failures=result.get("failures"),
            execution_time=float(execution_time) if execution_time is not None else None,
        )
    return project


from __future__ import annotations

from src.models import DBTColumn, DBTModel, DBTProject, DBTTest
from src.utils.file_utils import load_yaml
from src.utils.normalization import normalize_test_name


def _test_name(item) -> str | None:
    if isinstance(item, str):
        return normalize_test_name(item)
    if isinstance(item, dict) and item:
        return normalize_test_name(next(iter(item)))
    return None


def apply_schema_yaml(source, project: DBTProject) -> DBTProject:
    data = load_yaml(source)
    for model_data in data.get("models") or []:
        if not isinstance(model_data, dict) or not model_data.get("name"):
            continue
        name = str(model_data["name"])
        model = project.models.get(name.lower())
        if not model:
            model = DBTModel(unique_id=f"schema.{name}", name=name)
            project.models[name.lower()] = model
        for column_data in model_data.get("columns") or []:
            if not isinstance(column_data, dict) or not column_data.get("name"):
                continue
            column_name = str(column_data["name"])
            key = column_name.lower()
            column = model.columns.get(key) or DBTColumn(name=column_name)
            column.data_type = column_data.get("data_type") or column.data_type
            column.description = column_data.get("description") or column.description
            test_items = list(column_data.get("tests") or []) + list(column_data.get("data_tests") or [])
            for constraint in column_data.get("constraints") or []:
                if isinstance(constraint, dict) and constraint.get("type"):
                    test_items.append(constraint["type"])
            for item in test_items:
                test_name = _test_name(item)
                if not test_name:
                    continue
                column.tests.add(test_name)
                if not any(t.test_name == test_name and t.column_name == column_name for t in model.tests):
                    model.tests.append(DBTTest(
                        unique_id=f"schema_test.{name}.{column_name}.{test_name}",
                        test_name=test_name, model_name=name, column_name=column_name,
                    ))
            model.columns[key] = column
    return project


from __future__ import annotations

from src.models import DBTColumn, DBTModel, DBTProject, DBTTest
from src.utils.file_utils import load_json
from src.utils.normalization import normalize_test_name


def _test_details(unique_id: str, node: dict) -> DBTTest:
    metadata = node.get("test_metadata") or {}
    kwargs = metadata.get("kwargs") or {}
    test_name = normalize_test_name(metadata.get("name") or node.get("name")) or "unknown_test"
    attached = node.get("attached_node") or ""
    model_name = kwargs.get("model")
    # attached_node is the most reliable cross-version link. Rendered kwargs can
    # contain adapter macros rather than a plain model name.
    if attached.startswith("model."):
        model_name = attached.split(".")[-1]
    elif isinstance(model_name, str):
        model_name = model_name.replace("ref('", "").replace("')", "").replace('ref("', "").replace('")', "")
    return DBTTest(
        unique_id=unique_id, test_name=test_name, model_name=model_name,
        column_name=kwargs.get("column_name") or node.get("column_name"),
    )


def parse_manifest(source) -> DBTProject:
    data = load_json(source)
    project = DBTProject()
    pending_tests: list[DBTTest] = []
    nodes = data.get("nodes") or {}
    if not isinstance(nodes, dict):
        nodes = {}
    for unique_id, node in nodes.items():
        if not isinstance(node, dict):
            continue
        resource_type = node.get("resource_type") or str(unique_id).split(".", 1)[0]
        if resource_type == "model":
            columns = {}
            for key, value in (node.get("columns") or {}).items():
                value = value if isinstance(value, dict) else {}
                name = str(value.get("name") or key)
                columns[name.lower()] = DBTColumn(
                    name=name, data_type=value.get("data_type"), description=value.get("description"),
                )
            depends_on = (node.get("depends_on") or {}).get("nodes") or []
            model = DBTModel(
                unique_id=unique_id, name=node.get("name") or unique_id.split(".")[-1],
                schema_name=node.get("schema"), database=node.get("database"),
                relation_name=node.get("relation_name"), columns=columns,
                depends_on=list(depends_on),
                source_dependencies=[item for item in depends_on if str(item).startswith("source.")],
            )
            project.models[model.name.lower()] = model
        elif resource_type == "test":
            test = _test_details(unique_id, node)
            pending_tests.append(test)
    project.sources = data.get("sources") or {}
    for test in pending_tests:
        model = project.models.get((test.model_name or "").lower())
        if model:
            model.tests.append(test)
            if test.column_name and test.column_name.lower() in model.columns:
                model.columns[test.column_name.lower()].tests.add(test.test_name)
    return project

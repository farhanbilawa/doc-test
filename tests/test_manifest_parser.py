from pathlib import Path

from src.parsers import apply_schema_yaml, parse_manifest, parse_run_results


ROOT = Path(__file__).resolve().parents[1]


def test_manifest_parsing_extracts_model_columns_tests_and_dependencies():
    project = parse_manifest(ROOT / "sample_data" / "manifest.json")
    model = project.models["dim_customer"]
    assert model.relation_name == "analytics_dev.qa_demo.dim_customer"
    assert set(model.columns) == {"customer_id", "customer_name", "birth_date", "religion_code"}
    assert model.columns["customer_id"].tests == {"not_null", "unique"}
    assert model.source_dependencies == ["source.synthetic.raw_customer"]


def test_schema_yaml_variations_are_merged(sample_project):
    project = apply_schema_yaml(ROOT / "sample_data" / "schema.yml", sample_project)
    assert project.models["dim_customer"].columns["customer_id"].tests == {"not_null", "unique"}


def test_run_results_are_optional_and_parse_when_supplied(sample_project):
    assert sample_project.test_results == {}
    project = parse_run_results(ROOT / "sample_data" / "run_results.json", sample_project)
    assert project.test_results["test.synthetic.unique_dim_customer_customer_id"].status == "pass"


def test_manifest_with_missing_optional_metadata_is_safe(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text('{"nodes":{"model.x.min":{"resource_type":"model","name":"min"}}}', encoding="utf-8")
    project = parse_manifest(path)
    assert project.models["min"].columns == {}


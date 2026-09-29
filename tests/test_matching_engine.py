from pathlib import Path

from src.models import QARequirement
from src.parsers import parse_qa_document, parse_run_results
from src.validator.matcher import MatchingEngine, summarize_results


ROOT = Path(__file__).resolve().parents[1]


def find(results, category, object_fragment):
    return next(item for item in results if item.category == category and object_fragment in item.object_name)


def test_model_column_datatype_and_test_matching(config, sample_project):
    requirements = parse_qa_document(ROOT / "sample_data" / "qa_requirements.csv", "qa_requirements.csv")
    results = MatchingEngine(config).validate(requirements, sample_project)
    assert find(results, "Nama Model", "dim_customer").status == "PASS"
    assert find(results, "Kolom", "customer_id").status == "PASS"
    assert find(results, "Tipe Data", "birth_date").status == "FAIL"
    assert find(results, "Pengujian", "customer_id not_null").status == "PASS"
    assert find(results, "Pengujian", "customer_id unique").status == "PASS"


def test_missing_test_is_failure(config, sample_project):
    requirement = QARequirement(model_name="dim_customer", column_name="birth_date", expected_unique=True)
    results = MatchingEngine(config).validate([requirement], sample_project)
    assert find(results, "Pengujian", "birth_date unique").status == "FAIL"


def test_extra_column_is_warning_for_complete_schema(config, sample_project):
    requirements = [
        QARequirement(model_name="dim_customer", column_name=name, complete_schema=True)
        for name in ("customer_id", "customer_name", "birth_date")
    ]
    results = MatchingEngine(config).validate(requirements, sample_project)
    assert find(results, "Kolom Tak Terduga", "religion_code").status == "WARNING"


def test_row_count_difference_uses_thresholds(config, sample_project):
    requirement = QARequirement(model_name="dim_customer", expected_row_count=1000, actual_row_count=999)
    results = MatchingEngine(config).validate([requirement], sample_project)
    assert find(results, "Jumlah Baris", "dim_customer").status == "WARNING"


def test_missing_run_results_is_warning(config, sample_project):
    requirement = QARequirement(model_name="dim_customer", column_name="customer_id", expected_unique=True)
    results = MatchingEngine(config).validate([requirement], sample_project)
    assert find(results, "Hasil Pengujian dbt", "customer_id unique").status == "WARNING"


def test_run_result_failure_is_failure(config, sample_project):
    project = parse_run_results(b'{"results":[{"unique_id":"test.synthetic.unique_dim_customer_customer_id","status":"fail","failures":2}]}', sample_project)
    requirement = QARequirement(model_name="dim_customer", column_name="customer_id", expected_unique=True)
    results = MatchingEngine(config).validate([requirement], project)
    assert find(results, "Hasil Pengujian dbt", "customer_id unique").status == "FAIL"


def test_missing_model_is_failure(config, sample_project):
    results = MatchingEngine(config).validate([QARequirement(model_name="missing_model")], sample_project)
    assert results[0].status == "FAIL"


def test_demo_overall_status_is_fail(config, sample_project):
    requirements = parse_qa_document(ROOT / "sample_data" / "qa_requirements.csv", "qa_requirements.csv")
    results = MatchingEngine(config).validate(requirements, sample_project)
    assert summarize_results(results)["overall_status"] == "FAIL"

from pathlib import Path

import pytest

from src.parsers import parse_qa_document


ROOT = Path(__file__).resolve().parents[1]


def test_csv_qa_parser_normalizes_common_headers():
    requirements = parse_qa_document(ROOT / "sample_data" / "qa_requirements.csv", "qa_requirements.csv")
    customer_id = next(item for item in requirements if item.column_name == "customer_id")
    assert customer_id.model_name == "dim_customer"
    assert customer_id.expected_not_null is True
    assert customer_id.expected_unique is True
    assert customer_id.expected_row_count == 1_201_432
    assert customer_id.complete_schema is True


def test_unsupported_qa_format_has_readable_error():
    with pytest.raises(ValueError, match="belum didukung"):
        parse_qa_document(b"anything", "qa.txt")


def test_empty_qa_document_is_rejected(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("Model,Column,Data Type\n", encoding="utf-8")
    with pytest.raises(ValueError, match="kosong"):
        parse_qa_document(path, "empty.csv")


def test_csv_accepts_confirmed_custom_header_mapping():
    content = b"OBJECT,COL,DTYPE,MANDATORY_FLAG,UNIQ_CHK\ndim_customer,customer_id,BIGINT,Y,Y\n"
    mapping = {
        "OBJECT": "model_name",
        "COL": "column_name",
        "DTYPE": "expected_data_type",
        "MANDATORY_FLAG": "expected_not_null",
        "UNIQ_CHK": "expected_unique",
    }
    requirements = parse_qa_document(content, "custom.csv", mapping)
    assert requirements[0].model_name == "dim_customer"
    assert requirements[0].column_name == "customer_id"
    assert requirements[0].expected_data_type == "BIGINT"
    assert requirements[0].expected_not_null is True
    assert requirements[0].expected_unique is True

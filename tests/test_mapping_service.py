from pathlib import Path

from src.parsers import inspect_tabular_headers, parse_qa_document
from src.services.mapping_service import create_mapping_rows, mapping_dict_from_rows
from src.utils.normalization import canonical_header


ROOT = Path(__file__).resolve().parents[1]


class FakeOllama:
    def suggest_column_mapping(self, headers):
        assert headers == {"DTYPE": ["BIGINT"]}
        return [{
            "source_header": "DTYPE",
            "target_field": "expected_data_type",
            "confidence": 0.96,
            "reason": "Singkatan tipe data.",
        }]


def test_mapping_combines_builtin_alias_and_ai_suggestion():
    rows = create_mapping_rows({"Model": ["dim_customer"], "DTYPE": ["BIGINT"]}, FakeOllama())
    mapping = mapping_dict_from_rows(rows)
    assert mapping == {"Model": "model_name", "DTYPE": "expected_data_type"}
    assert next(row for row in rows if row["Header Asli"] == "Model")["Keyakinan"] == 1.0


def test_sample_random_headers_have_deterministic_fallback_mapping():
    headers = {
        "TBL_OBJ": ["orders"],
        "FIELD_NM": ["order_id"],
        "TARGET_FMT": ["BIGINT"],
        "REQUIRED_FLAG": ["Y"],
        "UNIQUE_FLAG": ["Y"],
        "EXPECTED_ROWS": ["100"],
        "OBSERVED_ROWS": ["98"],
        "FULL_LAYOUT": ["Y"],
    }

    mapping = mapping_dict_from_rows(create_mapping_rows(headers))

    assert mapping == {
        "TBL_OBJ": "model_name",
        "FIELD_NM": "column_name",
        "TARGET_FMT": "expected_data_type",
        "REQUIRED_FLAG": "expected_not_null",
        "UNIQUE_FLAG": "expected_unique",
        "EXPECTED_ROWS": "expected_row_count",
        "OBSERVED_ROWS": "actual_row_count",
        "FULL_LAYOUT": "complete_schema",
    }


class CaseChangingOllama:
    def suggest_column_mapping(self, headers):
        return [{
            "source_header": " custom-field ",
            "target_field": "column_name",
            "confidence": 0.91,
        }]


def test_ai_header_matching_is_case_and_separator_insensitive():
    rows = create_mapping_rows({"CUSTOM_FIELD": ["order_id"]}, CaseChangingOllama())
    mapping = mapping_dict_from_rows(rows)
    assert mapping == {"CUSTOM_FIELD": "column_name"}
    assert rows[0]["Alasan"] == (
        "Nama header dan contoh nilainya paling sesuai dengan Nama Kolom."
    )


def test_blind_mapping_fixture_really_bypasses_builtin_aliases():
    fixture = ROOT / "sample_data" / "blind_ai_mapping_case" / "qa_blind_mapping.csv"
    headers = inspect_tabular_headers(fixture.read_bytes(), fixture.name)

    assert len(headers) == 10
    assert all(canonical_header(header) is None for header in headers)


def test_blind_mapping_fixture_parses_after_expected_ai_mapping():
    fixture = ROOT / "sample_data" / "blind_ai_mapping_case" / "qa_blind_mapping.csv"
    mapping = {
        "ASSET_SCOPE": "model_name",
        "MEMBER_TOKEN": "column_name",
        "PHYSICAL_FORM": "expected_data_type",
        "PRESENCE_GUARD": "expected_not_null",
        "COLLISION_GUARD": "expected_unique",
        "PLANNED_VOLUME": "expected_row_count",
        "SEEN_VOLUME": "actual_row_count",
        "AUTHORITATIVE_BLUEPRINT": "complete_schema",
    }

    requirements = parse_qa_document(fixture.read_bytes(), fixture.name, mapping)

    assert len(requirements) == 3
    assert requirements[0].model_name == "dim_customer"
    assert requirements[0].column_name == "customer_id"
    assert requirements[0].expected_not_null is True
    assert requirements[0].expected_unique is True
    assert requirements[0].expected_row_count == 1_201_432
    assert requirements[0].actual_row_count == 1_201_431
    assert requirements[0].complete_schema is True

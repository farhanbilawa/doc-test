from src.services.mapping_service import create_mapping_rows, mapping_dict_from_rows


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
    mapping = mapping_dict_from_rows(
        create_mapping_rows({"CUSTOM_FIELD": ["order_id"]}, CaseChangingOllama())
    )
    assert mapping == {"CUSTOM_FIELD": "column_name"}

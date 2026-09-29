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


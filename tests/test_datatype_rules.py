from src.validator.datatype_rules import compare_datatypes, normalize_datatype


def test_datatype_normalization_preserves_length():
    assert normalize_datatype(" varchar ( 100 ) ") == ("VARCHAR", (100,))


def test_exact_datatype_match(config):
    assert compare_datatypes("BIGINT", "BIGINT", config).status == "EXACT"


def test_compatible_datatype_requires_review(config):
    assert compare_datatypes("VARCHAR", "VARCHAR(100)", config).status == "COMPATIBLE"


def test_datatype_mismatch(config):
    assert compare_datatypes("DATE", "STRING", config).status == "MISMATCH"


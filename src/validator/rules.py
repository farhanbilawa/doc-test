from __future__ import annotations

from src.models import DBTModel, QARequirement, ValidationResult
from src.validator.datatype_rules import compare_datatypes


def result(rule_id: str, category: str, object_name: str, expected, actual, status: str,
           explanation: str, evidence: str, source: str | None = None,
           suggested_review: str | None = None) -> ValidationResult:
    return ValidationResult(
        rule_id=rule_id, category=category, object_name=object_name,
        expected=str(expected), actual=str(actual), status=status,
        explanation=explanation, evidence=evidence, source=source,
        suggested_review=suggested_review,
    )


def check_model_existence(requirement: QARequirement, model: DBTModel | None) -> ValidationResult:
    name = requirement.model_name or requirement.target_name or "Model tidak diketahui"
    exists = model is not None
    return result(
        "R1", "Nama Model", name, name, model.name if model else "Tidak ditemukan",
        "PASS" if exists else "FAIL",
        "Model ditemukan dalam metadata dbt." if exists else "Model yang diharapkan tidak ditemukan dalam metadata dbt.",
        model.unique_id if model else "Tidak ada node model yang cocok pada manifest/schema YAML.",
        requirement.source_location, "Pastikan nama model dan artefak dbt yang disertakan sudah benar." if not exists else None,
    )


def check_column_existence(requirement: QARequirement, model: DBTModel) -> ValidationResult:
    column = model.columns.get((requirement.column_name or "").lower())
    exists = column is not None
    return result(
        "R2", "Kolom", f"{model.name}.{requirement.column_name}", requirement.column_name,
        column.name if column else "Tidak ditemukan", "PASS" if exists else "FAIL",
        "Kolom ditemukan dalam metadata dbt." if exists else "Kolom yang diharapkan tidak ditemukan.",
        f"Kolom tersedia: {', '.join(c.name for c in model.columns.values()) or 'tidak ada'}",
        requirement.source_location, "Tinjau skema model atau spesifikasi QA." if not exists else None,
    )


def check_datatype(requirement: QARequirement, model: DBTModel, config: dict) -> ValidationResult:
    column = model.columns[(requirement.column_name or "").lower()]
    comparison = compare_datatypes(requirement.expected_data_type, column.data_type, config)
    status = {"EXACT": "PASS", "COMPATIBLE": "WARNING", "MISMATCH": "FAIL", "UNKNOWN": "WARNING"}[comparison.status]
    return result(
        "R3", "Tipe Data", f"{model.name}.{column.name}", requirement.expected_data_type or "Tidak dicantumkan",
        column.data_type or "Tidak tersedia", status, comparison.reason,
        f"QA={requirement.expected_data_type or 'tidak ada'}; dbt={column.data_type or 'tidak ada'}",
        requirement.source_location,
        "Pastikan tipe kolom beserta kebutuhan panjang/presisinya." if status != "PASS" else None,
    )


def check_test(requirement: QARequirement, model: DBTModel, test_name: str) -> ValidationResult:
    column_name = requirement.column_name or ""
    column = model.columns.get(column_name.lower())
    model_tests = {(item.test_name, (item.column_name or "").lower()) for item in model.tests}
    present = bool(column and test_name in column.tests) or (test_name, column_name.lower()) in model_tests
    return result(
        "R4" if test_name == "not_null" else "R5" if test_name == "unique" else "R6",
        "Pengujian", f"{model.name}.{column_name} {test_name}", "Wajib", "Tersedia" if present else "Tidak ditemukan",
        "PASS" if present else "FAIL",
        f"Pengujian wajib {test_name} tersedia." if present else f"Pengujian wajib {test_name} tidak ditemukan.",
        f"Pengujian terdeteksi: {', '.join(sorted(column.tests)) if column else 'kolom tidak tersedia'}",
        requirement.source_location, "Tambahkan atau pastikan pengujian data dbt yang diwajibkan." if not present else None,
    )


def check_row_count(requirement: QARequirement, config: dict) -> ValidationResult:
    expected, actual = requirement.expected_row_count, requirement.actual_row_count
    if actual is None:
        return result("R11", "Jumlah Baris", requirement.model_name or "Tidak diketahui", expected, "Tidak tersedia", "WARNING",
                      "Jumlah baris yang diharapkan tercantum, tetapi bukti aktual tidak tersedia.",
                      "Jumlah baris aktual tidak ditemukan.", requirement.source_location,
                      "Sertakan bukti eksekusi atau jumlah baris aktual.")
    delta = actual - expected
    percentage = abs(delta) / expected * 100 if expected else (0 if actual == 0 else 100)
    settings = config.get("row_count") or {}
    exact = bool(settings.get("exact_match_required", False))
    warning = float(settings.get("warning_percentage_threshold", 0.1))
    failure = float(settings.get("failure_percentage_threshold", 5.0))
    if delta == 0:
        status = "PASS"
    elif exact or percentage >= failure:
        status = "FAIL"
    else:
        status = "WARNING" if percentage >= warning or percentage < warning else "WARNING"
    return result("R11", "Jumlah Baris", requirement.model_name or "Tidak diketahui", expected, actual, status,
                  f"Selisih jumlah baris adalah {delta:+,} ({(delta / expected * 100) if expected else 0:+.6f}%).",
                  f"ambang peringatan={warning}%; ambang gagal={failure}%; harus sama persis={exact}",
                  requirement.source_location, "Pastikan apakah perbedaan jumlah baris dapat diterima." if status != "PASS" else None)

from __future__ import annotations

from collections import defaultdict

from src.models import DBTProject, QARequirement, ValidationResult
from src.utils.normalization import normalize_test_name
from src.validator.rules import (
    check_column_existence, check_datatype, check_model_existence, check_row_count, check_test, result,
)


class MatchingEngine:
    """Deterministic comparison engine; no AI participates in status decisions."""

    def __init__(self, config: dict):
        self.config = config

    def validate(self, requirements: list[QARequirement], project: DBTProject) -> list[ValidationResult]:
        output: list[ValidationResult] = []
        grouped: dict[str, list[QARequirement]] = defaultdict(list)
        for requirement in requirements:
            grouped[(requirement.model_name or requirement.target_name or "").lower()].append(requirement)

        for model_key, model_requirements in grouped.items():
            representative = model_requirements[0]
            model = project.models.get(model_key)
            output.append(check_model_existence(representative, model))
            if not model:
                continue
            output.extend(self._source_target_checks(model_requirements, model))
            expected_columns: set[str] = set()
            complete_schema = any(item.complete_schema for item in model_requirements)
            for requirement in model_requirements:
                if requirement.expected_row_count is not None:
                    output.append(check_row_count(requirement, self.config))
                if not requirement.column_name:
                    continue
                expected_columns.add(requirement.column_name.lower())
                column_check = check_column_existence(requirement, model)
                output.append(column_check)
                if column_check.status == "FAIL":
                    continue
                if requirement.expected_data_type:
                    output.append(check_datatype(requirement, model, self.config))
                else:
                    output.append(result(
                        "R10", "Bukti QA", f"{model.name}.{requirement.column_name} tipe data",
                        "Tipe data dicantumkan", "Tidak ada di QA", "WARNING",
                        "QA tidak mencantumkan tipe data sehingga perbandingan tidak dapat dilakukan.",
                        requirement.raw_text or "Tidak ada bukti tipe data", requirement.source_location,
                        "Tambahkan tipe data yang diharapkan ke dokumen QA.",
                    ))
                required_tests = set()
                if requirement.expected_not_null is True or requirement.expected_nullable is False:
                    required_tests.add("not_null")
                if requirement.expected_unique is True:
                    required_tests.add("unique")
                if requirement.expected_test:
                    normalized = normalize_test_name(requirement.expected_test)
                    if normalized:
                        required_tests.add(normalized)
                for test_name in sorted(required_tests):
                    test_check = check_test(requirement, model, test_name)
                    output.append(test_check)
                    if test_check.status == "PASS":
                        output.append(self._test_result_check(requirement, model, test_name, project))
            if complete_schema:
                ignored = {str(item).lower() for item in self.config.get("ignored_columns") or []}
                for extra in sorted(set(model.columns) - expected_columns - ignored):
                    output.append(result(
                        "R9", "Kolom Tak Terduga", f"{model.name}.{model.columns[extra].name}",
                        "Tidak ada dalam skema QA lengkap", "Tersedia di dbt", "WARNING",
                        "dbt memiliki kolom yang tidak tercantum dalam skema QA lengkap.",
                        f"Kolom tambahan: {model.columns[extra].name}", representative.source_location,
                        "Pastikan apakah kolom tambahan tersebut memang disengaja.",
                    ))
        return output

    def _test_result_check(self, requirement, model, test_name, project) -> ValidationResult:
        test = next((item for item in model.tests if item.test_name == test_name and
                     (item.column_name or "").lower() == (requirement.column_name or "").lower()), None)
        run_result = project.test_results.get(test.unique_id) if test else None
        if not run_result:
            return result("R7", "Hasil Pengujian dbt", f"{model.name}.{requirement.column_name} {test_name}",
                          "Hasil lulus", "Tidak tersedia", "WARNING",
                          "Pengujian wajib tersedia, tetapi hasil eksekusinya tidak disertakan.",
                          test.unique_id if test else "Tidak ada node pengujian yang terpetakan", requirement.source_location,
                          "Tinjau run_results.json terbaru sebelum deployment.")
        status = "PASS" if run_result.status in {"pass", "success"} else "FAIL" if run_result.status in {"fail", "error"} else "WARNING"
        explanation = f"dbt melaporkan status asli '{run_result.status}'."
        if requirement.qa_status and requirement.qa_status.lower() in {"pass", "passed", "success"} and status == "FAIL":
            explanation += " QA menyatakan PASS, sedangkan hasil dbt tidak lulus."
        return result("R7", "Hasil Pengujian dbt", f"{model.name}.{requirement.column_name} {test_name}",
                      "pass/success", run_result.status, status, explanation,
                      f"jumlah kegagalan={run_result.failures}; waktu eksekusi={run_result.execution_time}",
                      requirement.source_location, "Selidiki hasil pengujian dbt yang gagal atau belum lengkap." if status != "PASS" else None)

    def _source_target_checks(self, requirements, model) -> list[ValidationResult]:
        output = []
        for requirement in requirements:
            if requirement.target_name:
                target = requirement.target_name.lower()
                candidates = {model.name.lower(), (model.relation_name or "").lower()}
                comparable = any(target == item or item.endswith("." + target) for item in candidates if item)
                output.append(result("R8", "Target", model.name, requirement.target_name,
                                     model.relation_name or model.name, "PASS" if comparable else "WARNING",
                                     "Target sesuai dengan metadata dbt." if comparable else "Target tidak dapat dicocokkan secara meyakinkan.",
                                     f"model={model.name}; relasi={model.relation_name or 'tidak tersedia'}", requirement.source_location,
                                     None if comparable else "Pastikan penamaan target dan kualifikasi environment."))
            if requirement.source_name:
                source = requirement.source_name.lower()
                matches = [item for item in model.source_dependencies if item.lower().endswith("." + source)]
                status = "PASS" if matches else "WARNING"
                output.append(result("R8", "Sumber", model.name, requirement.source_name,
                                     ", ".join(model.source_dependencies) or "Tidak tersedia", status,
                                     "Dependensi sumber sesuai." if matches else "Metadata sumber tidak ada atau tidak dapat dibandingkan langsung.",
                                     f"dependensi={model.depends_on}", requirement.source_location,
                                     None if matches else "Tinjau lineage pada manifest dan dokumen QA."))
        return output


def summarize_results(results: list[ValidationResult]) -> dict[str, int | str]:
    counts = {status: sum(item.status == status for item in results) for status in ("PASS", "WARNING", "FAIL")}
    overall = "FAIL" if counts["FAIL"] else "WARNING" if counts["WARNING"] else "PASS"
    return {"overall_status": overall, "total": len(results), "passed": counts["PASS"],
            "warnings": counts["WARNING"], "failed": counts["FAIL"]}

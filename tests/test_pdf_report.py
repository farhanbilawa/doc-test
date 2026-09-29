from io import BytesIO

from pypdf import PdfReader

from src.models import ValidationResult
from src.services.pdf_report import build_pdf_report


def test_pdf_report_is_readable_and_contains_summary():
    finding = ValidationResult(
        rule_id="R3",
        category="Tipe Data",
        object_name="dim_customer.birth_date",
        expected="DATE",
        actual="STRING",
        status="FAIL",
        explanation="Kelompok tipe data tidak kompatibel.",
        evidence="QA=DATE; dbt=STRING",
        suggested_review="Pastikan definisinya.",
    )
    summary = {"overall_status": "FAIL", "total": 1, "passed": 0, "warnings": 0, "failed": 1}
    filenames = {"qa": "qa.csv", "manifest": "manifest.json", "run_results": None, "schema": None}

    report = build_pdf_report([finding], summary, filenames)

    assert report.startswith(b"%PDF-")
    reader = PdfReader(BytesIO(report))
    assert len(reader.pages) >= 1
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Laporan Validasi Deployment QA" in text
    assert "dim_customer.birth_date" in text
    assert "Peninjauan engineer" in text

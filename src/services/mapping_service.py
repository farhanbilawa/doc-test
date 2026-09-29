from __future__ import annotations

from src.services.ollama_service import OllamaService
from src.utils.normalization import canonical_header


FIELD_LABELS = {
    "ignore": "Abaikan",
    "model_name": "Nama Model/Tabel",
    "source_name": "Nama Sumber",
    "target_name": "Nama Target",
    "column_name": "Nama Kolom",
    "expected_data_type": "Tipe Data Diharapkan",
    "expected_nullable": "Boleh Null",
    "expected_not_null": "Wajib Terisi (Not Null)",
    "expected_unique": "Harus Unik",
    "expected_row_count": "Jumlah Baris Diharapkan",
    "actual_row_count": "Jumlah Baris Aktual",
    "expected_test": "Pengujian Diharapkan",
    "qa_status": "Status QA",
    "complete_schema": "Skema Lengkap",
}
LABEL_FIELDS = {label: field for field, label in FIELD_LABELS.items()}


def create_mapping_rows(
    header_samples: dict[str, list[str]],
    ollama: OllamaService | None = None,
) -> list[dict]:
    """Combine deterministic aliases with optional local-AI suggestions."""
    rows: list[dict] = []
    unknown: dict[str, list[str]] = {}
    for header, samples in header_samples.items():
        field = canonical_header(header)
        if field:
            rows.append({
                "Header Asli": header,
                "Dipetakan Ke": FIELD_LABELS[field],
                "Keyakinan": 1.0,
                "Alasan": "Dikenali oleh alias bawaan.",
            })
        else:
            unknown[header] = samples

    suggestions = ollama.suggest_column_mapping(unknown) if ollama and unknown else []
    by_header = {
        str(item.get("source_header", "")).strip(): item
        for item in suggestions
        if str(item.get("source_header", "")).strip() in unknown
    }
    for header in unknown:
        suggestion = by_header.get(header) or {}
        field = str(suggestion.get("target_field") or "ignore")
        if field not in FIELD_LABELS:
            field = "ignore"
        try:
            confidence = max(0.0, min(1.0, float(suggestion.get("confidence", 0))))
        except (TypeError, ValueError):
            confidence = 0.0
        rows.append({
            "Header Asli": header,
            "Dipetakan Ke": FIELD_LABELS[field],
            "Keyakinan": confidence,
            "Alasan": str(suggestion.get("reason") or ("Saran Qwen lokal." if suggestion else "Belum dapat dipetakan otomatis.")),
        })
    return rows


def mapping_dict_from_rows(rows: list[dict]) -> dict[str, str]:
    output = {}
    for row in rows:
        header = str(row.get("Header Asli") or "").strip()
        field = LABEL_FIELDS.get(str(row.get("Dipetakan Ke") or ""))
        if header and field and field != "ignore":
            output[header] = field
    return output

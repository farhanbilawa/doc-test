from __future__ import annotations

import json

import requests

from src.models import ValidationResult


class OllamaService:
    """Optional Ollama client. It never assigns validation status."""

    def __init__(self, config: dict):
        self.url = str(config.get("url", "http://127.0.0.1:11434")).rstrip("/")
        self.model = str(config.get("model", "llama3.2"))
        self.timeout = float(config.get("timeout_seconds", 10))
        self.api_key = str(config.get("api_key", "")).strip()

    @property
    def headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    def available_models(self) -> list[str]:
        """Return model tags exposed by the local Ollama service."""
        try:
            response = requests.get(
                f"{self.url}/api/tags",
                headers=self.headers,
                timeout=min(self.timeout, 5),
            )
            response.raise_for_status()
            return [
                str(item.get("name"))
                for item in response.json().get("models", [])
                if isinstance(item, dict) and item.get("name")
            ]
        except (requests.RequestException, ValueError, AttributeError):
            return []

    def is_ready(self) -> bool:
        return self.model in self.available_models()

    def explain(self, finding: ValidationResult) -> str:
        prompt = (
            "Jelaskan temuan validasi pipeline data deterministik berikut dalam Bahasa Indonesia. "
            "Bersikap konservatif dan jangan menyetujui atau menolak deployment. "
            "Berikan tiga bagian singkat: Anomali, Kemungkinan dampak, dan Rekomendasi peninjauan.\n"
            f"Kategori: {finding.category}\nObjek: {finding.object_name}\n"
            f"Diharapkan: {finding.expected}\nAktual: {finding.actual}\n"
            f"Status: {finding.status}\nBukti: {finding.evidence}"
        )
        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "think": False,
                    "options": {"temperature": 0.2, "num_predict": 300},
                },
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            text = response.json().get("response")
            return str(text).strip() if text else "Penjelasan AI tidak tersedia."
        except (requests.RequestException, ValueError):
            return "Penjelasan AI tidak tersedia."

    def suggest_column_mapping(self, headers: dict[str, list[str]]) -> list[dict]:
        """Map unfamiliar tabular headers to the normalized QA schema."""
        allowed_fields = [
            "model_name", "source_name", "target_name", "column_name",
            "expected_data_type", "expected_nullable", "expected_not_null",
            "expected_unique", "expected_row_count", "actual_row_count",
            "expected_test", "qa_status", "complete_schema", "ignore",
        ]
        compact_input = [
            {"header": header, "contoh": samples[:2]}
            for header, samples in headers.items()
        ]
        schema = {
            "type": "object",
            "properties": {
                "mappings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_header": {"type": "string"},
                            "target_field": {"type": "string", "enum": allowed_fields},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        },
                        "required": ["source_header", "target_field", "confidence"],
                    },
                }
            },
            "required": ["mappings"],
        }
        prompt = (
            "Petakan setiap header QA ke satu field internal. Jangan mengarang header; gunakan "
            "'ignore' jika tidak relevan. Kamus: model_name=nama model/tabel, source_name=sumber, "
            "target_name=target, column_name=nama kolom, expected_data_type=tipe data target, "
            "expected_nullable=boleh null, expected_not_null=wajib terisi, expected_unique=unik, "
            "expected_row_count=jumlah baris harapan, actual_row_count=jumlah baris aktual, "
            "expected_test=pengujian, qa_status=status QA, complete_schema=skema lengkap.\n"
            f"Input: {json.dumps(compact_input, ensure_ascii=False)}"
        )
        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "think": False,
                    "format": schema,
                    "options": {"temperature": 0, "num_predict": 320},
                },
                headers=self.headers,
                timeout=max(self.timeout, 120),
            )
            response.raise_for_status()
            raw = response.json().get("response") or "{}"
            parsed = json.loads(raw)
            mappings = parsed.get("mappings") or []
            return [item for item in mappings if isinstance(item, dict)]
        except (requests.RequestException, ValueError, TypeError, AttributeError):
            return []

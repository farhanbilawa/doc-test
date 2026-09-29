from __future__ import annotations

import json
from urllib.parse import urlparse

import requests

from src.models import ValidationResult


class OllamaService:
    """Optional Ollama client. It never assigns validation status."""

    provider_name = "Ollama"

    def __init__(self, config: dict):
        self.url = str(config.get("url", "http://127.0.0.1:11434")).rstrip("/")
        self.model = str(config.get("model", "llama3.2"))
        self.timeout = float(config.get("timeout_seconds", 10))
        self.api_key = str(config.get("api_key", "")).strip()
        self.last_error: str | None = None

    @property
    def headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    @property
    def is_cloud(self) -> bool:
        return urlparse(self.url).hostname in {"ollama.com", "www.ollama.com"}

    @staticmethod
    def _response_text(payload: dict) -> str:
        message = payload.get("message")
        if isinstance(message, dict) and message.get("content"):
            return str(message["content"]).strip()
        return str(payload.get("response") or "").strip()

    @staticmethod
    def _json_from_text(text: str) -> dict:
        """Parse plain or fenced JSON returned by models without schema enforcement."""
        candidate = text.strip()
        if candidate.startswith("```"):
            lines = candidate.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            candidate = "\n".join(lines).strip()
        start, end = candidate.find("{"), candidate.rfind("}")
        if start < 0 or end < start:
            raise ValueError("Respons tidak memuat objek JSON.")
        parsed = json.loads(candidate[start:end + 1])
        if not isinstance(parsed, dict):
            raise ValueError("Respons JSON bukan object.")
        return parsed

    def _chat(self, prompt: str, *, options: dict, schema: dict | None = None, timeout: float) -> str:
        payload: dict = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": options,
        }
        # Ollama Cloud belum mendukung structured outputs. Schema tetap
        # dicantumkan dalam prompt, tetapi field `format` hanya dikirim ke
        # Ollama lokal/gateway yang mendukungnya.
        if not self.is_cloud:
            payload["think"] = False
            if schema is not None:
                payload["format"] = schema
        response = requests.post(
            f"{self.url}/api/chat",
            json=payload,
            headers=self.headers,
            timeout=timeout,
        )
        response.raise_for_status()
        return self._response_text(response.json())

    def _record_request_error(self, exc: requests.RequestException) -> None:
        response = getattr(exc, "response", None)
        status = getattr(response, "status_code", None)
        detail = str(getattr(response, "text", "") or "").strip().replace("\n", " ")[:240]
        if status:
            self.last_error = f"Permintaan AI gagal (HTTP {status})"
            if detail:
                self.last_error += f": {detail}"
        else:
            self.last_error = f"Endpoint AI tidak dapat dihubungi: {exc}"

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
        self.last_error = None
        prompt = (
            "Jelaskan temuan validasi pipeline data deterministik berikut dalam Bahasa Indonesia. "
            "Bersikap konservatif dan jangan menyetujui atau menolak deployment. "
            "Berikan tiga bagian singkat: Anomali, Kemungkinan dampak, dan Rekomendasi peninjauan.\n"
            f"Kategori: {finding.category}\nObjek: {finding.object_name}\n"
            f"Diharapkan: {finding.expected}\nAktual: {finding.actual}\n"
            f"Status: {finding.status}\nBukti: {finding.evidence}"
        )
        try:
            text = self._chat(
                prompt,
                options={"temperature": 0.2, "num_predict": 300},
                timeout=self.timeout,
            )
            return str(text).strip() if text else "Penjelasan AI tidak tersedia."
        except requests.RequestException as exc:
            self._record_request_error(exc)
            return "Penjelasan AI tidak tersedia."
        except (ValueError, TypeError, AttributeError) as exc:
            self.last_error = f"Respons AI tidak dapat dibaca: {exc}"
            return "Penjelasan AI tidak tersedia."

    def suggest_column_mapping(self, headers: dict[str, list[str]]) -> list[dict]:
        """Map unfamiliar tabular headers to the normalized QA schema."""
        self.last_error = None
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
            "Balas HANYA dengan JSON valid sesuai schema berikut, tanpa markdown atau penjelasan lain:\n"
            f"{json.dumps(schema, ensure_ascii=False)}\n"
            f"Input: {json.dumps(compact_input, ensure_ascii=False)}"
        )
        try:
            raw = self._chat(
                prompt,
                options={"temperature": 0, "num_predict": 500},
                schema=schema,
                timeout=max(self.timeout, 120),
            )
            parsed = self._json_from_text(raw)
            mappings = parsed.get("mappings") or []
            if not isinstance(mappings, list):
                raise ValueError("Field mappings bukan array.")
            return [item for item in mappings if isinstance(item, dict)]
        except requests.RequestException as exc:
            self._record_request_error(exc)
            return []
        except (ValueError, TypeError, AttributeError, json.JSONDecodeError) as exc:
            self.last_error = f"Respons mapping AI tidak dapat dibaca: {exc}"
            return []

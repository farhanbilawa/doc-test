from __future__ import annotations

import json
import logging
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st

from src.parsers import (
    apply_schema_yaml, inspect_tabular_headers, parse_manifest, parse_qa_document,
    parse_run_results,
)
from src.services.mapping_service import FIELD_LABELS, create_mapping_rows, mapping_dict_from_rows
from src.services.ollama_service import OllamaService
from src.services.pdf_report import build_pdf_report
from src.utils.config import load_config
from src.utils.normalization import canonical_header
from src.validator.anomaly_detector import RuleBasedAnomalyDetector
from src.validator.matcher import MatchingEngine, summarize_results


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[logging.FileHandler(LOG_DIR / "validator.log", encoding="utf-8"), logging.StreamHandler()],
)
LOGGER = logging.getLogger("qa_validator")


def result_rows(results) -> list[dict]:
    return [{
        "Kategori": item.category, "Objek": item.object_name, "Diharapkan": item.expected,
        "Aktual": item.actual, "Status": item.status, "Bukti": item.evidence,
        "Penjelasan": item.explanation, "Saran Peninjauan": item.suggested_review or "",
        "ID Aturan": item.rule_id, "Sumber": item.source or "",
    } for item in results]


def build_json_report(results, summary, filenames: dict[str, str | None]) -> str:
    payload = {
        "waktu_utc": datetime.now(timezone.utc).isoformat(),
        "berkas": {
            "dokumen_qa": filenames.get("qa"),
            "manifest": filenames.get("manifest"),
            "hasil_eksekusi": filenames.get("run_results"),
            "skema_yaml": filenames.get("schema"),
        },
        "ringkasan": {
            "status_keseluruhan": summary["overall_status"],
            "total": summary["total"],
            "lulus": summary["passed"],
            "peringatan": summary["warnings"],
            "gagal": summary["failed"],
        },
        "hasil_validasi": [{
            "id_aturan": item.rule_id,
            "kategori": item.category,
            "objek": item.object_name,
            "diharapkan": item.expected,
            "aktual": item.actual,
            "status": item.status,
            "penjelasan": item.explanation,
            "bukti": item.evidence,
            "sumber": item.source,
            "saran_peninjauan": item.suggested_review,
        } for item in results],
        "catatan": "Validasi selesai. Peninjauan engineer tetap diperlukan.",
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def build_csv_report(results, summary, filenames: dict[str, str | None]) -> bytes:
    rows = result_rows(results)
    timestamp = datetime.now(timezone.utc).isoformat()
    for row in rows:
        row.update({
            "Waktu UTC": timestamp, "Berkas QA": filenames["qa"],
            "Berkas Manifest": filenames["manifest"], "Status Keseluruhan": summary["overall_status"],
        })
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")


st.set_page_config(page_title="Validator Deployment QA", page_icon="✅", layout="wide")
config = load_config()

with st.sidebar:
    st.header("Aplikasi")
    st.write("Validator Deployment QA")
    ai_enabled = st.toggle(
        "Fitur AI Ollama",
        value=bool((config.get("ollama") or {}).get("enabled", False)),
        help="Mengirim data terbatas ke endpoint Ollama yang dikonfigurasi untuk mapping dan penjelasan.",
    )
    st.caption("Seluruh validasi utama tetap deterministik dan diproses secara lokal.")
    if ai_enabled:
        ollama_status_service = OllamaService(config.get("ollama") or {})
        available_models = ollama_status_service.available_models()
        if ollama_status_service.model in available_models:
            st.success(f"Ollama siap · {ollama_status_service.model}")
        elif available_models:
            st.error(
                f"Model {ollama_status_service.model} tidak ditemukan. "
                f"Model tersedia: {', '.join(available_models)}"
            )
        else:
            st.error("Ollama tidak dapat dihubungi atau model tidak tersedia di endpoint yang dikonfigurasi.")

st.title("Validator Deployment QA")
st.write("Validasi dokumentasi QA terhadap metadata dbt sebelum deployment.")
st.info("Aplikasi ini adalah alat bantu pengambilan keputusan. Hasil validasi tidak mengesahkan deployment produksi.")

left, right = st.columns(2)
with left:
    st.subheader("1. Unggah dokumen QA")
    qa_file = st.file_uploader("Dokumen QA", type=["csv", "xlsx", "xls", "docx", "pdf"])
with right:
    st.subheader("2. Unggah artefak dbt")
    manifest_file = st.file_uploader("manifest.json", type=["json"], key="manifest")

st.subheader("3. Artefak opsional")
optional_left, optional_right = st.columns(2)
with optional_left:
    run_results_file = st.file_uploader("run_results.json", type=["json"], key="run_results")
with optional_right:
    schema_file = st.file_uploader("schema.yml / properties.yml", type=["yml", "yaml"], key="schema")

header_mapping: dict[str, str] = {}
if qa_file:
    header_samples = inspect_tabular_headers(qa_file.getvalue(), qa_file.name)
    if header_samples:
        file_signature = hashlib.sha256(qa_file.getvalue()).hexdigest()[:16]
        # Versi key mencegah hasil mapping lama tersimpan setelah kamus alias diperbarui.
        mapping_state_key = f"mapping_rows_v3_{file_signature}"
        mapping_ai_status_key = f"mapping_ai_status_v3_{file_signature}"
        if mapping_state_key not in st.session_state:
            mapping_ollama = None
            unknown_headers = [header for header in header_samples if canonical_header(header) is None]
            if ai_enabled and unknown_headers:
                candidate_service = OllamaService(config.get("ollama") or {})
                if candidate_service.is_ready():
                    mapping_ollama = candidate_service
                    with st.spinner(f"Model AI {candidate_service.model} sedang memetakan header QA..."):
                        st.session_state[mapping_state_key] = create_mapping_rows(header_samples, mapping_ollama)
                    if candidate_service.last_error:
                        st.session_state[mapping_ai_status_key] = {
                            "ok": False,
                            "message": candidate_service.last_error,
                        }
                    else:
                        st.session_state[mapping_ai_status_key] = {
                            "ok": True,
                            "message": f"Model AI {candidate_service.model} berhasil merespons mapping.",
                        }
            if mapping_state_key not in st.session_state:
                st.session_state[mapping_state_key] = create_mapping_rows(header_samples)

        mapping_rows = st.session_state[mapping_state_key]
        low_confidence = any(float(row.get("Keyakinan", 0)) < 0.75 for row in mapping_rows)
        with st.expander("Pemetaan kolom QA otomatis", expanded=low_confidence):
            st.caption(
                "Alias umum dipetakan langsung. Header yang tidak dikenal dipetakan oleh model AI "
                "menggunakan nama header dan maksimal dua contoh nilai pendek. Periksa mapping sebelum validasi."
            )
            mapping_ai_status = st.session_state.get(mapping_ai_status_key)
            if mapping_ai_status:
                if mapping_ai_status["ok"]:
                    st.success(mapping_ai_status["message"])
                else:
                    st.error(f"Mapping AI gagal. {mapping_ai_status['message']}")
            mapping_frame = pd.DataFrame(mapping_rows)
            # Nilai internal memakai rentang 0.0-1.0. UI menampilkan persen 0-100
            # agar 1.0 terbaca sebagai 100%, bukan 1%.
            mapping_frame["Keyakinan (%)"] = mapping_frame.pop("Keyakinan") * 100
            edited_mapping = st.data_editor(
                mapping_frame,
                key=f"mapping_editor_{file_signature}",
                hide_index=True,
                use_container_width=True,
                disabled=["Header Asli", "Keyakinan (%)", "Alasan"],
                column_config={
                    "Dipetakan Ke": st.column_config.SelectboxColumn(
                        "Dipetakan Ke",
                        options=list(FIELD_LABELS.values()),
                        required=True,
                    ),
                    "Keyakinan (%)": st.column_config.ProgressColumn(
                        "Keyakinan AI",
                        min_value=0.0,
                        max_value=100.0,
                        format="%.0f%%",
                    ),
                },
            )
            header_mapping = mapping_dict_from_rows(edited_mapping.to_dict(orient="records"))
            ignored_headers = [
                row["Header Asli"] for row in edited_mapping.to_dict(orient="records")
                if row.get("Dipetakan Ke") == FIELD_LABELS["ignore"]
            ]
            if ignored_headers:
                st.warning(f"Header yang diabaikan: {', '.join(ignored_headers)}")

if st.button("Jalankan Validasi", type="primary", use_container_width=True):
    if not qa_file or not manifest_file:
        st.error("Unggah dokumen QA dan manifest.json sebelum menjalankan validasi.")
    else:
        try:
            max_bytes = int(config.get("maximum_uploaded_file_size_mb", 25)) * 1024 * 1024
            uploads = [item for item in (qa_file, manifest_file, run_results_file, schema_file) if item]
            oversized = [item.name for item in uploads if len(item.getvalue()) > max_bytes]
            if oversized:
                raise ValueError(f"Berkas melebihi batas ukuran yang dikonfigurasi: {', '.join(oversized)}")

            LOGGER.info("Parsing dimulai untuk QA=%s dan manifest=%s", qa_file.name, manifest_file.name)
            requirements = parse_qa_document(qa_file.getvalue(), qa_file.name, header_mapping)
            project = parse_manifest(manifest_file.getvalue())
            if schema_file:
                project = apply_schema_yaml(schema_file.getvalue(), project)
            if run_results_file:
                project = parse_run_results(run_results_file.getvalue(), project)
            LOGGER.info("Parsing selesai: %d requirement, %d model", len(requirements), len(project.models))

            LOGGER.info("Validasi dimulai")
            results = MatchingEngine(config).validate(requirements, project)
            summary = summarize_results(results)
            LOGGER.info("Validasi selesai: %d pemeriksaan", len(results))
            st.session_state["ai_explanations"] = {}
            st.session_state["validation"] = (results, summary, {
                "qa": qa_file.name, "manifest": manifest_file.name,
                "run_results": run_results_file.name if run_results_file else None,
                "schema": schema_file.name if schema_file else None,
            })
        except ValueError as exc:
            LOGGER.warning("Kesalahan input pengguna: %s", exc)
            st.error(str(exc))
        except Exception:
            LOGGER.exception("Kesalahan validasi tidak terduga")
            st.error("Validasi tidak dapat diselesaikan. Periksa format berkas yang diunggah dan log lokal.")

if "validation" in st.session_state:
    results, summary, filenames = st.session_state["validation"]
    st.divider()
    status = summary["overall_status"]
    if status == "PASS":
        st.success(f"Status Keseluruhan: {status}")
    elif status == "WARNING":
        st.warning(f"Status Keseluruhan: {status}")
    else:
        st.error(f"Status Keseluruhan: {status}")
    st.write("Validasi selesai. Peninjauan engineer tetap diperlukan.")

    columns = st.columns(4)
    for column, label, key in zip(columns, ["Total Pemeriksaan", "Lulus", "Peringatan", "Gagal"], ["total", "passed", "warnings", "failed"]):
        column.metric(label, summary[key])

    st.subheader("Detail hasil validasi")
    status_filter = st.selectbox("Filter status", ["Semua", "PASS", "WARNING", "FAIL"])
    visible = results if status_filter == "Semua" else [item for item in results if item.status == status_filter]
    st.dataframe(pd.DataFrame(result_rows(visible)), use_container_width=True, hide_index=True)

    anomalies = RuleBasedAnomalyDetector().detect(results)
    if anomalies:
        st.subheader("Temuan yang perlu ditinjau")
        ollama = OllamaService(config.get("ollama") or {}) if ai_enabled else None
        ai_explanations = st.session_state.setdefault("ai_explanations", {})
        for index, finding in enumerate(anomalies):
            with st.expander(f"{finding.status} · {finding.category} · {finding.object_name}"):
                st.write(f"**Diharapkan:** {finding.expected}")
                st.write(f"**Aktual:** {finding.actual}")
                st.write(f"**Bukti:** {finding.evidence}")
                st.write(f"**Penjelasan:** {finding.explanation}")
                st.write(f"**Saran peninjauan:** {finding.suggested_review or 'Penilaian engineer diperlukan.'}")
                if ollama:
                    explanation_key = f"{index}:{finding.rule_id}:{finding.object_name}:{finding.status}"
                    if st.button("Buat penjelasan AI", key=f"ai_button_{explanation_key}"):
                        with st.spinner(f"Model AI {ollama.model} sedang menyusun penjelasan..."):
                            ai_explanations[explanation_key] = ollama.explain(finding)
                    if explanation_key in ai_explanations:
                        st.write(f"**Penjelasan AI:** {ai_explanations[explanation_key]}")

    json_report = build_json_report(results, summary, filenames)
    csv_report = build_csv_report(results, summary, filenames)
    pdf_report = build_pdf_report(results, summary, filenames)
    download_left, download_middle, download_right = st.columns(3)
    download_left.download_button("Unduh laporan CSV", csv_report, "laporan_validasi_qa.csv", "text/csv", use_container_width=True)
    download_middle.download_button("Unduh laporan JSON", json_report, "laporan_validasi_qa.json", "application/json", use_container_width=True)
    download_right.download_button("Unduh laporan PDF", pdf_report, "laporan_validasi_qa.pdf", "application/pdf", use_container_width=True)

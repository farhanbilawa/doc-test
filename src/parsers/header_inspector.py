from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd
from docx import Document

from src.utils.file_utils import read_bytes
from src.utils.normalization import clean_name


def _merge_samples(output: dict[str, list[str]], frame: pd.DataFrame) -> None:
    for header in frame.columns:
        header_text = str(header).strip()
        if not header_text:
            continue
        values = output.setdefault(header_text, [])
        for value in frame[header].tolist():
            cleaned = clean_name(value)
            if cleaned and cleaned not in values:
                values.append(cleaned[:80])
            if len(values) >= 3:
                break


def inspect_tabular_headers(source: Any, filename: str) -> dict[str, list[str]]:
    """Read only headers and short samples for local semantic mapping."""
    extension = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    content = read_bytes(source)
    output: dict[str, list[str]] = {}
    try:
        if extension == "csv":
            _merge_samples(output, pd.read_csv(BytesIO(content), sep=None, engine="python", nrows=5))
        elif extension in {"xlsx", "xls"}:
            workbook = pd.read_excel(BytesIO(content), sheet_name=None, nrows=5)
            for frame in workbook.values():
                _merge_samples(output, frame)
        elif extension == "docx":
            document = Document(BytesIO(content))
            for table in document.tables:
                if not table.rows:
                    continue
                headers = [cell.text.strip() for cell in table.rows[0].cells]
                for column_index, header in enumerate(headers):
                    if not header:
                        continue
                    samples = output.setdefault(header, [])
                    for row in table.rows[1:4]:
                        if column_index < len(row.cells):
                            value = row.cells[column_index].text.strip()
                            if value and value not in samples:
                                samples.append(value[:80])
        return output
    except Exception:
        # The main parser provides the user-facing format error later.
        return {}


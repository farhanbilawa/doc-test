from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader

from src.parsers.base import QAParser, requirements_from_text
from src.utils.file_utils import read_bytes


class PDFParser(QAParser):
    def parse(self, source, header_mapping=None) -> list:
        try:
            reader = PdfReader(BytesIO(read_bytes(source)))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise ValueError(f"PDF tidak dapat dibaca: {exc}") from exc
        return requirements_from_text(text, "PDF")

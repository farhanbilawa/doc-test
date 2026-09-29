from __future__ import annotations

from src.parsers.csv_parser import CSVParser
from src.parsers.excel_parser import ExcelParser
from src.parsers.pdf_parser import PDFParser
from src.parsers.word_parser import WordParser


def parse_qa_document(source, filename: str, header_mapping: dict[str, str] | None = None) -> list:
    extension = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    parsers = {"csv": CSVParser, "xlsx": ExcelParser, "xls": ExcelParser, "docx": WordParser, "pdf": PDFParser}
    parser_class = parsers.get(extension)
    if not parser_class:
        raise ValueError(f"Format QA '.{extension}' belum didukung.")
    requirements = parser_class().parse(source, header_mapping)
    if not requirements:
        raise ValueError("Dokumen QA kosong atau tidak berisi requirement yang dikenali.")
    return requirements

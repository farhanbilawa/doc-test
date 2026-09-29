from __future__ import annotations

from io import BytesIO

import pandas as pd

from src.parsers.base import QAParser, requirements_from_rows
from src.utils.file_utils import read_bytes


class ExcelParser(QAParser):
    def parse(self, source, header_mapping=None) -> list:
        try:
            workbook = pd.read_excel(BytesIO(read_bytes(source)), sheet_name=None)
        except Exception as exc:
            raise ValueError(f"Excel tidak dapat dibaca: {exc}") from exc
        output = []
        for sheet_name, frame in workbook.items():
            output.extend(requirements_from_rows(frame.to_dict(orient="records"), f"lembar {sheet_name}", header_mapping))
        return output

from __future__ import annotations

from io import BytesIO

import pandas as pd

from src.parsers.base import QAParser, requirements_from_rows
from src.utils.file_utils import read_bytes


class CSVParser(QAParser):
    def parse(self, source, header_mapping=None) -> list:
        try:
            frame = pd.read_csv(BytesIO(read_bytes(source)), sep=None, engine="python")
        except Exception as exc:
            raise ValueError(f"CSV tidak dapat dibaca: {exc}") from exc
        return requirements_from_rows(frame.to_dict(orient="records"), "CSV", header_mapping)

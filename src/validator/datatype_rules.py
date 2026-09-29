from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

DatatypeStatus = Literal["EXACT", "COMPATIBLE", "MISMATCH", "UNKNOWN"]


@dataclass(frozen=True)
class DatatypeComparison:
    status: DatatypeStatus
    expected_normalized: str
    actual_normalized: str
    reason: str


def normalize_datatype(value: str | None) -> tuple[str, tuple[int, ...] | None]:
    if not value:
        return "", None
    text = re.sub(r"\s+", " ", value.strip().upper())
    match = re.match(r"([A-Z ]+?)(?:\s*\(([^)]*)\))?$", text)
    if not match:
        return text, None
    base = match.group(1).strip()
    params = None
    if match.group(2):
        try:
            params = tuple(int(part.strip()) for part in match.group(2).split(","))
        except ValueError:
            params = None
    return base, params


def _family(base: str, groups: dict[str, list[str]]) -> str | None:
    for family, members in groups.items():
        if base in {str(item).upper() for item in members}:
            return family
    return None


def compare_datatypes(expected: str | None, actual: str | None, config: dict) -> DatatypeComparison:
    expected_base, expected_params = normalize_datatype(expected)
    actual_base, actual_params = normalize_datatype(actual)
    if not expected_base or not actual_base:
        return DatatypeComparison("UNKNOWN", expected_base or "tidak diketahui", actual_base or "tidak diketahui", "Metadata tipe data tidak lengkap.")
    if expected_base == actual_base and expected_params == actual_params:
        return DatatypeComparison("EXACT", expected_base, actual_base, "Tipe data dan parameternya sama persis.")
    if expected_base == actual_base:
        if expected_params is None or actual_params is None:
            return DatatypeComparison("COMPATIBLE", expected_base, actual_base, "Tipe data dasar sama, tetapi bukti presisi/panjang tidak lengkap.")
        return DatatypeComparison("MISMATCH", expected_base, actual_base, "Parameter tipe data berbeda.")
    groups = config.get("datatype_groups") or {}
    expected_family = _family(expected_base, groups)
    actual_family = _family(actual_base, groups)
    compatible_pairs = {frozenset(pair) for pair in config.get("datatype_compatibility") or []}
    if expected_family and actual_family:
        if expected_family == actual_family or frozenset((expected_family, actual_family)) in compatible_pairs:
            return DatatypeComparison("COMPATIBLE", expected_base, actual_base, f"Tipe data berada dalam kelompok yang kompatibel ({expected_family}/{actual_family}).")
    return DatatypeComparison("MISMATCH", expected_base, actual_base, "Kelompok tipe data tidak kompatibel.")

from __future__ import annotations

from src.models import ValidationResult


class RuleBasedAnomalyDetector:
    """Separates review-worthy findings from successful checks."""

    def detect(self, results: list[ValidationResult]) -> list[ValidationResult]:
        return [item for item in results if item.status in {"WARNING", "FAIL"}]

    def by_severity(self, results: list[ValidationResult]) -> dict[str, list[ValidationResult]]:
        anomalies = self.detect(results)
        return {
            "FAIL": [item for item in anomalies if item.status == "FAIL"],
            "WARNING": [item for item in anomalies if item.status == "WARNING"],
        }


from src.models import ValidationResult
from src.validator.anomaly_detector import RuleBasedAnomalyDetector


def make(status):
    return ValidationResult(rule_id="x", category="Test", object_name="x", expected="x", actual="x",
                            status=status, explanation="x", evidence="x")


def test_anomaly_detector_excludes_passes():
    anomalies = RuleBasedAnomalyDetector().detect([make("PASS"), make("WARNING"), make("FAIL")])
    assert [item.status for item in anomalies] == ["WARNING", "FAIL"]


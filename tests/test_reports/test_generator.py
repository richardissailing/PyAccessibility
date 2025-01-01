from typing import List
import pytest
from pyaccessibility.reports.generator import ReportGenerator
from pyaccessibility.rules.base import RuleViolation


@pytest.fixture
def sample_violations() -> List[RuleViolation]:
    return [
        RuleViolation(
            rule_id="img-alt-text",
            severity="error",
            element='<img src="test.jpg">',
            description="Image missing alt text",
            wcag_criterion="1.1.1",
            suggested_fix="Add alt attribute",
        ),
        RuleViolation(
            rule_id="contrast",
            severity="warning",
            element='<p style="color: #777">Low contrast text</p>',
            description="Insufficient color contrast",
            wcag_criterion="1.4.3",
            suggested_fix="Increase contrast ratio",
        ),
    ]


def test_generate_report_html(sample_violations: List[RuleViolation]) -> None:
    generator = ReportGenerator()
    report = generator.generate_report(
        url="https://example.com",
        violations=sample_violations,
        scan_duration_ms=1234.56,
        elements_checked=100,
        output_format="html",
    )
    assert isinstance(report, str)
    assert "https://example.com" in report
    assert "Image missing alt text" in report
    assert "Insufficient color contrast" in report


def test_calculate_compliance_score() -> None:
    generator = ReportGenerator()
    # Test perfect score
    assert generator._calculate_compliance_score([], 100) == 100.0

    # Test with some violations
    violations = [
        RuleViolation(
            rule_id="test",
            severity="error",
            element="test",
            description="test"
        ),
        RuleViolation(
            rule_id="test",
            severity="warning",
            element="test",
            description="test"
        ),
    ]
    score = generator._calculate_compliance_score(violations, 100)
    assert 0 <= score <= 100


def test_group_violations(sample_violations: List[RuleViolation]) -> None:
    generator = ReportGenerator()
    grouped = generator._group_violations(sample_violations)
    assert "1.1.1" in grouped
    assert "1.4.3" in grouped
    assert len(grouped["1.1.1"]) == 1
    assert len(grouped["1.4.3"]) == 1


def test_count_severities(sample_violations: List[RuleViolation]) -> None:
    generator = ReportGenerator()
    counts = generator._count_severities(sample_violations)
    assert isinstance(counts, dict)
    assert counts["error"] == 1
    assert counts["warning"] == 1
    assert counts.get("info", 0) == 0
    assert counts.get("critical", 0) == 0


def test_generate_report_json(sample_violations: List[RuleViolation]) -> None:
    generator = ReportGenerator()
    report = generator.generate_report(
        url="https://example.com",
        violations=sample_violations,
        scan_duration_ms=1000.0,
        elements_checked=50,
        output_format="json"
    )
    assert isinstance(report, str)

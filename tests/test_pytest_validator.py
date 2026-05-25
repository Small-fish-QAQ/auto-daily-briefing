from __future__ import annotations

from pathlib import Path

from utils.validator import ReportValidator


def test_minimal_report_fixture_is_valid() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "minimal_report.md"
    report = fixture_path.read_text(encoding="utf-8")

    result = ReportValidator.validate(
        report,
        expected_count=1,
        advice_label="技术观察",
    )

    assert result.is_valid
    assert result.errors == []

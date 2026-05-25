from __future__ import annotations

from pathlib import Path

import pytest

from utils.validator import ReportValidator

INTEL = "\u60c5\u62a5"
CORE_FACT = "\u6838\u5fc3\u4e8b\u5b9e"
INDUSTRY_INSIGHT = "\u884c\u4e1a\u5185\u53c2"
ADVICE_LABEL = "\u6280\u672f\u89c2\u5bdf"


def report_item(
    number: int = 1,
    *,
    title: str = "Example title",
    url: str = "https://example.com/news",
    body_labels: tuple[str, ...] = (CORE_FACT, INDUSTRY_INSIGHT, ADVICE_LABEL),
) -> str:
    lines = [f"**[{INTEL}{number}] [{title}]({url})**"]
    for label in body_labels:
        lines.append(f"* **[{label}]**: Example content.")
    return "\n".join(lines)


def validate(content: str, expected_count: int = 1):
    return ReportValidator.validate(
        content,
        expected_count=expected_count,
        advice_label=ADVICE_LABEL,
    )


def test_valid_minimal_report_fixture_passes() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "minimal_report.md"

    result = validate(fixture_path.read_text(encoding="utf-8"))

    assert result.is_valid is True
    assert result.errors == []
    assert result.warnings == []
    assert result.normalized_content.endswith("\n")


def test_missing_intelligence_heading_fails() -> None:
    content = (
        f"* **[{CORE_FACT}]**: Example fact.\n"
        f"* **[{INDUSTRY_INSIGHT}]**: Example analysis.\n"
        f"* **[{ADVICE_LABEL}]**: Example advice.\n"
    )

    result = validate(content)

    assert result.is_valid is False
    assert result.errors
    assert result.warnings == []


def test_heading_without_markdown_link_fails() -> None:
    content = (
        f"**[{INTEL}1] Example title**\n"
        f"* **[{CORE_FACT}]**: Example fact.\n"
        f"* **[{INDUSTRY_INSIGHT}]**: Example analysis.\n"
        f"* **[{ADVICE_LABEL}]**: Example advice.\n"
    )

    result = validate(content)

    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "Markdown" in result.errors[0]


def test_heading_with_multiple_markdown_links_fails() -> None:
    content = (
        f"**[{INTEL}1] [A](https://example.com/a) and [B](https://example.com/b)**\n"
        f"* **[{CORE_FACT}]**: Example fact.\n"
        f"* **[{INDUSTRY_INSIGHT}]**: Example analysis.\n"
        f"* **[{ADVICE_LABEL}]**: Example advice.\n"
    )

    result = validate(content)

    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "1" in result.errors[0]


def test_missing_required_field_fails() -> None:
    content = report_item(body_labels=(CORE_FACT, ADVICE_LABEL))

    result = validate(content)

    assert result.is_valid is False
    assert len(result.errors) == 1
    assert f"[{INDUSTRY_INSIGHT}]" in result.errors[0]


def test_spaced_markdown_link_is_normalized() -> None:
    content = (
        f"  **[{INTEL}1] [Example title] (https://example.com/news)**\n"
        f"* **[{CORE_FACT}]**: Example fact.\n"
        f"* **[{INDUSTRY_INSIGHT}]**: Example analysis.\n"
        f"* **[{ADVICE_LABEL}]**: Example advice.\n\n"
    )

    result = validate(content)

    assert result.is_valid is True
    assert "[Example title](https://example.com/news)" in result.normalized_content
    assert result.normalized_content.endswith("\n")


def test_expected_count_match_passes_without_warning() -> None:
    content = "\n".join(
        [
            report_item(1, title="First", url="https://example.com/1"),
            report_item(2, title="Second", url="https://example.com/2"),
        ]
    )

    result = validate(content, expected_count=2)

    assert result.is_valid is True
    assert result.errors == []
    assert result.warnings == []


def test_expected_count_mismatch_is_warning_not_error() -> None:
    result = validate(report_item(), expected_count=2)

    assert result.is_valid is True
    assert result.errors == []
    assert len(result.warnings) == 1
    assert "1" in result.warnings[0]
    assert "2" in result.warnings[0]


@pytest.mark.parametrize(
    "content",
    [
        "",
        "not a markdown daily report",
        "# Daily Report\nNo intelligence sections here.",
    ],
)
def test_empty_or_unrelated_content_fails(content: str) -> None:
    result = validate(content)

    assert result.is_valid is False
    assert result.errors
    assert result.normalized_content.endswith("\n")


def test_validation_result_fields_follow_current_implementation() -> None:
    result = validate(report_item())

    assert result.is_valid is True
    assert result.errors == []
    assert result.warnings == []
    assert result.normalized_content == report_item() + "\n"
    assert not hasattr(result, "fixed_content")

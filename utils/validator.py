"""Markdown report validation helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final


SPACED_LINK_RE: Final[re.Pattern[str]] = re.compile(r"\]\s+\((https?://[^)]+)\)")
HEADING_RE: Final[re.Pattern[str]] = re.compile(
    r"^\*\*\[情报(\d+)\]\s+(.+?)\*\*$",
    re.MULTILINE,
)
LINK_RE: Final[re.Pattern[str]] = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")


@dataclass(frozen=True)
class ValidationResult:
    normalized_content: str
    errors: list[str]
    warnings: list[str]

    @property
    def is_valid(self) -> bool:
        return not self.errors


class ReportValidator:
    @staticmethod
    def normalize(content: str) -> str:
        """Fix common Markdown issues without changing the report meaning."""

        return SPACED_LINK_RE.sub(r"](\1)", content).strip() + "\n"

    @classmethod
    def validate(
        cls,
        content: str,
        expected_count: int,
        advice_label: str,
    ) -> ValidationResult:
        normalized = cls.normalize(content)
        errors: list[str] = []
        warnings: list[str] = []

        headings = list(HEADING_RE.finditer(normalized))
        if not headings:
            errors.append("未找到符合格式的情报标题。")
            return ValidationResult(normalized, errors, warnings)

        if len(headings) != expected_count:
            warnings.append(f"情报数量为 {len(headings)}，预期为 {expected_count}。")

        for index, heading in enumerate(headings):
            line = heading.group(0)
            links = LINK_RE.findall(line)
            item_number = heading.group(1)
            section_end = headings[index + 1].start() if index + 1 < len(headings) else len(normalized)
            section = normalized[heading.start() : section_end]

            if not links:
                errors.append(f"情报{item_number} 标题行缺少原文 Markdown 链接。")
            elif len(links) > 1:
                errors.append(f"情报{item_number} 标题行包含多个原文链接，可能合并了多条情报。")

            for label in ("核心事实", "行业内参", advice_label):
                if f"[{label}]" not in section:
                    errors.append(f"情报{item_number} 缺少 [{label}] 字段。")

        return ValidationResult(normalized, errors, warnings)

"""新闻候选筛选：打分、分类、近似去重。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Final


BASE_SCORE: Final[int] = 10
INCLUDE_KEYWORD_SCORE: Final[int] = 4
EXCLUDE_KEYWORD_PENALTY: Final[int] = 5
TITLE_KEYWORD_BONUS: Final[int] = 2
TITLE_SIMILARITY_THRESHOLD: Final[float] = 0.86


@dataclass(frozen=True)
class FilterConfig:
    candidate_limit: int
    include_keywords: list[str]
    exclude_keywords: list[str]
    source_weights: dict[str, int]
    category_keywords: dict[str, list[str]]


class NewsFilter:
    def __init__(self, config: FilterConfig):
        self.config = config

    def _normalize_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip().lower()

    def _keyword_hits(self, text: str, keywords: list[str]) -> list[str]:
        normalized = self._normalize_text(text)
        return [keyword for keyword in keywords if keyword.lower() in normalized]

    def _classify(self, item: dict[str, str]) -> str:
        text = f"{item.get('title', '')} {item.get('digest', '')}"
        best_category = "其他"
        best_hits = 0

        for category, keywords in self.config.category_keywords.items():
            hits = len(self._keyword_hits(text, keywords))
            if hits > best_hits:
                best_category = category
                best_hits = hits

        return best_category

    def _score(self, item: dict[str, str], category: str) -> int:
        title = item.get("title", "")
        text = f"{title} {item.get('digest', '')}"
        include_hits = self._keyword_hits(text, self.config.include_keywords)
        exclude_hits = self._keyword_hits(text, self.config.exclude_keywords)
        title_hits = self._keyword_hits(title, self.config.include_keywords)

        return (
            BASE_SCORE
            + self.config.source_weights.get(item.get("origin", ""), 0)
            + len(include_hits) * INCLUDE_KEYWORD_SCORE
            + len(title_hits) * TITLE_KEYWORD_BONUS
            - len(exclude_hits) * EXCLUDE_KEYWORD_PENALTY
            + (1 if category != "其他" else 0)
        )

    def _title_similarity(self, left: str, right: str) -> float:
        return SequenceMatcher(
            None,
            self._normalize_text(left),
            self._normalize_text(right),
        ).ratio()

    def _is_duplicate_title(self, item: dict[str, str], selected: list[dict[str, str]]) -> bool:
        title = item.get("title", "")
        if not title:
            return False

        return any(
            self._title_similarity(title, existing.get("title", "")) >= TITLE_SIMILARITY_THRESHOLD
            for existing in selected
        )

    def select(self, items: list[dict[str, str]]) -> list[dict[str, str]]:
        """返回按质量排序并截断后的候选新闻。"""

        enriched_items: list[dict[str, str]] = []
        for item in items:
            category = self._classify(item)
            score = self._score(item, category)
            enriched_item = dict(item)
            enriched_item["category"] = category
            enriched_item["score"] = str(score)
            enriched_items.append(enriched_item)

        ranked_items = sorted(
            enriched_items,
            key=lambda item: int(item["score"]),
            reverse=True,
        )

        selected: list[dict[str, str]] = []
        for item in ranked_items:
            if self._is_duplicate_title(item, selected):
                continue
            selected.append(item)
            if len(selected) >= self.config.candidate_limit:
                break

        return selected

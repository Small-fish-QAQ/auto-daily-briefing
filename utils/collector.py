"""RSS 抓取模块。"""

from __future__ import annotations

import html
import re
import urllib.error
import urllib.request
from typing import Final

import feedparser

DEFAULT_TIMEOUT_SECONDS: Final[int] = 20
DEFAULT_USER_AGENT: Final[str] = (
    "News-Briefing/0.2 (+https://github.com/Small-fish-QAQ/auto-daily-briefing)"
)


class IntelligenceCollector:
    def __init__(
        self,
        sources: dict[str, str],
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ):
        self.sources = sources
        self.timeout_seconds = timeout_seconds
        self.seen_links: set[str] = set()

    def _clean_text(self, value: object) -> str:
        if value is None:
            return ""
        text = html.unescape(str(value))
        text = re.sub(r"<[^>]+>", " ", text)
        return " ".join(text.split())

    def _parse_feed(self, url: str) -> feedparser.FeedParserDict:
        # 先用 urllib 控制超时和 User-Agent，再交给 feedparser 解析内容。
        request = urllib.request.Request(
            url,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return feedparser.parse(response.read())

    def _format_error(self, error: Exception) -> str:
        if isinstance(error, urllib.error.HTTPError):
            return f"HTTP {error.code}: {error.reason}"
        if isinstance(error, urllib.error.URLError):
            return str(error.reason)
        return " ".join(str(error).split()) or error.__class__.__name__

    def scan(self, limit_per_source: int = 15) -> list[dict[str, str]]:
        """抓取 RSS 条目，并在单次运行内做去重。"""

        raw_intel: list[dict[str, str]] = []

        for name, url in self.sources.items():
            try:
                feed = self._parse_feed(url)
            except Exception as error:
                print(f"[RSS] {name} 抓取失败，已跳过：{self._format_error(error)}")
                continue

            if getattr(feed, "bozo", False):
                bozo_error = getattr(feed, "bozo_exception", None)
                print(f"[RSS] {name} 解析存在异常：{bozo_error}")

            entries = getattr(feed, "entries", [])
            if not entries:
                print(f"[RSS] {name} 未返回有效条目。")
                continue

            for entry in entries[:limit_per_source]:
                link = getattr(entry, "link", "").strip()
                if not link or link in self.seen_links:
                    continue

                raw_intel.append(
                    {
                        "origin": name,
                        "title": self._clean_text(getattr(entry, "title", "Untitled")),
                        "digest": self._clean_text(getattr(entry, "summary", "No summary")),
                        "published": self._clean_text(
                            getattr(entry, "published", "") or getattr(entry, "updated", "")
                        ),
                        "url": link,
                    }
                )
                self.seen_links.add(link)

        return raw_intel

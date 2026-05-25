from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from urllib.error import URLError

import pytest

from utils import collector as collector_module
from utils.collector import IntelligenceCollector


def entry(
    link: str = "https://example.com/news",
    *,
    title: str = "Example title",
    summary: str = "Example summary",
    published: str = "2026-05-25",
    updated: str = "",
) -> SimpleNamespace:
    values = {"link": link}
    if title is not None:
        values["title"] = title
    if summary is not None:
        values["summary"] = summary
    if published is not None:
        values["published"] = published
    if updated is not None:
        values["updated"] = updated
    return SimpleNamespace(**values)


def feed(entries: list[SimpleNamespace], *, bozo: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        entries=entries,
        bozo=bozo,
        bozo_exception=ValueError("fixture parse warning") if bozo else None,
    )


def patch_parse_feed(
    monkeypatch: pytest.MonkeyPatch,
    feeds: dict[str, SimpleNamespace | Exception],
) -> None:
    def fake_parse_feed(self: IntelligenceCollector, url: str) -> SimpleNamespace:
        result = feeds[url]
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(IntelligenceCollector, "_parse_feed", fake_parse_feed)


def test_local_rss_fixture_is_parsed_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rss_bytes = (Path(__file__).parent / "fixtures" / "sample_feed.xml").read_bytes()

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return rss_bytes

    def fake_urlopen(request: object, timeout: int) -> FakeResponse:
        assert timeout == 3
        return FakeResponse()

    monkeypatch.setattr(collector_module.urllib.request, "urlopen", fake_urlopen)

    selected = IntelligenceCollector(
        {"Fixture": "https://example.com/feed.xml"},
        timeout_seconds=3,
    ).scan(limit_per_source=5)

    assert selected == [
        {
            "origin": "Fixture",
            "title": "AI & Tools Update",
            "digest": "Hello world",
            "published": "Mon, 25 May 2026 08:00:00 GMT",
            "url": "https://example.com/news/1",
        }
    ]


def test_scan_returns_current_item_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_parse_feed(
        monkeypatch,
        {
            "feed://source": feed(
                [
                    entry(
                        "https://example.com/item",
                        title="Title",
                        summary="Digest",
                        published="Published",
                    )
                ]
            )
        },
    )

    selected = IntelligenceCollector({"Source": "feed://source"}).scan()

    assert set(selected[0]) == {"origin", "title", "digest", "published", "url"}
    assert selected[0] == {
        "origin": "Source",
        "title": "Title",
        "digest": "Digest",
        "published": "Published",
        "url": "https://example.com/item",
    }


def test_html_summary_is_cleaned_without_truncation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_parse_feed(
        monkeypatch,
        {
            "feed://source": feed(
                [
                    entry(
                        "https://example.com/html",
                        title="<b>Title&nbsp;Text</b>",
                        summary="<p>Alpha&nbsp;<strong>Beta</strong></p>",
                    )
                ]
            )
        },
    )

    selected = IntelligenceCollector({"Source": "feed://source"}).scan()

    assert selected[0]["title"] == "Title Text"
    assert selected[0]["digest"] == "Alpha Beta"


def test_entry_without_link_is_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_parse_feed(
        monkeypatch,
        {
            "feed://source": feed(
                [
                    entry("", title="Missing link"),
                    entry("   ", title="Blank link"),
                    entry("https://example.com/valid", title="Valid link"),
                ]
            )
        },
    )

    selected = IntelligenceCollector({"Source": "feed://source"}).scan()

    assert [item["url"] for item in selected] == ["https://example.com/valid"]


def test_missing_title_summary_and_published_use_current_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_parse_feed(
        monkeypatch,
        {"feed://source": feed([SimpleNamespace(link="https://example.com/minimal")])},
    )

    selected = IntelligenceCollector({"Source": "feed://source"}).scan()

    assert selected[0]["title"] == "Untitled"
    assert selected[0]["digest"] == "No summary"
    assert selected[0]["published"] == ""


def test_updated_is_used_when_published_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_parse_feed(
        monkeypatch,
        {
            "feed://source": feed(
                [
                    entry(
                        "https://example.com/updated",
                        published="",
                        updated="Updated timestamp",
                    )
                ]
            )
        },
    )

    selected = IntelligenceCollector({"Source": "feed://source"}).scan()

    assert selected[0]["published"] == "Updated timestamp"


def test_single_source_failure_does_not_stop_other_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_parse_feed(
        monkeypatch,
        {
            "feed://bad": URLError("offline"),
            "feed://good": feed([entry("https://example.com/good")]),
        },
    )

    selected = IntelligenceCollector(
        {
            "Bad": "feed://bad",
            "Good": "feed://good",
        }
    ).scan()

    assert [item["origin"] for item in selected] == ["Good"]
    assert [item["url"] for item in selected] == ["https://example.com/good"]


def test_empty_feed_returns_no_items(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_parse_feed(monkeypatch, {"feed://empty": feed([])})

    selected = IntelligenceCollector({"Empty": "feed://empty"}).scan()

    assert selected == []


def test_bozo_feed_is_still_processed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_parse_feed(
        monkeypatch,
        {"feed://bozo": feed([entry("https://example.com/bozo")], bozo=True)},
    )

    selected = IntelligenceCollector({"Bozo": "feed://bozo"}).scan()

    assert [item["url"] for item in selected] == ["https://example.com/bozo"]


def test_parse_exception_returns_no_items_for_that_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_parse_feed(monkeypatch, {"feed://broken": RuntimeError("parse failed")})

    selected = IntelligenceCollector({"Broken": "feed://broken"}).scan()

    assert selected == []


def test_duplicate_urls_are_deduplicated_in_one_scan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_parse_feed(
        monkeypatch,
        {
            "feed://a": feed(
                [
                    entry("https://example.com/duplicate", title="First"),
                    entry("https://example.com/duplicate", title="Second"),
                ]
            ),
            "feed://b": feed(
                [
                    entry("https://example.com/duplicate", title="Third"),
                    entry("https://example.com/unique", title="Unique"),
                ]
            ),
        },
    )

    selected = IntelligenceCollector(
        {
            "A": "feed://a",
            "B": "feed://b",
        }
    ).scan()

    assert [item["title"] for item in selected] == ["First", "Unique"]
    assert [item["url"] for item in selected] == [
        "https://example.com/duplicate",
        "https://example.com/unique",
    ]


def test_limit_per_source_is_applied_before_processing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_parse_feed(
        monkeypatch,
        {
            "feed://source": feed(
                [
                    entry("https://example.com/1", title="One"),
                    entry("https://example.com/2", title="Two"),
                    entry("https://example.com/3", title="Three"),
                ]
            )
        },
    )

    selected = IntelligenceCollector({"Source": "feed://source"}).scan(limit_per_source=2)

    assert [item["title"] for item in selected] == ["One", "Two"]

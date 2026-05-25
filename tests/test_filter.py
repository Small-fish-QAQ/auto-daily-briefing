from __future__ import annotations

from utils.filter import FilterConfig, NewsFilter

DEFAULT_CATEGORY = "\u5176\u4ed6"


def make_filter(candidate_limit: int = 10) -> NewsFilter:
    return NewsFilter(
        FilterConfig(
            candidate_limit=candidate_limit,
            include_keywords=["ai", "agent", "chip", "signal"],
            exclude_keywords=["rumor", "housing"],
            source_weights={"Trusted": 3, "Low": -2},
            category_keywords={
                "AI": ["ai", "agent"],
                "Hardware": ["chip", "gpu"],
            },
        )
    )


def make_item(
    title: str,
    url: str,
    *,
    digest: str = "general update",
    origin: str = "Neutral",
    published: str = "2026-01-01",
) -> dict[str, str]:
    return {
        "title": title,
        "url": url,
        "origin": origin,
        "digest": digest,
        "published": published,
    }


def by_url(items: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {item["url"]: item for item in items}


def test_include_keyword_hit_increases_score() -> None:
    selected = make_filter().select(
        [
            make_item("Company update", "https://example.com/plain"),
            make_item(
                "Company workflow update",
                "https://example.com/include",
                digest="teams adopt signal workflow",
            ),
        ]
    )

    items = by_url(selected)

    assert int(items["https://example.com/include"]["score"]) == 14
    assert int(items["https://example.com/plain"]["score"]) == 10
    assert selected[0]["url"] == "https://example.com/include"


def test_exclude_keyword_hit_lowers_score_without_filtering_item_out() -> None:
    selected = make_filter().select(
        [
            make_item("Clean infrastructure update", "https://example.com/clean"),
            make_item(
                "Market rumor update",
                "https://example.com/rumor",
                digest="unconfirmed rumor about operations",
            ),
        ]
    )

    items = by_url(selected)

    assert int(items["https://example.com/clean"]["score"]) == 10
    assert int(items["https://example.com/rumor"]["score"]) == 5
    assert selected[0]["url"] == "https://example.com/clean"


def test_title_keyword_hit_gets_extra_bonus() -> None:
    selected = make_filter().select(
        [
            make_item(
                "Workflow update",
                "https://example.com/digest-hit",
                digest="teams adopt signal workflow",
            ),
            make_item("Signal workflow update", "https://example.com/title-hit"),
        ]
    )

    items = by_url(selected)

    assert int(items["https://example.com/digest-hit"]["score"]) == 14
    assert int(items["https://example.com/title-hit"]["score"]) == 16
    assert selected[0]["url"] == "https://example.com/title-hit"


def test_source_weights_affect_score_and_sorting() -> None:
    selected = make_filter().select(
        [
            make_item("Neutral source note", "https://example.com/neutral"),
            make_item(
                "Trusted source note",
                "https://example.com/trusted",
                origin="Trusted",
            ),
        ]
    )

    items = by_url(selected)

    assert int(items["https://example.com/trusted"]["score"]) == 13
    assert int(items["https://example.com/neutral"]["score"]) == 10
    assert selected[0]["url"] == "https://example.com/trusted"


def test_category_keywords_assign_category() -> None:
    selected = make_filter().select(
        [
            make_item("Enterprise AI agent platform", "https://example.com/ai"),
            make_item(
                "Datacenter expansion",
                "https://example.com/hardware",
                digest="new gpu and chip capacity",
            ),
        ]
    )

    items = by_url(selected)

    assert items["https://example.com/ai"]["category"] == "AI"
    assert items["https://example.com/hardware"]["category"] == "Hardware"


def test_default_category_is_used_when_no_category_matches() -> None:
    selected = make_filter().select(
        [
            make_item(
                "Operations update",
                "https://example.com/default-category",
                digest="general company operations",
            )
        ]
    )

    assert selected[0]["category"] == DEFAULT_CATEGORY


def test_similar_titles_are_deduplicated_after_ranking() -> None:
    selected = make_filter().select(
        [
            make_item(
                "AI platform launches enterprise agent",
                "https://example.com/agent-a",
            ),
            make_item(
                "AI platform launches enterprise agents",
                "https://example.com/agent-b",
            ),
            make_item(
                "Storage vendor publishes quarterly plan",
                "https://example.com/storage",
            ),
        ]
    )

    selected_urls = [item["url"] for item in selected]

    assert selected_urls == [
        "https://example.com/agent-a",
        "https://example.com/storage",
    ]


def test_exact_duplicate_titles_are_not_repeated() -> None:
    selected = make_filter().select(
        [
            make_item("AI agent launch report", "https://example.com/a"),
            make_item("AI agent launch report", "https://example.com/b"),
            make_item("Independent storage update", "https://example.com/c"),
        ]
    )

    assert [item["title"] for item in selected].count("AI agent launch report") == 1
    assert [item["url"] for item in selected] == [
        "https://example.com/a",
        "https://example.com/c",
    ]


def test_duplicate_urls_with_different_titles_follow_current_title_dedupe_rule() -> None:
    selected = make_filter().select(
        [
            make_item("AI agent release", "https://example.com/same-url"),
            make_item("Chip capacity plan", "https://example.com/same-url"),
        ]
    )

    assert [item["url"] for item in selected].count("https://example.com/same-url") == 2


def test_candidate_limit_restricts_final_output_count() -> None:
    selected = make_filter(candidate_limit=3).select(
        [
            make_item("Alpha compiler note", "https://example.com/alpha"),
            make_item("Bravo storage plan", "https://example.com/bravo"),
            make_item("Charlie network patch", "https://example.com/charlie"),
            make_item("Delta privacy rule", "https://example.com/delta"),
            make_item("Echo robotics lab", "https://example.com/echo"),
        ]
    )

    assert len(selected) == 3


def test_output_preserves_original_fields_and_adds_filter_fields() -> None:
    source_item = make_item(
        "Signal workflow update",
        "https://example.com/output-fields",
        digest="teams adopt signal workflow",
        origin="Trusted",
        published="2026-05-25",
    )

    selected = make_filter().select([source_item])

    assert selected[0]["title"] == source_item["title"]
    assert selected[0]["url"] == source_item["url"]
    assert selected[0]["origin"] == source_item["origin"]
    assert selected[0]["digest"] == source_item["digest"]
    assert selected[0]["published"] == source_item["published"]
    assert selected[0]["category"] == DEFAULT_CATEGORY
    assert selected[0]["score"] == "19"

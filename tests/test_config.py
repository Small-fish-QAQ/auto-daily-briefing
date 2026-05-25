from __future__ import annotations

import json
from pathlib import Path

import pytest

from utils.config import (
    DEFAULT_ADVICE_LABEL,
    DEFAULT_AUDIENCE,
    DEFAULT_CANDIDATE_LIMIT,
    DEFAULT_EXCLUDE_KEYWORDS,
    DEFAULT_HISTORY_CAPACITY,
    DEFAULT_HISTORY_FILE,
    DEFAULT_INCLUDE_KEYWORDS,
    DEFAULT_LIMIT_PER_SOURCE,
    DEFAULT_MODEL,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPORT_PREFIX,
    DEFAULT_REPORT_TITLE,
    DEFAULT_SOURCES,
    DEFAULT_STYLE_ROLE,
    DEFAULT_TONE,
    DEFAULT_TOP_N,
    load_config,
)

CONFIG_ENV_NAMES = [
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
    "BRIEFING_CONFIG_FILE",
    "BRIEFING_SOURCES_JSON",
    "BRIEFING_LIMIT_PER_SOURCE",
    "BRIEFING_TOP_N",
    "BRIEFING_CANDIDATE_LIMIT",
    "BRIEFING_HISTORY_FILE",
    "BRIEFING_HISTORY_CAPACITY",
    "BRIEFING_OUTPUT_DIR",
    "BRIEFING_REPORT_PREFIX",
    "BRIEFING_REPORT_TITLE",
    "BRIEFING_STYLE_ROLE",
    "BRIEFING_ADVICE_LABEL",
    "BRIEFING_AUDIENCE",
    "BRIEFING_TONE",
]


@pytest.fixture(autouse=True)
def isolated_config_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    for name in CONFIG_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


def write_config(data: dict[str, object], filename: str = "briefing_config.json") -> None:
    Path(filename).write_text(json.dumps(data), encoding="utf-8")


def test_loads_defaults_without_config_file_or_env() -> None:
    config = load_config()

    assert config.sources == DEFAULT_SOURCES
    assert config.history_file == DEFAULT_HISTORY_FILE
    assert config.history_capacity == DEFAULT_HISTORY_CAPACITY
    assert config.model == DEFAULT_MODEL
    assert config.output_dir == DEFAULT_OUTPUT_DIR
    assert config.report_prefix == DEFAULT_REPORT_PREFIX
    assert config.report_title == DEFAULT_REPORT_TITLE
    assert config.limit_per_source == DEFAULT_LIMIT_PER_SOURCE
    assert config.top_n == DEFAULT_TOP_N
    assert config.candidate_limit == DEFAULT_CANDIDATE_LIMIT
    assert config.include_keywords == DEFAULT_INCLUDE_KEYWORDS
    assert config.exclude_keywords == DEFAULT_EXCLUDE_KEYWORDS
    assert config.style_role == DEFAULT_STYLE_ROLE
    assert config.advice_label == DEFAULT_ADVICE_LABEL
    assert config.audience == DEFAULT_AUDIENCE
    assert config.tone == DEFAULT_TONE


def test_json_config_file_overrides_defaults() -> None:
    write_config(
        {
            "sources": {"Example": "https://example.com/feed.xml"},
            "selection": {
                "limit_per_source": 4,
                "top_n": 3,
                "candidate_limit": 8,
            },
            "filtering": {
                "include_keywords": ["AI", "Agent"],
                "exclude_keywords": ["rumor"],
                "source_weights": {"Example": 2},
                "category_keywords": {"AI": ["AI", "Agent"]},
            },
            "history": {"file": "custom/history.txt", "capacity": 12},
            "output": {
                "dir": "reports",
                "prefix": "briefing",
                "title": "Daily Briefing",
            },
            "style": {
                "role": "Neutral analyst",
                "advice_label": "Action",
                "audience": "developers",
                "tone": "concise",
            },
        }
    )

    config = load_config()

    assert config.sources == {"Example": "https://example.com/feed.xml"}
    assert config.limit_per_source == 4
    assert config.top_n == 3
    assert config.candidate_limit == 8
    assert config.include_keywords == ["AI", "Agent"]
    assert config.exclude_keywords == ["rumor"]
    assert config.source_weights == {"Example": 2}
    assert config.category_keywords == {"AI": ["AI", "Agent"]}
    assert config.history_file == "custom/history.txt"
    assert config.history_capacity == 12
    assert config.output_dir == "reports"
    assert config.report_prefix == "briefing"
    assert config.report_title == "Daily Briefing"
    assert config.style_role == "Neutral analyst"
    assert config.advice_label == "Action"
    assert config.audience == "developers"
    assert config.tone == "concise"


def test_env_vars_override_json_config(monkeypatch: pytest.MonkeyPatch) -> None:
    write_config(
        {
            "selection": {
                "limit_per_source": 4,
                "top_n": 3,
                "candidate_limit": 8,
            },
            "history": {"file": "file-history.txt", "capacity": 12},
            "output": {
                "dir": "file-reports",
                "prefix": "file-prefix",
                "title": "From file",
            },
            "style": {
                "role": "File role",
                "advice_label": "File advice",
                "audience": "File audience",
                "tone": "File tone",
            },
        }
    )
    monkeypatch.setenv("BRIEFING_LIMIT_PER_SOURCE", "9")
    monkeypatch.setenv("BRIEFING_TOP_N", "7")
    monkeypatch.setenv("BRIEFING_CANDIDATE_LIMIT", "11")
    monkeypatch.setenv("BRIEFING_HISTORY_FILE", "env-history.txt")
    monkeypatch.setenv("BRIEFING_HISTORY_CAPACITY", "21")
    monkeypatch.setenv("BRIEFING_OUTPUT_DIR", "env-reports")
    monkeypatch.setenv("BRIEFING_REPORT_PREFIX", "env-prefix")
    monkeypatch.setenv("BRIEFING_REPORT_TITLE", "From env")
    monkeypatch.setenv("BRIEFING_STYLE_ROLE", "Env role")
    monkeypatch.setenv("BRIEFING_ADVICE_LABEL", "Env advice")
    monkeypatch.setenv("BRIEFING_AUDIENCE", "Env audience")
    monkeypatch.setenv("BRIEFING_TONE", "Env tone")

    config = load_config()

    assert config.limit_per_source == 9
    assert config.top_n == 7
    assert config.candidate_limit == 11
    assert config.history_file == "env-history.txt"
    assert config.history_capacity == 21
    assert config.output_dir == "env-reports"
    assert config.report_prefix == "env-prefix"
    assert config.report_title == "From env"
    assert config.style_role == "Env role"
    assert config.advice_label == "Env advice"
    assert config.audience == "Env audience"
    assert config.tone == "Env tone"


def test_gemini_model_is_read_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")

    config = load_config()

    assert config.model == "gemini-test-model"


def test_sources_json_env_replaces_config_file_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_config({"sources": {"File": "https://example.com/file.xml"}})
    monkeypatch.setenv(
        "BRIEFING_SOURCES_JSON",
        '{"Env":"https://example.com/env.xml"}',
    )

    config = load_config()

    assert config.sources == {"Env": "https://example.com/env.xml"}


def test_explicit_config_file_path_is_loaded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "custom_config.json"
    config_path.write_text(
        json.dumps({"output": {"title": "Custom path"}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("BRIEFING_CONFIG_FILE", str(config_path))

    config = load_config()

    assert config.report_title == "Custom path"


def test_invalid_json_config_file_raises_value_error() -> None:
    Path("briefing_config.json").write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ValueError):
        load_config()


def test_invalid_integer_environment_variable_raises_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BRIEFING_TOP_N", "zero")

    with pytest.raises(ValueError):
        load_config()


def test_empty_sources_in_config_file_raise_value_error() -> None:
    write_config({"sources": {}})

    with pytest.raises(ValueError):
        load_config()


def test_empty_sources_from_environment_raise_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BRIEFING_SOURCES_JSON", "{}")

    with pytest.raises(ValueError):
        load_config()

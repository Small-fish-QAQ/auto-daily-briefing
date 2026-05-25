from __future__ import annotations

from pathlib import Path

import pytest

from utils import memory as memory_module
from utils.memory import MemoryBank


def read_history(history_file: Path) -> list[str]:
    return history_file.read_text(encoding="utf-8").splitlines()


def test_initializes_when_history_file_is_missing(tmp_path: Path) -> None:
    history_file = tmp_path / "missing" / "history.txt"

    memory = MemoryBank(str(history_file), max_capacity=10)

    assert memory.history_list == []
    assert memory.history_set == set()
    assert read_history(history_file) == []


def test_reads_existing_history_file(tmp_path: Path) -> None:
    history_file = tmp_path / "history.txt"
    history_file.write_text(
        "https://example.com/a\nhttps://example.com/b\n",
        encoding="utf-8",
    )

    memory = MemoryBank(str(history_file), max_capacity=10)

    assert memory.history_list == [
        "https://example.com/a",
        "https://example.com/b",
    ]
    assert memory.history_set == {
        "https://example.com/a",
        "https://example.com/b",
    }


def test_deduplicates_repeated_links(tmp_path: Path) -> None:
    history_file = tmp_path / "history.txt"
    history_file.write_text(
        "\n".join(
            [
                "https://example.com/a",
                "https://example.com/b",
                "https://example.com/a",
                "https://example.com/c",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    memory = MemoryBank(str(history_file), max_capacity=10)

    assert memory.history_list == [
        "https://example.com/a",
        "https://example.com/b",
        "https://example.com/c",
    ]
    assert read_history(history_file) == memory.history_list


def test_is_new_distinguishes_new_and_existing_links(tmp_path: Path) -> None:
    history_file = tmp_path / "history.txt"
    history_file.write_text("https://example.com/old\n", encoding="utf-8")
    memory = MemoryBank(str(history_file), max_capacity=10)

    assert memory.is_new("https://example.com/new") is True
    assert memory.is_new("https://example.com/old") is False


def test_is_new_normalizes_surrounding_whitespace(tmp_path: Path) -> None:
    history_file = tmp_path / "history.txt"
    history_file.write_text("https://example.com/a\n", encoding="utf-8")
    memory = MemoryBank(str(history_file), max_capacity=10)

    assert memory.is_new(" https://example.com/a ") is False
    assert memory.is_new("\nhttps://example.com/a\t") is False
    assert memory.is_new("   ") is False


def test_update_writes_new_links(tmp_path: Path) -> None:
    history_file = tmp_path / "history.txt"
    history_file.write_text("https://example.com/a\n", encoding="utf-8")
    memory = MemoryBank(str(history_file), max_capacity=10)

    memory.update(["https://example.com/b", "https://example.com/c"])

    assert read_history(history_file) == [
        "https://example.com/a",
        "https://example.com/b",
        "https://example.com/c",
    ]


def test_update_ignores_blank_links(tmp_path: Path) -> None:
    history_file = tmp_path / "history.txt"
    history_file.write_text("https://example.com/a\n", encoding="utf-8")
    memory = MemoryBank(str(history_file), max_capacity=10)

    memory.update(["", " ", "\n", "\t"])

    assert memory.history_list == ["https://example.com/a"]
    assert memory.history_set == {"https://example.com/a"}
    assert read_history(history_file) == ["https://example.com/a"]


def test_trims_oldest_links_when_capacity_is_exceeded(tmp_path: Path) -> None:
    history_file = tmp_path / "history.txt"
    history_file.write_text(
        "\n".join(
            [
                "https://example.com/a",
                "https://example.com/b",
                "https://example.com/c",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    memory = MemoryBank(str(history_file), max_capacity=3)

    memory.update(["https://example.com/d", "https://example.com/e"])

    assert memory.history_list == [
        "https://example.com/c",
        "https://example.com/d",
        "https://example.com/e",
    ]
    assert read_history(history_file) == memory.history_list


def test_update_keeps_memory_state_and_file_content_in_sync(tmp_path: Path) -> None:
    history_file = tmp_path / "history.txt"
    history_file.write_text("https://example.com/a\n", encoding="utf-8")
    memory = MemoryBank(str(history_file), max_capacity=3)

    memory.update(
        [
            "https://example.com/a",
            "https://example.com/b",
            "https://example.com/b",
            "https://example.com/c",
            "https://example.com/d",
        ]
    )

    file_history = read_history(history_file)

    assert file_history == [
        "https://example.com/b",
        "https://example.com/c",
        "https://example.com/d",
    ]
    assert memory.history_list == file_history
    assert memory.history_set == set(file_history)


def test_failed_atomic_replace_keeps_original_history_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history_file = tmp_path / "history.txt"
    history_file.write_text("https://example.com/a\n", encoding="utf-8")
    memory = MemoryBank(str(history_file), max_capacity=10)

    def fail_replace(source: str, target: str) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(memory_module.os, "replace", fail_replace)

    with pytest.raises(OSError):
        memory.update(["https://example.com/b"])

    assert read_history(history_file) == ["https://example.com/a"]
    assert list(tmp_path.glob(".history.txt.*.tmp")) == []

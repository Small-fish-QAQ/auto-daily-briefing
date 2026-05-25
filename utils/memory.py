"""跨运行历史去重模块。"""

from __future__ import annotations

import os
import tempfile
from typing import Iterable


class MemoryBank:
    def __init__(self, history_file: str = "utils/history.txt", max_capacity: int = 500):
        self.history_file = history_file
        self.max_capacity = max_capacity
        self.history_list = self._normalize_history(self._load_history())
        self.history_set = set(self.history_list)

        # 自动修复旧历史文件中可能存在的重复记录或超量记录。
        self._write_history(self.history_list)

    def _load_history(self) -> list[str]:
        """从磁盘读取历史记录，并保留文件中的原始顺序。"""

        if not os.path.exists(self.history_file):
            return []

        with open(self.history_file, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]

    def _normalize_history(self, links: Iterable[str]) -> list[str]:
        """保持文件顺序稳定，去重后再裁剪超量记录。"""

        normalized: list[str] = []
        seen: set[str] = set()

        for link in links:
            normalized_link = link.strip()
            if not normalized_link or normalized_link in seen:
                continue
            normalized.append(normalized_link)
            seen.add(normalized_link)

        if len(normalized) > self.max_capacity:
            normalized = normalized[-self.max_capacity :]

        return normalized

    def _write_history(self, links: Iterable[str]) -> None:
        """将历史记录写回磁盘。"""

        target_path = os.path.abspath(self.history_file)
        directory = os.path.dirname(target_path)
        os.makedirs(directory, exist_ok=True)

        temp_path = ""
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=directory,
                prefix=f".{os.path.basename(target_path)}.",
                suffix=".tmp",
                delete=False,
            ) as file:
                temp_path = file.name
                for link in links:
                    file.write(f"{link}\n")
                file.flush()
                os.fsync(file.fileno())

            os.replace(temp_path, target_path)
        except Exception:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    def _refresh_state(self, links: list[str]) -> None:
        """在每次更新后同步内存中的列表和集合状态。"""

        self.history_list = links
        self.history_set = set(links)

    def is_new(self, link: str) -> bool:
        """判断链接是否为未出现过的新内容。"""

        normalized_link = link.strip()
        if not normalized_link:
            return False
        return normalized_link not in self.history_set

    def update(self, new_links: Iterable[str]) -> None:
        """追加新链接、裁剪容量，并同步内存状态。"""

        pending_links: list[str] = []
        pending_set: set[str] = set()

        for link in new_links:
            normalized_link = link.strip()
            if not normalized_link:
                continue
            if normalized_link in self.history_set or normalized_link in pending_set:
                continue
            pending_links.append(normalized_link)
            pending_set.add(normalized_link)

        if not pending_links:
            return

        updated_history = self._normalize_history(self.history_list + pending_links)
        self._write_history(updated_history)
        self._refresh_state(updated_history)

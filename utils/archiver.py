"""Markdown 日报归档模块。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


class ArchiveMaster:
    @staticmethod
    def store(
        content: str,
        output_dir: str = "每日简报",
        prefix: str = "精选简报",
        report_title: str = "自动化科技简报",
    ) -> str:
        """按现有日期目录结构归档生成后的日报。"""

        now = datetime.now()
        target_dir = Path(output_dir) / now.strftime("%Y") / now.strftime("%m")
        target_dir.mkdir(parents=True, exist_ok=True)

        full_path = target_dir / f"{now.strftime('%Y-%m-%d')}-{prefix}.md"
        header = f"# {now.strftime('%Y-%m-%d %H:%M')} {report_title}\n\n"
        full_path.write_text(header + content, encoding="utf-8")

        return str(full_path)

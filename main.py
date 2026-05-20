"""自动日报系统的主入口。"""

from __future__ import annotations

import os

from dotenv import load_dotenv

from utils.analyst import GeminiChief
from utils.archiver import ArchiveMaster
from utils.config import load_config
from utils.collector import IntelligenceCollector
from utils.memory import MemoryBank

load_dotenv()


def run_daily_briefing() -> int:
    """抓取新内容、生成日报并完成归档。"""

    try:
        config = load_config()
    except ValueError as error:
        print(f"配置错误：{error}")
        return 1

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("错误：未找到 GEMINI_API_KEY，请检查本地 .env 或 GitHub Secrets。")
        return 1

    collector = IntelligenceCollector(config.sources)
    memory = MemoryBank(
        history_file=config.history_file,
        max_capacity=config.history_capacity,
    )
    analyst = GeminiChief(
        api_key=api_key,
        model=config.model,
        top_n=config.top_n,
        style_guide={
            "role": config.style_role,
            "advice_label": config.advice_label,
            "audience": config.audience,
            "tone": config.tone,
        },
    )

    print("正在抓取 RSS 源...")
    raw_items = collector.scan(limit_per_source=config.limit_per_source)

    fresh_items = [item for item in raw_items if memory.is_new(item["url"])]
    new_links = [item["url"] for item in fresh_items]

    if not fresh_items:
        print(f"未发现新内容，本次共扫描 {len(raw_items)} 条，跳过摘要生成。")
        return 0

    print(f"开始生成日报：共扫描 {len(raw_items)} 条，新增 {len(fresh_items)} 条。")
    report = analyst.summarize(fresh_items)

    archived_path = ArchiveMaster.store(
        report,
        output_dir=config.output_dir,
        prefix=config.report_prefix,
        report_title=config.report_title,
    )
    memory.update(new_links)

    print(f"日报已归档到：{archived_path}")
    print(f"历史记录已更新，最多保留最近 {config.history_capacity} 条链接。")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_daily_briefing())

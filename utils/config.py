"""运行配置模块：默认值 < JSON 配置文件 < 环境变量。"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

DEFAULT_SOURCES: Final[dict[str, str]] = {
    "36氪": "https://36kr.com/feed",
    "少数派": "https://sspai.com/feed",
    "IT之家": "https://www.ithome.com/rss/",
}
DEFAULT_HISTORY_FILE: Final[str] = "utils/history.txt"
DEFAULT_HISTORY_CAPACITY: Final[int] = 500
DEFAULT_LIMIT_PER_SOURCE: Final[int] = 15
DEFAULT_TOP_N: Final[int] = 10
DEFAULT_CANDIDATE_LIMIT: Final[int] = 24
DEFAULT_MODEL: Final[str] = "gemini-2.5-flash"
DEFAULT_OUTPUT_DIR: Final[str] = "每日简报"
DEFAULT_REPORT_PREFIX: Final[str] = "精选简报"
DEFAULT_REPORT_TITLE: Final[str] = "自动化科技简报"
DEFAULT_STYLE_ROLE: Final[str] = "专业科技新闻分析助手"
DEFAULT_ADVICE_LABEL: Final[str] = "技术观察"
DEFAULT_AUDIENCE: Final[str] = "关注科技与产业动态的读者"
DEFAULT_TONE: Final[str] = "客观、克制、少口号，优先事实和可执行建议"
DEFAULT_CONFIG_FILE: Final[str] = "briefing_config.json"
DEFAULT_INCLUDE_KEYWORDS: Final[list[str]] = [
    "AI",
    "Agent",
    "大模型",
    "开源",
    "编程",
    "开发者",
    "芯片",
    "操作系统",
    "安全",
    "机器人",
    "云计算",
]
DEFAULT_EXCLUDE_KEYWORDS: Final[list[str]] = [
    "明星",
    "综艺",
    "餐饮",
    "门店",
    "房价",
    "楼市",
    "股价",
]
DEFAULT_SOURCE_WEIGHTS: Final[dict[str, int]] = {}
DEFAULT_CATEGORY_KEYWORDS: Final[dict[str, list[str]]] = {
    "AI": ["AI", "Agent", "大模型", "模型", "智能体", "机器人"],
    "开发工具": ["编程", "开发者", "开源", "代码", "GitHub", "操作系统"],
    "硬件": ["芯片", "半导体", "处理器", "服务器", "存储", "GPU"],
    "安全": ["安全", "漏洞", "攻击", "隐私", "泄露", "加密"],
    "商业": ["融资", "IPO", "收购", "营收", "财报", "投资"],
}


@dataclass(frozen=True)
class BriefingConfig:
    sources: dict[str, str]
    history_file: str
    history_capacity: int
    model: str
    output_dir: str
    report_prefix: str
    report_title: str
    limit_per_source: int
    top_n: int
    candidate_limit: int
    include_keywords: list[str]
    exclude_keywords: list[str]
    source_weights: dict[str, int]
    category_keywords: dict[str, list[str]]
    style_role: str
    advice_label: str
    audience: str
    tone: str


def _load_config_file() -> dict[str, object]:
    """读取可选 JSON 配置文件。

    `briefing_config.json` 默认可不存在，方便旧部署继续运行。
    如果显式设置了 BRIEFING_CONFIG_FILE，文件缺失或格式错误会被视为配置错误。
    """

    configured_path = os.getenv("BRIEFING_CONFIG_FILE", "").strip()
    config_path = Path(configured_path or DEFAULT_CONFIG_FILE)
    if not config_path.exists():
        if configured_path:
            raise ValueError(f"配置文件不存在：{config_path}")
        return {}

    try:
        parsed = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"配置文件不是合法 JSON：{config_path}") from error

    if not isinstance(parsed, dict):
        raise ValueError(f"配置文件顶层必须是 JSON 对象：{config_path}")

    return parsed


def _section(config_data: dict[str, object], name: str) -> dict[str, object]:
    value = config_data.get(name, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"配置项 {name} 必须是 JSON 对象。")
    return value


def _config_text(section: dict[str, object], name: str, default: str) -> str:
    value = section.get(name)
    if value is None:
        return default
    return str(value).strip() or default


def _config_int(
    section: dict[str, object],
    name: str,
    default: int,
    minimum: int = 1,
) -> int:
    value = section.get(name)
    if value is None or value == "":
        return default

    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"配置项 {name} 必须是整数，当前值为 {value!r}。") from error

    if parsed < minimum:
        raise ValueError(f"配置项 {name} 必须大于等于 {minimum}，当前值为 {parsed}。")

    return parsed


def _config_string_list(
    section: dict[str, object],
    name: str,
    default: list[str],
) -> list[str]:
    value = section.get(name)
    if value is None:
        return list(default)
    if not isinstance(value, list):
        raise ValueError(f"配置项 {name} 必须是字符串数组。")

    result = [str(item).strip() for item in value if str(item).strip()]
    return result


def _config_int_dict(
    section: dict[str, object],
    name: str,
    default: dict[str, int],
) -> dict[str, int]:
    value = section.get(name)
    if value is None:
        return dict(default)
    if not isinstance(value, dict):
        raise ValueError(f"配置项 {name} 必须是对象。")

    result: dict[str, int] = {}
    for key, raw_weight in value.items():
        source_name = str(key).strip()
        if not source_name:
            continue
        try:
            result[source_name] = int(raw_weight)
        except (TypeError, ValueError) as error:
            raise ValueError(f"配置项 {name}.{source_name} 必须是整数。") from error

    return result


def _config_string_list_dict(
    section: dict[str, object],
    name: str,
    default: dict[str, list[str]],
) -> dict[str, list[str]]:
    value = section.get(name)
    if value is None:
        return {key: list(items) for key, items in default.items()}
    if not isinstance(value, dict):
        raise ValueError(f"配置项 {name} 必须是对象。")

    result: dict[str, list[str]] = {}
    for key, raw_items in value.items():
        category = str(key).strip()
        if not category:
            continue
        if not isinstance(raw_items, list):
            raise ValueError(f"配置项 {name}.{category} 必须是字符串数组。")
        items = [str(item).strip() for item in raw_items if str(item).strip()]
        if items:
            result[category] = items

    if not result:
        raise ValueError(f"配置项 {name} 至少需要一个有效分类。")

    return result


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = int(raw_value)
    except ValueError as error:
        raise ValueError(f"{name} 必须是整数，当前值为 {raw_value!r}。") from error

    if value < minimum:
        raise ValueError(f"{name} 必须大于等于 {minimum}，当前值为 {value}。")

    return value


def _env_text(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip() or default


def _normalize_sources(value: object, source_name: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f'{source_name} 必须是对象，格式如 {{"来源名":"RSS_URL"}}。')

    sources: dict[str, str] = {}
    for name, url in value.items():
        rss_name = str(name).strip()
        rss_url = str(url).strip()
        if not rss_name or not rss_url:
            continue
        sources[rss_name] = rss_url

    if not sources:
        raise ValueError(f"{source_name} 至少需要配置一个有效 RSS 源。")

    return sources


def _load_sources(config_data: dict[str, object]) -> dict[str, str]:
    sources = dict(DEFAULT_SOURCES)
    if "sources" in config_data:
        sources = _normalize_sources(config_data["sources"], "sources")

    # 保留环境变量覆盖，方便 GitHub Actions 等 CI 环境不改仓库文件也能配置源。
    raw_value = os.getenv("BRIEFING_SOURCES_JSON")
    if raw_value is None or not raw_value.strip():
        return sources

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError as error:
        raise ValueError("BRIEFING_SOURCES_JSON 必须是合法的 JSON 对象。") from error

    return _normalize_sources(parsed, "BRIEFING_SOURCES_JSON")


def load_config() -> BriefingConfig:
    """按优先级合并内置默认值、配置文件和环境变量。"""

    config_data = _load_config_file()
    history = _section(config_data, "history")
    output = _section(config_data, "output")
    selection = _section(config_data, "selection")
    filtering = _section(config_data, "filtering")
    style = _section(config_data, "style")

    return BriefingConfig(
        sources=_load_sources(config_data),
        history_file=_env_text(
            "BRIEFING_HISTORY_FILE",
            _config_text(history, "file", DEFAULT_HISTORY_FILE),
        ),
        history_capacity=_env_int(
            "BRIEFING_HISTORY_CAPACITY",
            _config_int(history, "capacity", DEFAULT_HISTORY_CAPACITY),
        ),
        model=_env_text("GEMINI_MODEL", DEFAULT_MODEL),
        output_dir=_env_text(
            "BRIEFING_OUTPUT_DIR",
            _config_text(output, "dir", DEFAULT_OUTPUT_DIR),
        ),
        report_prefix=_env_text(
            "BRIEFING_REPORT_PREFIX",
            _config_text(output, "prefix", DEFAULT_REPORT_PREFIX),
        ),
        report_title=_env_text(
            "BRIEFING_REPORT_TITLE",
            _config_text(output, "title", DEFAULT_REPORT_TITLE),
        ),
        limit_per_source=_env_int(
            "BRIEFING_LIMIT_PER_SOURCE",
            _config_int(selection, "limit_per_source", DEFAULT_LIMIT_PER_SOURCE),
        ),
        top_n=_env_int(
            "BRIEFING_TOP_N",
            _config_int(selection, "top_n", DEFAULT_TOP_N),
        ),
        candidate_limit=_env_int(
            "BRIEFING_CANDIDATE_LIMIT",
            _config_int(selection, "candidate_limit", DEFAULT_CANDIDATE_LIMIT),
        ),
        include_keywords=_config_string_list(
            filtering,
            "include_keywords",
            DEFAULT_INCLUDE_KEYWORDS,
        ),
        exclude_keywords=_config_string_list(
            filtering,
            "exclude_keywords",
            DEFAULT_EXCLUDE_KEYWORDS,
        ),
        source_weights=_config_int_dict(
            filtering,
            "source_weights",
            DEFAULT_SOURCE_WEIGHTS,
        ),
        category_keywords=_config_string_list_dict(
            filtering,
            "category_keywords",
            DEFAULT_CATEGORY_KEYWORDS,
        ),
        style_role=_env_text(
            "BRIEFING_STYLE_ROLE",
            _config_text(style, "role", DEFAULT_STYLE_ROLE),
        ),
        advice_label=_env_text(
            "BRIEFING_ADVICE_LABEL",
            _config_text(style, "advice_label", DEFAULT_ADVICE_LABEL),
        ),
        audience=_env_text(
            "BRIEFING_AUDIENCE",
            _config_text(style, "audience", DEFAULT_AUDIENCE),
        ),
        tone=_env_text(
            "BRIEFING_TONE",
            _config_text(style, "tone", DEFAULT_TONE),
        ),
    )

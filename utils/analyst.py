"""基于 Gemini 的摘要生成模块。"""

from __future__ import annotations

import time
from typing import Final

from google import genai

from utils.validator import ReportValidator

DEFAULT_STYLE_GUIDE: Final[dict[str, str]] = {
    "role": "专业科技新闻分析助手",
    "advice_label": "技术观察",
    "audience": "软件工程学生和技术从业者",
    "tone": "客观、克制、少口号，优先事实和可执行建议",
}
DEFAULT_RETRY_DELAYS: Final[tuple[int, ...]] = (15, 45, 90)
RETRYABLE_STATUS_CODES: Final[set[int]] = {429, 500, 502, 503, 504}
RETRYABLE_KEYWORDS: Final[tuple[str, ...]] = (
    "429",
    "500",
    "502",
    "503",
    "504",
    "service unavailable",
    "temporarily unavailable",
    "temporary unavailable",
    "too many requests",
    "rate limit",
    "resource exhausted",
    "quota exceeded",
    "overloaded",
    "backend error",
    "unavailable",
)


class GeminiChief:
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        top_n: int = 10,
        style_guide: dict[str, str] | None = None,
        retry_delays: tuple[int, ...] = DEFAULT_RETRY_DELAYS,
    ):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.top_n = top_n
        self.style_guide = DEFAULT_STYLE_GUIDE | (style_guide or {})
        self.retry_delays = retry_delays
        self.max_attempts = len(retry_delays) + 1

    def _build_package(self, intel_list: list[dict[str, str]]) -> str:
        return "\n\n".join(
            "\n".join(
                [
                    f"[{item['origin']}] {item['title']}",
                    f"分类：{item.get('category') or '其他'}",
                    f"本地评分：{item.get('score') or '未知'}",
                    f"发布时间：{item.get('published') or '未知'}",
                    f"摘要：{item['digest'][:300]}",
                    f"Link: {item['url']}",
                ]
            )
            for item in intel_list
        )

    def _build_prompt(self, intel_list: list[dict[str, str]]) -> str:
        package = self._build_package(intel_list)
        advice_label = self.style_guide["advice_label"]
        role = self.style_guide["role"]
        audience = self.style_guide["audience"]
        tone = self.style_guide["tone"]
        expected_count = min(self.top_n, len(intel_list))

        return (
            f"你是{role}。请从以下 {len(intel_list)} 条候选情报中精选 "
            f"Top {expected_count} 进行深度研判，目标读者是{audience}。"
            f"整体语气要求：{tone}。\n\n"
            f"{package}\n\n"
            "--- 最高指令 ---\n"
            "只输出日报正文，不要写开场白、总结、署名或解释。\n"
            "禁止使用私人称呼、军政化称谓或强拟人化汇报口吻。\n"
            f"必须输出 {expected_count} 条；如果候选不足该数量，则输出全部候选。\n"
            "每条情报只能对应一个候选来源，禁止把多个候选合并成同一条。\n"
            "必须保留原文 Link，且标题行只能包含一个 Markdown 链接。\n"
            "请你必须严格按照以下 Markdown 格式输出每一条情报：\n\n"
            "**[情报X] [{情报标题}]({原文Link})**\n"
            "* **[核心事实]**：一句话概括核心事件。\n"
            "* **[行业内参]**：深度分析行业影响与趋势。\n"
            f"* **[{advice_label}]**：专门为软件工程学生提供的技术关注点或行动建议。\n"
        )

    def _extract_status_code(self, error: Exception) -> int | None:
        for attr_name in ("status_code", "code"):
            value = getattr(error, attr_name, None)
            if isinstance(value, int):
                return value
            if isinstance(value, str) and value.isdigit():
                return int(value)

        response = getattr(error, "response", None)
        if response is not None:
            for attr_name in ("status_code", "status"):
                value = getattr(response, attr_name, None)
                if isinstance(value, int):
                    return value
                if isinstance(value, str) and value.isdigit():
                    return int(value)

        return None

    def _format_error(self, error: Exception) -> str:
        status_code = self._extract_status_code(error)
        message = " ".join(str(error).split()).strip() or error.__class__.__name__

        if len(message) > 220:
            message = f"{message[:217]}..."

        if status_code is not None and f"{status_code}" not in message:
            return f"HTTP {status_code}: {message}"

        return message

    def _should_retry(self, error: Exception) -> bool:
        status_code = self._extract_status_code(error)
        if status_code in RETRYABLE_STATUS_CODES:
            return True

        error_text = self._format_error(error).lower()
        return any(keyword in error_text for keyword in RETRYABLE_KEYWORDS)

    def _request_summary(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        result = (response.text or "").strip()
        if not result:
            raise RuntimeError("Gemini 返回空内容。")
        return result

    def _build_fallback_report(self, intel_list: list[dict[str, str]], reason: str) -> str:
        lines = [
            "## 系统说明",
            "",
            "> 本次为 AI 摘要失败后的 fallback 简报，仅保留基础信息以保证当日产物不断档。",
        ]

        if reason:
            lines.extend(["", f"> 失败原因：{reason}"])

        lines.extend(
            [
                "",
                f"## 今日新内容速览（共 {len(intel_list)} 条）",
                "",
            ]
        )

        for index, item in enumerate(intel_list, start=1):
            lines.extend(
                [
                    f"### [{index}] {item['title']}",
                    f"- 来源：{item['origin']}",
                    f"- 发布时间：{item.get('published') or '未知'}",
                    f"- 摘要：{item['digest'][:180]}",
                    f"- 原文链接：{item['url']}",
                    "",
                ]
            )

        return "\n".join(lines).rstrip() + "\n"

    def _validate_summary(self, summary: str, intel_count: int) -> str:
        # 这层只做格式门禁，不做事实核验；事实核验需要额外的信息源校对流程。
        expected_count = min(self.top_n, intel_count)
        validation = ReportValidator.validate(
            summary,
            expected_count=expected_count,
            advice_label=self.style_guide["advice_label"],
        )

        for warning in validation.warnings:
            print(f"[Report] 格式警告：{warning}")

        if validation.errors:
            error_text = "；".join(validation.errors[:3])
            if len(validation.errors) > 3:
                error_text += f"；另有 {len(validation.errors) - 3} 个问题"
            raise RuntimeError(f"Gemini 输出格式不合格：{error_text}")

        return validation.normalized_content

    def summarize(self, intel_list: list[dict[str, str]]) -> str:
        if not intel_list:
            return "今日无重大情报。"

        prompt = self._build_prompt(intel_list)
        last_error: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                print(f"[Gemini] 正在进行第 {attempt}/{self.max_attempts} 次摘要请求...")
                summary = self._request_summary(prompt)
                summary = self._validate_summary(summary, intel_count=len(intel_list))
                if attempt > 1:
                    print(f"[Gemini] 第 {attempt} 次请求成功，继续生成正式日报。")
                return summary
            except Exception as error:
                last_error = error
                error_text = self._format_error(error)
                has_next_attempt = attempt < self.max_attempts

                print(f"[Gemini] 第 {attempt} 次请求失败：{error_text}")

                if has_next_attempt and self._should_retry(error):
                    wait_seconds = self.retry_delays[attempt - 1]
                    print(
                        f"[Gemini] 判定为可重试错误，将在 {wait_seconds} 秒后发起下一次请求。"
                    )
                    time.sleep(wait_seconds)
                    continue

                if has_next_attempt:
                    print("[Gemini] 判定为不可重试错误，将直接生成 fallback 简报。")
                else:
                    print("[Gemini] 已达到最大重试次数，将生成 fallback 简报。")
                break

        fallback_reason = self._format_error(last_error) if last_error else "未知错误"
        print("[Gemini] AI 摘要不可用，开始生成 fallback 简报。")
        return self._build_fallback_report(intel_list, reason=fallback_reason)

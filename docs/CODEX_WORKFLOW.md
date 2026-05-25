# Codex 协作说明

这个项目适合用 Codex 做小步迭代。每次任务应有明确边界，避免把测试、重构、功能和文档混在一次改动里。

## 基本原则

- 每次任务只做一件事。
- 不顺手做大重构或风格迁移。
- 不修改 `GEMINI_API_KEY`、`GEMINI_MODEL` 名称。
- 不引入数据库、Web 框架、消息队列、Docker、Poetry、PDM、pre-commit。
- 测试不调用 Gemini，不访问真实 RSS。
- 非相关任务不改 GitHub Actions 的 cron、Secrets、日报产物路径或 push 逻辑。
- 不承诺事实核验；当前只做格式、链接和基础结构校验。

## 每次任务交付说明

Codex 完成后应说明：

- 修改了哪些文件；
- 运行了哪些验证命令；
- 行为是否变化；
- 剩余风险或后续建议。

## 推荐任务模板

```text
本次任务只做一件事：

<具体目标>

请先阅读：
- <相关文件>

允许修改：
- <允许文件或目录>

禁止修改：
- <明确边界>

验收标准：
- python -m ruff check .
- python -m ruff format --check .
- python -m pytest

完成后请说明：
1. 修改了哪些文件；
2. 运行了哪些验证；
3. 是否有剩余风险。
```

## PR Review Checklist

- 改动是否严格匹配任务范围。
- 是否没有改变未要求改变的运行行为。
- 测试是否不访问网络、不调用 Gemini。
- `python -m ruff check .` 是否通过。
- `python -m ruff format --check .` 是否通过。
- `python -m pytest` 是否通过。
- 如果改了命令、配置、workflow 或文件结构，README/docs 是否同步更新。
- 如果新增文件，是否考虑了复制/发布 allowlist 和 ignore 规则。

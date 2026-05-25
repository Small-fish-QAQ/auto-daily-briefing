# 开发者说明

本项目保持轻量定位：RSS 输入、本地候选筛选、Gemini 生成 Markdown、按日期归档、GitHub Actions 自动运行。开发时优先维护这条主链路，不引入重平台能力。

## 本地环境

GitHub Actions 当前使用 Python 3.10，本地开发建议尽量保持兼容。

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

只有运行 `python main.py` 才需要 `GEMINI_API_KEY`。测试和 lint 不应依赖 API Key。

## 常用命令

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

GitHub Actions 会先运行 `quality` job 执行以上检查，通过后才进入日报生成 job。

## 测试目录

- `tests/test_memory.py`：history 初始化、去重、更新、裁剪、原子写入。
- `tests/test_filter.py`：候选新闻打分、分类、近似去重、候选截断。
- `tests/test_validator.py`：Markdown 日报格式校验。
- `tests/test_config.py`：默认配置、JSON 覆盖、环境变量覆盖、错误处理。
- `tests/test_collector.py`：RSS 解析、清洗、失败隔离、去重。
- `tests/fixtures/`：小型、稳定、本地化的测试输入。

fixture 应保持最小，不放真实密钥、大型日报产物或依赖外网的内容。

## 测试边界

测试不要：

- 调用 Gemini；
- 访问真实 RSS 或外部网络；
- 依赖当前日期；
- 要求配置 `GEMINI_API_KEY`；
- 修改真实 `utils/history.txt` 或日报输出目录。

涉及文件系统、RSS、环境变量时，优先使用 `tmp_path`、`monkeypatch` 和本地 fixture。

## 修改后的验证清单

代码改动完成后至少运行：

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

如果新增配置、脚本、测试 fixture 或发布/复制相关文件，记得同步检查 README、allowlist/ignore 规则是否也需要更新。

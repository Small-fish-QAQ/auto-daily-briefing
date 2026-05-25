# 自动日报系统

一个基于 **RSS + Gemini + GitHub Actions** 的自动化日报项目。

它会定时抓取多个 RSS 源，过滤历史已处理内容，先做本地候选筛选与排序，再调用 Gemini 生成 Markdown 日报，并把结果按日期归档到仓库中。项目目标不是做成重平台，而是保持 **小而清晰、能长期自动跑** 的 `v0.3` 版本。

---

## 项目卖点

- **小而完整**：没有重型框架，核心链路短，适合个人维护。
- **自动闭环**：抓取、去重、摘要、归档、提交已串起来。
- **部署轻**：直接跑在 GitHub Actions 上，无需数据库或常驻服务。
- **输出稳定**：默认采用中性开源风格，也可以按目标读者自定义输出口吻。
- **可持续**：Gemini 高峰期失败时支持重试与 fallback，不至于当天完全断档。

---

## 核心流程

```text
+-------------+    +-------------+    +-------------+    +----------------+    +---------------+    +-------------+    +-------------+
| Actions 定时 | -> | RSS 抓取     | -> | 历史去重     | -> | 候选筛选 / 排序   | -> | Gemini 生成摘要 | -> | Markdown 归档 | -> | 提交回仓库   |
| / 手动触发   |    | collector   |    | memory      |    | filter         |    | analyst       |    | archiver    |    | git push    |
+-------------+    +-------------+    +-------------+    +----------------+    +---------------+    +-------------+    +-------------+
```

---

## 目录结构

```text
.
├─ .github/
│  └─ workflows/
│     └─ daily_briefing.yml
├─ docs/
│  ├─ CODEX_WORKFLOW.md
│  └─ DEVELOPMENT.md
├─ tests/
│  ├─ fixtures/
│  ├─ test_archiver.py
│  ├─ test_collector.py
│  ├─ test_config.py
│  ├─ test_filter.py
│  ├─ test_memory.py
│  ├─ test_pytest_validator.py
│  ├─ test_smoke_imports.py
│  └─ test_validator.py
├─ utils/
│  ├─ analyst.py
│  ├─ archiver.py
│  ├─ config.py
│  ├─ collector.py
│  ├─ filter.py
│  ├─ history.txt                    # 初始为空，运行后自动更新
│  ├─ memory.py
│  └─ validator.py
├─ briefing_config.example.json
├─ 每日简报/
│  └─ 2026/04/
│     └─ 2026-04-16-精选简报.md      # 示例输出
├─ .env.example
├─ .gitignore
├─ LICENSE
├─ main.py
├─ README.md
├─ pyproject.toml
├─ requirements-dev.txt
└─ requirements.txt
```

---

## 快速开始（推荐：先用 GitHub Actions 直接跑起来）

### 第一步：Fork 或创建你的仓库

把这个项目放到你自己的 GitHub 仓库里。

---

### 第二步：进入 GitHub Actions 配置页面

打开你的仓库后，依次进入：

```text
Settings → Secrets and variables → Actions
```

---

### 第三步：添加 Secret

在 **Secrets** 标签页点击 **New repository secret**，新增：

- **Name**：`GEMINI_API_KEY`
- **Secret**：你的 Gemini API Key

注意：

- 这里的 **Name 必须严格写成 `GEMINI_API_KEY`**
- 因为代码里读取的就是这个名字

---

### 第四步：添加 Variable（可选）

在 **Variables** 标签页点击 **New repository variable**，新增：

- **Name**：`GEMINI_MODEL`
- **Value**：`gemini-2.5-flash`

说明：

- 这里的 **Name 必须严格写成 `GEMINI_MODEL`**
- 如果你不配置它，程序也能跑，会自动回退到默认模型 `gemini-2.5-flash`

---

### 第五步：手动运行一次工作流

进入仓库顶部的 **Actions** 页面，找到对应工作流，点击 **Run workflow**，手动运行一次。

运行成功后，你应该能看到：

- `每日简报/` 下生成新的日报文件
- `utils/history.txt` 从初始空状态开始写入新的历史记录
- Actions 日志中能看到抓取、摘要、归档、提交过程

---

## 本地运行（适合开发和调试）

### 1. 克隆仓库到本地

```bash
git clone https://github.com/Small-fish-QAQ/auto-daily-briefing.git
cd auto-daily-briefing
```

解释：

- `git clone`：把 GitHub 上的仓库下载到你电脑本地
- `cd auto-daily-briefing`：进入这个项目文件夹

如果你的仓库名不是 `auto-daily-briefing`，请把命令中的目录名改成你自己的仓库名。

---

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

---

### 3. 配置本地环境变量和运行配置

复制 `.env.example` 为 `.env`，然后填写你的 Gemini API Key。

`.env` 示例：

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
# BRIEFING_CONFIG_FILE=briefing_config.json
```

然后按需复制 `briefing_config.example.json` 为 `briefing_config.json`，集中配置 RSS 源、抓取条数、输出目录、日报标题和摘要风格。这个文件不是必需的；不存在时程序会使用内置默认值。配置文件不应写入 API Key，且默认已被 `.gitignore` 排除，适合存放个人运行偏好。

> [!WARNING]
> `.env` 仅用于本地调试，请不要提交到 GitHub。
> 公开仓库时只保留 `.env.example`。
> 如果你使用 GitHub Actions，请在  
> `Settings → Secrets and variables → Actions`
> 中配置 `GEMINI_API_KEY`。

说明：

- `GEMINI_API_KEY`：必填
- `GEMINI_MODEL`：可选
- `BRIEFING_CONFIG_FILE`：可选，默认尝试读取 `briefing_config.json`
- 如果你**不填写** `GEMINI_MODEL`，程序会自动回退到默认模型：

```text
gemini-2.5-flash
```

---

### 4. 本地执行一次

```bash
python main.py
```

运行成功后，日报默认会生成到：

```text
每日简报/YYYY/MM/YYYY-MM-DD-精选简报.md
```

历史去重文件位于：

```text
utils/history.txt
```

### 5. 开发者测试

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

测试不会请求 Gemini，也不会访问外部 RSS。

GitHub Actions 会先运行 `quality` job，执行 ruff 和 pytest；通过后才会进入日报生成 job。

更多维护说明见：

- [开发者说明](docs/DEVELOPMENT.md)
- [Codex 协作说明](docs/CODEX_WORKFLOW.md)

## 为什么适合部署在 GitHub Actions

- 日报任务天然是定时批处理，不需要常驻服务。
- 产物本身就是 Markdown 文件，直接提交回仓库即可。
- 依赖少，运维面小，适合个人项目长期运行。
- 失败时可直接在 Actions 日志中定位问题，也可以手动补跑。

---

## 故障与降级策略

为了避免 Gemini 高峰期导致当日完全断更，当前版本加入了简单的容错逻辑。

### 当前策略

- 当 Gemini 返回 `429`、`503` 或其他临时服务不可用信号时，系统会进行有限次重试。
- 当前默认采用简单指数退避：

```text
15s -> 45s -> 90s
```

- 如果多次重试后仍失败，不会直接中断当天产物，而是生成一份 **fallback 简报**。
- fallback 简报至少保留：
  - 来源
  - 标题
  - 发布时间
  - RSS 摘要
  - 原文链接
- fallback 简报仍会按原有目录结构归档，随后继续更新 `history.txt`，避免第二天重复处理同一批内容。

---

## 仓库存放策略

当前版本采用 **“源码 + 产物同仓库”** 的策略：

- 源码、workflow、历史去重文件、日报 Markdown 都放在同一个仓库中。
- 这样做的主要目的，是简化 GitHub Actions 的提交逻辑、归档逻辑和展示链路。
- 对 `v0.1` 来说，这比拆分产物仓库或引入对象存储更稳妥，也更易维护。
- 当前仓库已经保留一批历史日报作为真实输出样例；实际运行后，新的日报会继续按日期累积。

如果后续历史日报规模继续扩大，再考虑：

- `gh-pages`
- 独立产物仓库
- 静态站展示层
- 对象存储

当前阶段不做这类复杂拆分。

---

## 配置方式

运行配置优先级如下：

```text
内置默认值 < briefing_config.json < 环境变量
```

推荐把个人运行参数放在本地 `briefing_config.json` 中，把公开默认值维护在 `briefing_config.example.json` 中；密钥放在 GitHub Secrets 或本地 `.env` 中。

`briefing_config.json` 示例：

```json
{
  "sources": {
    "36氪": "https://36kr.com/feed",
    "少数派": "https://sspai.com/feed",
    "IT之家": "https://www.ithome.com/rss/"
  },
  "selection": {
    "limit_per_source": 15,
    "top_n": 10,
    "candidate_limit": 24
  },
  "filtering": {
    "include_keywords": [
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
      "云计算"
    ],
    "exclude_keywords": [
      "明星",
      "综艺",
      "餐饮",
      "门店",
      "房价",
      "楼市",
      "股价"
    ],
    "source_weights": {},
    "category_keywords": {
      "AI": ["AI", "Agent", "大模型", "模型", "智能体", "机器人"],
      "开发工具": ["编程", "开发者", "开源", "代码", "GitHub", "操作系统"],
      "硬件": ["芯片", "半导体", "处理器", "服务器", "存储", "GPU"],
      "安全": ["安全", "漏洞", "攻击", "隐私", "泄露", "加密"],
      "商业": ["融资", "IPO", "收购", "营收", "财报", "投资"]
    }
  },
  "history": {
    "file": "utils/history.txt",
    "capacity": 500
  },
  "output": {
    "dir": "每日简报",
    "prefix": "精选简报",
    "title": "自动化科技简报"
  },
  "style": {
    "role": "专业科技新闻分析助手",
    "advice_label": "技术观察",
    "audience": "关注科技与产业动态的读者",
    "tone": "客观、克制、少口号，优先事实和可执行建议"
  }
}
```

### 筛选与偏好配置

日报生成前会先在本地对 RSS 新内容做一次轻量筛选，再把候选新闻交给 Gemini。

可重点调整这些字段：

| 配置项 | 作用 |
|---|---|
| `selection.limit_per_source` | 每个 RSS 源最多抓取多少条 |
| `selection.candidate_limit` | 本地筛选后最多交给 Gemini 的候选条数 |
| `selection.top_n` | Gemini 最终写入日报的条数 |
| `filtering.include_keywords` | 命中后加分，适合放你更关注的主题 |
| `filtering.exclude_keywords` | 命中后扣分，适合放你不想频繁看到的主题 |
| `filtering.source_weights` | 按来源整体加分或扣分，例如让某个 RSS 源优先级更高 |
| `filtering.category_keywords` | 用关键词给新闻打分类标签，辅助 Gemini 判断内容类型 |

例如，如果希望日报更偏 AI、开发工具、芯片和安全，可以把相关词加入 `include_keywords`；如果不想让娱乐、地产、股价快讯占位，可以放入 `exclude_keywords`。

### 环境变量

| 变量名 | 是否必填 | 说明 |
|---|---|---|
| `GEMINI_API_KEY` | 是 | Gemini API Key |
| `GEMINI_MODEL` | 否 | Gemini 模型名，默认 `gemini-2.5-flash` |
| `BRIEFING_CONFIG_FILE` | 否 | JSON 配置文件路径，默认 `briefing_config.json` |
| `BRIEFING_SOURCES_JSON` | 否 | 覆盖默认 RSS 源，格式为 JSON 对象，例如 `{"来源":"https://example.com/feed.xml"}` |
| `BRIEFING_LIMIT_PER_SOURCE` | 否 | 每个 RSS 源最多抓取条数，默认 `15` |
| `BRIEFING_TOP_N` | 否 | Gemini 精选输出条数，默认 `10` |
| `BRIEFING_CANDIDATE_LIMIT` | 否 | 进入 Gemini 前的候选新闻上限，默认 `24` |
| `BRIEFING_HISTORY_FILE` | 否 | 历史去重文件路径，默认 `utils/history.txt` |
| `BRIEFING_HISTORY_CAPACITY` | 否 | 历史链接保留上限，默认 `500` |
| `BRIEFING_OUTPUT_DIR` | 否 | 日报输出目录，默认 `每日简报` |
| `BRIEFING_REPORT_PREFIX` | 否 | 日报文件名后缀，默认 `精选简报` |
| `BRIEFING_REPORT_TITLE` | 否 | Markdown 顶部标题，默认 `自动化科技简报` |
| `BRIEFING_STYLE_ROLE` | 否 | Gemini 角色设定，默认 `专业科技新闻分析助手` |
| `BRIEFING_ADVICE_LABEL` | 否 | 建议字段名称，默认 `技术观察` |
| `BRIEFING_AUDIENCE` | 否 | 目标读者，默认 `关注科技与产业动态的读者` |
| `BRIEFING_TONE` | 否 | 输出语气要求，默认偏客观克制 |

---

## 输出说明

默认输出为 Markdown 文件，采用中性开源风格，不再绑定“统帅”“战报”等个人化称呼；角色、建议字段、目标读者和语气都可以通过配置文件调整。

归档文件头部会写入生成时间，正文通常为 Gemini 生成的精选摘要。生成后的 Markdown 会经过基础格式校验，重点检查情报标题、原文链接和固定字段；若 Gemini 失败或输出严重不合格，则会退化为基础信息版 fallback 简报。

当前仓库采用“源码 + 产物同仓库”策略，历史日报会随着工作流持续累积。若后续日报数量继续增长，可以再迁移到独立产物仓库、`gh-pages` 或静态站展示层。

示例路径：

```text
每日简报/2026/04/2026-04-16-精选简报.md
```

---

## 当前限制

- 依赖 RSS 源质量，源站摘要不完整时会影响输入质量。
- Gemini 摘要仍未做事实核验，当前只做格式和链接层面的质量门禁。
- 摘要风格已改为中性默认值，并支持通过配置文件调整，但还不是完整模板系统。
- 本地筛选只是启发式打分，不能完全替代人工选题或事实判断。
- 目前抓取和分析流程仍是串行的，优先保证简单可维护。
- RSS 抓取已有源级失败隔离，但还没有做并行抓取、缓存和更细粒度的内容正文抽取。

---

## Roadmap

- [x] 基于 RSS 抓取内容
- [x] GitHub Actions 定时运行
- [x] 历史去重
- [x] Gemini 摘要生成
- [x] 失败重试与 fallback 简报
- [x] 运行配置化
- [x] 日报格式质量门禁
- [x] 本地新闻候选筛选
- [ ] 扩展更多 RSS / 信息源
- [ ] 支持飞书推送
- [ ] 支持 Telegram / 邮件推送
- [ ] 提供更通用的日报提示词模板
- [ ] 增加并行抓取
- [ ] 提供简单的 Web 前端

---

## 开源说明

本项目是个人维护的开源项目，欢迎提交 issue 或讨论改进思路，但不保证实时响应。

---

## License

本项目采用 `MIT License` 开源，详见仓库中的 `LICENSE` 文件。

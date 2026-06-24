# skills

个人 Agent Skills 收藏仓库。每个子目录是一个独立的 skill，包含 `SKILL.md` 及其依赖文件。

兼容：**Claude Code / OpenClaw**（SKILL.md 原生）、**Hermes**（tap install）、**Codex / 通用**（clone 后直接运行）。

## 已收录

### `api-relay-audit/`

第三方 AI API 中转 / 代理服务的安全审计工具（红队向）。

- **来源**：[toby-bridges/api-relay-audit](https://github.com/toby-bridges/api-relay-audit)
- **版本**：v2.3.0
- **License**：AGPL-3.0-only（作者 Toby Bridges，再分发注意传染性条款）
- **依赖**：Python 3 + `curl`，零第三方库

检测项：隐藏 prompt 注入、prompt 泄漏、指令覆盖、上下文截断、tool-call 替换、包安装指令篡改、上游凭证 / 内部 header 泄漏、Anthropic SSE 流损坏、上游 channel 偷换、Web3 钱包安全注入、基础设施指纹、延迟方差。

**运行**：

```bash
python3 api-relay-audit/audit.py \
  --key "$API_RELAY_AUDIT_KEY" \
  --url "https://你的中转地址/v1" \
  --model claude-opus-4-6 \
  --profile general \
  --output api-relay-audit-report.md
```

`--profile` 支持 `general` / `web3` / `full`。`audit.py` 已随仓库本地化，运行时无需再联网拉取脚本。

> 切勿在报告、文件名、shell 记录或提交中泄露原始 API key；建议使用临时 / 低权限 key，审计后视情况轮换。

---

### `api-relay-perf-bench/`

第三方 AI API 中转服务的性能基准 + 响应纯净度检测工具。

- **创意来源**：[gigi1121/audit_ai_api](https://github.com/gigi1121/audit_ai_api)
- **版本**：v1.0.0
- **License**：AGPL-3.0-only
- **依赖**：Python 3 + `curl`，零第三方库

测量项：流式 TTFT、p50/p90/p95/p99 延迟、身份泄漏、系统提示泄漏、中转内部 token、语言不匹配、拒绝响应、空响应。输出自包含 HTML + JSON 报告。

**运行**：

```bash
# 单端点
python3 api-relay-perf-bench/perf-bench.py \
  --url "$PERF_BENCH_URL" \
  --key "$PERF_BENCH_KEY" \
  --vendor gpt \
  --rounds 10 \
  --output perf-report.html

# 多端点对比（JSON 配置，自备 config 文件）
python3 api-relay-perf-bench/perf-bench.py \
  --config your-endpoints.json \
  --output perf-report.html
```

> 与 `api-relay-audit` 互补：audit 做安全深查，perf-bench 做速度和纯净度快检。建议两者配合使用。

---

### `browser-act/`

Browser automation CLI for AI agents。提供 Stealth 反检测浏览器、Chrome 导入、无头浏览器自动化能力，支持数据提取、表单填写、截图、网络请求捕获、多浏览器并行、验证码自动处理等。

- **来源**：[BrowserAct](https://www.browseract.com)
- **安装**：`uv tool install browser-act-cli --python 3.12`
- **版本**：v2.0.2
- **License**：详见 SKILL.md
- **依赖**：Python 3.12+、uv package manager

核心功能：`stealth-extract`（反检测内容提取）、session 管理（多窗口隔离）、network request 捕获、solve-captcha。

> 参考用法见本仓库 `browser-act/SKILL.md`。browser-act 的 Stealth 浏览器可绕过 X/Twitter、Reddit 等站点的反爬检测。

---

### `browser-act-skill-forge/`

将任意网站的数据提取或操作需求转化为可复用的 Agent Skill 包（SKILL.md + Python 脚本）。先探索（API 优先，DOM 兜底），再生成已验证的 Skill 包，后续调用无需重复探索。

- **来源**：[BrowserAct](https://www.browseract.com)
- **版本**：v1.0.6
- **License**：详见 SKILL.md

典型场景：批量提取（数百/数千条记录）、网站内部 API 逆向、将现有爬虫/SaaS 工具复现为 Skill。

---

### `web-access/`

给 AI Agent 装上完整联网能力的 Skill — 联网策略 + CDP 浏览器操作 + 站点经验积累，兼容所有支持 SKILL.md 的 Agent（Claude Code、Cursor、Gemini CLI、Codex CLI 等）。

- **来源**：[eze-is/web-access](https://github.com/eze-is/web-access)
- **版本**：v2.5.3
- **License**：MIT
- **依赖**：Node.js 22+（原生 WebSocket）、Chrome / Edge / Chromium 系浏览器

核心能力：联网工具自动选择（WebSearch / WebFetch / curl / Jina / CDP）、CDP Proxy 直连用户日常浏览器（天然登录态）、三种点击方式（JS click / 真实鼠标事件 / 文件上传）、本地书签/历史检索、多目标并行子 Agent 分治、站点经验跨 session 积累。

> 与 `browser-act` 互补：`browser-act` 提供独立的 Stealth 反检测浏览器环境，`web-access` 直连用户日常浏览器并侧重联网策略调度。

---

### `humanizer/`

将 AI 生成文本改写为更自然人类风格的 Skill。基于 Wikipedia「AI 写作特征」指南，系统检测并修正：浮夸象征手法、推广性语言、空洞 -ing 分析、模糊归因、em dash 滥用、三段式、AI 特征词汇、负向平行句、过量连接短语等。

- **版本**：v2.1.1
- **来源**：clawic.com skill 市场
- **依赖**：无（纯提示工程）

---

### `prototype-html/`

根据产品需求生成可交互的单文件 HTML 原型。适合快速验证 UI 布局、交互逻辑和功能演示，无需搭建前端环境。

- **版本**：v1.0.0
- **依赖**：无（生成纯 HTML，浏览器直接打开）

---

### `self-improving/`

让 Agent 具备自我反思与持续学习能力的 Skill。当命令/工具失败、用户纠正、知识过时或发现更优方案时自动触发，将修正持久化写入本地记忆文件，下次对话直接应用。

- **版本**：v1.2.16
- **来源**：[clawic.com/skills/self-improving](https://clawic.com/skills/self-improving)
- **注意**：`corrections.md`、`memory.md`、`heartbeat-state.md`、`learning.md`、`reflections.md` 为运行时状态文件，已通过子目录 `.gitignore` 屏蔽，本地保留。

---

### `tc-exam-solver/`

自动完成 `ai-exam.tcredit.com` 飞书认证考试的 Skill。通过 CDP 直连用户已登录的 Chrome 浏览器，自动列出可选考试、逐题分析作答、二次核查后提交。

- **版本**：v1.0.0
- **依赖**：Python 3、Chrome 已登录飞书（保留 JWT）
- **注意**：必须等待 >5 分钟后再提交以规避机器人检测；PDF 培训材料为私有业务文件，仅本地保留。

**脚本说明**：

```
scripts/
  check_login.py    # 检查飞书登录态
  list_exams.py     # 列出可参加的考试
  start_exam.py     # 开始考试，返回题目
  get_questions.py  # 获取题目详情
  get_attempts.py   # 查看历史作答
  submit_exam.py    # 提交答案
```

---

### `tc-protohub/`

在 ProtoHub 私有沙箱管理 HTML 原型的 Skill。支持上传目录或 ZIP、更新现有原型、列出原型列表、获取预览链接，强制校验 `index.html` 入口文件。

- **版本**：v1.0.0
- **环境变量**：`PROTOHUB_API_KEY`、`PROTOHUB_URL`
- **依赖**：Python 3

> 与 `prototype-html` 配套使用：`prototype-html` 负责生成原型，`tc-protohub` 负责发布到 ProtoHub。

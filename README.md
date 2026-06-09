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

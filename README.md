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

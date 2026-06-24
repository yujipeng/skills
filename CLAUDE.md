# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库用途

个人 Agent Skills 收藏仓库。每个子目录是一个独立的 skill，包含 `SKILL.md` 和对应的可执行脚本。所有 skill 遵循 AGPL-3.0-only 许可证。

## 子目录结构

- `api-relay-audit/` — 安全审计 skill：`SKILL.md` + `audit.py`（零依赖，Python 3 + curl）
- `api-relay-perf-bench/` — 性能基准 skill：`SKILL.md` + `perf-bench.py`（多端点模式可自备 JSON 配置）
- `browser-act/` — 浏览器自动化 CLI：`SKILL.md`（需 `uv tool install browser-act-cli --python 3.12` 安装运行时）
- `browser-act-skill-forge/` — 网站数据提取 skill 生成器：`SKILL.md`
- `humanizer/` — 去除 AI 写作痕迹 skill：`SKILL.md` + `README.md`（纯提示工程，无依赖）
- `prototype-html/` — 交互式 HTML 产品原型生成 skill：`SKILL.md` + `assets/example.html`
- `self-improving/` — Agent 自我反思与持久学习 skill：`SKILL.md` + 多个规则/状态文件（运行时状态文件通过 `.gitignore` 屏蔽）
- `tc-exam-solver/` — 自动完成 tcredit 考试 skill：`SKILL.md` + 6 个 Python 脚本（通过 CDP 直连 Chrome）
- `tc-protohub/` — ProtoHub 原型管理 skill：`SKILL.md` + `scripts/publish.py` + `evals/evals.json`
- `web-access/` — AI Agent 联网能力 skill：`SKILL.md` + 5 个 Node.js 脚本（依赖 Node.js 22+，需 Chrome/Edge 开启远程调试）

## 运行脚本

```bash
# 安全审计
python3 api-relay-audit/audit.py \
  --key "$API_RELAY_AUDIT_KEY" \
  --url "$API_RELAY_AUDIT_URL" \
  --model claude-opus-4-6 \
  --profile general \
  --output api-relay-audit-report.md

# 性能基准（单端点）
python3 api-relay-perf-bench/perf-bench.py \
  --url "$PERF_BENCH_URL" \
  --key "$PERF_BENCH_KEY" \
  --vendor gpt \
  --rounds 10 \
  --output perf-report.html

# 性能基准（多端点 JSON 配置，自备 config 文件）
python3 api-relay-perf-bench/perf-bench.py \
  --config your-endpoints.json \
  --output perf-report.html

# web-access 环境检查与 CDP Proxy 启动（通常由 Agent 自动执行）
node web-access/scripts/check-deps.mjs
# 临时指定浏览器：node web-access/scripts/check-deps.mjs --browser edge
```

## SKILL.md 规范

每个 skill 的 `SKILL.md` 必须满足：

- frontmatter 包含：`name`、`description`（<1024 字符，以 "Use when" 开头）、`version`、`author`、`license`、`metadata.hermes.tags`
- 必须声明 `required_environment_variables`，禁止把 key 硬编码或出现在报告/日志中
- 相关 skill 通过 `metadata.hermes.related_skills` 关联
- 不使用环境变量配置的 skill（如 web-access，使用 config.env 文件）声明 `required_environment_variables: []`

## 安全要求

- API key 始终通过环境变量传入（`$API_RELAY_AUDIT_KEY`、`$PERF_BENCH_KEY`）
- 禁止在报告文件名、shell 日志、提交信息、GitHub 评论中出现原始 key
- 建议使用临时或低权限 key，审计后按需轮换
- 自备 JSON 配置文件时，key 用占位符或环境变量引用，禁止提交真实 key

## 版本管理

- `api-relay-audit` 来源：`toby-bridges/api-relay-audit` v2.3.0（AGPL-3.0-only）
- `api-relay-perf-bench` 作者：gigi1121，v1.0.0（AGPL-3.0-only）
- `browser-act` 来源：[BrowserAct](https://www.browseract.com) v2.0.2（安装：`uv tool install browser-act-cli --python 3.12`）
- `browser-act-skill-forge` 来源：[BrowserAct](https://www.browseract.com) v1.0.6
- `humanizer` 来源：clawic.com skill 市场，v2.1.1
- `prototype-html` 内部 skill，v1.0.0
- `self-improving` 来源：[clawic.com/skills/self-improving](https://clawic.com/skills/self-improving) v1.2.16
- `tc-exam-solver` 内部 skill，v1.0.0（针对 ai-exam.tcredit.com）
- `tc-protohub` 内部 skill，v1.0.0（针对 tcredit ProtoHub）
- `web-access` 来源：[eze-is/web-access](https://github.com/eze-is/web-access) v2.5.3（MIT 许可证）

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## 仓库用途

个人 Agent Skills 收藏仓库。每个子目录是一个独立的 skill，包含 `SKILL.md` 及其脚本、模板或参考资料。各 skill 保留上游许可证，具体见对应目录。

## 子目录结构

- `anatomy/` — 等距技术解释图 skill：根目录 `SKILL.md` + `references/` + `kit/` + `scripts/` + `examples/`，把技术概念构造成可交互的机械 / 仪器图（SVG、可选 WebGL / 3D），输出 HTML / SVG / React，可打印 A4 PDF（依赖 Node.js 20.10+、Chrome / Chromium；零 npm 依赖）
- `api-relay-audit/` — 安全审计 skill：`SKILL.md` + `audit.py`（零依赖，Python 3 + curl）
- `api-relay-perf-bench/` — 性能基准 skill：`SKILL.md` + `perf-bench.py`（多端点模式可自备 JSON 配置）
- `browser-act/` — 浏览器自动化 CLI：`SKILL.md`（需 `uv tool install browser-act-cli --python 3.12` 安装运行时）
- `browser-act-skill-forge/` — 网站数据提取 skill 生成器：`SKILL.md`
- `fireworks-tech-graph/` — 技术图生成 skill：自然语言生成 SVG + PNG，支持架构图、流程图、UML、ER 图和多种视觉风格
- `frontend-design/` — Anthropic 前端设计 skill：指导构建有明确视觉方向、避免模板感的生产级界面
- `guizang-ppt-skill/` — 归藏 PPT skill：生成电子杂志或瑞士风单文件 HTML 演示、配图和多平台封面
- `huashu-design/` — 花叔设计 skill：根目录 `SKILL.md` + `references/` + `assets/` + `scripts/` + `demos/`，覆盖高保真原型、HTML deck / 可编辑 PPTX、信息图、动画与 5 维评审（依赖 Node.js / FFmpeg / Playwright / Python）
- `huashu-motion/` — 花叔动效 skill：完整上游项目，skill 入口为 `skills/huashu-motion/`，`bin/om` 优先调用同级 `cli/`（缺失时回退 `npx huashu-motion`），支持发布片 / 动效片、作曲、音效、口播和 studio 点选修改（依赖 Node.js 22+ / Chrome / FFmpeg）
- `humanizer/` — 去除 AI 写作痕迹 skill：`SKILL.md` + `README.md` + Claude 插件元数据（纯提示工程，无运行时依赖）
- `humanizer-zh/` — 中文去 AI 写作痕迹 skill：针对中文表达检测并重写模板化、宣传化和机械排比等模式
- `life-decision-guide/` — 人生决策查询 skill：先到《高性价比人生指南》查条目，再按成本（钱/时间/毅力）、收益量级和证据等级 A/B/C 排序作答并给出处，查不到不编（纯提示工程，正文运行时现取）
- `moli-jev/` — Moli + jev 浏览器操作 skill：`SKILL.md` + vendored `jev-ultrafast/`（上游 `browser-use/jev-ultrafast` commit `1231850`，MIT），通过 CDP 驱动 Moli 完成点击、填表和多步导航；依赖 Python 3.12+ / `uv` 与 Moli 1.1.18+，`.env` 本地保存 key 且不入库
- `multica-server-setup/` — Multica 服务器端 agent 安装与定时更新 skill：`SKILL.md` + 3 个 Bash 脚本 + 2 份文档 + 3 个模板（一键安装、服务器精简/开发机完整每周更新、crontab/systemd/launchd）
- `newapi-billing/` — NewAPI 计费表达式设计 skill：`SKILL.md`（纯提示工程，无运行时依赖，支持固定价格/阶梯定价/多模态/动态调价）
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
  --model Codex-opus-4-6 \
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

# huashu-design 本机能力探测（生图 / 兄弟 skill / Node / FFmpeg / Playwright）
python3 huashu-design/scripts/capabilities.py

# huashu-motion 环境检查（Node / Chrome / FFmpeg 与可选模型）
huashu-motion/skills/huashu-motion/bin/om doctor

# anatomy 示例重建（输出独立 HTML；加 --light 出浅色主题）
node anatomy/examples/dial-indicator/build.mjs
```

## SKILL.md 规范

每个 skill 的 `SKILL.md` 必须满足：

- frontmatter 包含：`name`、`description`（<1024 字符，以 "Use when" 开头）、`version`、`author`、`license`、`metadata.hermes.tags`
- 必须声明 `required_environment_variables`，禁止把 key 硬编码或出现在报告/日志中
- 相关 skill 通过 `metadata.hermes.related_skills` 关联
- 不使用环境变量配置的 skill（如 web-access，使用 config.env 文件）声明 `required_environment_variables: []`
- 上游原样收录的第三方 skill（`anatomy`、`huashu-design`、`huashu-motion`）保留上游 frontmatter 以便同步，不强制套用上述字段；新增或本地维护的 skill 仍需满足。

## 安全要求

- API key 始终通过环境变量传入（`$API_RELAY_AUDIT_KEY`、`$PERF_BENCH_KEY`）
- 禁止在报告文件名、shell 日志、提交信息、GitHub 评论中出现原始 key
- 建议使用临时或低权限 key，审计后按需轮换
- 自备 JSON 配置文件时，key 用占位符或环境变量引用，禁止提交真实 key

## 版本管理

- `anatomy` 来源：[wheresryan22/anatomy](https://github.com/wheresryan22/anatomy) v1.1.0 后 53 个提交（commit `1482e84`；MIT）
- `api-relay-audit` 来源：`toby-bridges/api-relay-audit` v2.4.0（AGPL-3.0-only）
- `api-relay-perf-bench` 作者：gigi1121，v1.0.0（AGPL-3.0-only）
- `browser-act` 来源：[BrowserAct](https://www.browseract.com) v2.0.2（安装：`uv tool install browser-act-cli --python 3.12`）
- `browser-act-skill-forge` 来源：[BrowserAct](https://www.browseract.com) v1.0.6
- `fireworks-tech-graph` 来源：[yizhiyanhua-ai/fireworks-tech-graph](https://github.com/yizhiyanhua-ai/fireworks-tech-graph) v1.2.0（MIT）
- `frontend-design` 来源：[anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/frontend-design) `main`（许可证见 `frontend-design/LICENSE.txt`）
- `guizang-ppt-skill` 来源：[op7418/guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill) `main`（AGPL-3.0）
- `huashu-design` 来源：[alchaincyf/huashu-design](https://github.com/alchaincyf/huashu-design) v3.0.0（MIT，2026-05-14 起；早期版本为 Personal Use License）
- `huashu-motion` 来源：[alchaincyf/huashu-motion](https://github.com/alchaincyf/huashu-motion) v0.1.0 后 1 个提交（commit `3e92780`；MIT，GSAP Standard License、字体 OFL 1.1、「豆子花叔」角色不在 MIT 范围内）
- `humanizer` 来源：[blader/humanizer](https://github.com/blader/humanizer) v2.11.1（MIT）
- `humanizer-zh` 来源：[op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh) `main`（MIT）
- `life-decision-guide` 来源：[eternity4719/HowToLiveBetter](https://github.com/eternity4719/HowToLiveBetter) 的 `skills/life-decision-guide/` v1.0.0（CC-BY-4.0；正文约 1.3 MB 不随本仓库分发，运行时现取）
- `moli-jev` 内部 skill，v1.1.0（vendored [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast) commit `1231850`，MIT；运行时依赖 `uv` 与 Moli 1.1.18+）
- `multica-server-setup` 内部 skill，v1.0.0（源自本仓库 `tests/` 实测脚本与教程；基于 `@deepseek-ai/dsh` + `@multica-ai/dsh-runtime` + `@huiliyi37/dsh-tianshu-tui` 组合，dsh 版本以 `--probe` 验证）
- `prototype-html` 来源：[vagerent/prototype-html](https://github.com/vagerent/prototype-html) v1.0.0（Apache-2.0）
- `self-improving` 来源：[clawic.com/skills/self-improving](https://clawic.com/skills/self-improving) v1.2.16
- `tc-exam-solver` 内部 skill，v1.0.0（针对 ai-exam.tcredit.com）
- `tc-protohub` 来源：[airclear/skills](https://github.com/airclear/skills/tree/main/skills/tc-protohub) `main`（本地元数据 v1.0.0；默认 `PROTOHUB_URL` 已适配 tcredit 测试环境）
- `web-access` 来源：[eze-is/web-access](https://github.com/eze-is/web-access) v2.5.4（MIT 许可证）

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

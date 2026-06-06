---
name: api-relay-perf-bench
description: Use when benchmarking AI API relay latency with streaming TTFT measurements, p50/p95/p99 percentiles, and running purity/injection checks against relay responses — detects identity leakage, system-prompt leakage, relay-internal tokens, language mismatches, refusals, and empty responses.
version: 1.0.0
author: gigi1121
license: AGPL-3.0-only
platforms: [linux, macos]
metadata:
  hermes:
    tags: [performance, benchmarking, ai-safety, api-relay, purity-check]
    related_skills: [api-relay-audit]
required_environment_variables:
  - name: PERF_BENCH_KEY
    prompt: Relay API key for perf benchmark
    help: Use a temporary or low-scope key for the relay being tested.
    required_for: Running benchmarks without pasting secrets into chat
  - name: PERF_BENCH_URL
    prompt: Relay base URL for perf benchmark
    help: Example https://relay.example.com
    required_for: Running benchmarks without pasting URLs into chat
---

# API Relay Perf Bench

## Overview

This skill runs `perf-bench.py`, a **zero-dependency** performance and purity benchmark for third-party AI API relays. It measures streaming latency (TTFT, p50/p95/p99), detects injection/purity anomalies in relay responses, and produces a self-contained HTML + JSON comparison report.

It is the **performance companion** to `api-relay-audit` (which covers security). Use both together for a complete relay evaluation: `api-relay-audit` for safety, `api-relay-perf-bench` for speed and response purity.

The standalone `perf-bench.py` needs only Python 3 and `curl` — no `pip install`, no `httpx`, no `PyYAML`.

## When to Use

- The user wants to measure streaming TTFT and total latency (p50/p90/p95/p99) for one or more API relays.
- The user wants to compare multiple relays side-by-side in a single HTML report.
- The user suspects a relay is injecting hidden prompts, leaking upstream tokens, substituting model identities, refusing benign prompts, or returning empty/pure-English responses to Chinese prompts.
- The user wants a quick purity verdict (clean / suspicious / injected / failed) from a batch of perf test responses.
- The user needs reproducible benchmark configs (JSON) for periodic relay monitoring.

Do not use this skill for full security auditing (use `api-relay-audit`), general model quality benchmarking, or provider price comparison. The purity check is a lightweight heuristic, not a deep audit.

## Install or Share

Repository: **https://github.com/yujipeng/skills** — adapted from the original work at https://github.com/gigi1121/audit_ai_api

### Claude Code / OpenClaw

The SKILL.md format is natively compatible. Place the `api-relay-perf-bench/` directory under your agent's skills folder, or reference it from your `CLAUDE.md` / agent config.

### Hermes

```bash
hermes skills tap add yujipeng/skills
hermes skills install yujipeng/skills/api-relay-perf-bench
```

### Codex / General (any agent with shell access)

Clone and run directly — no agent integration needed:

```bash
git clone https://github.com/yujipeng/skills
python3 skills/api-relay-perf-bench/perf-bench.py --url "$PERF_BENCH_URL" --key "$PERF_BENCH_KEY" --vendor gpt
```

## Required Inputs

| Input | How to provide it | Notes |
|---|---|---|
| Relay API key | Prefer `$PERF_BENCH_KEY` via `.env` or agent secure env | Use a temporary or low-scope key when possible. |
| Base URL | Ask the user or use `$PERF_BENCH_URL` if already set | Example: `https://relay.example.com`. |
| Vendor | `gpt` or `claude` preset | Selects representative models for the vendor. |
| Model | Optional; use `--model` to pin specific model IDs | Overrides vendor preset. Repeatable. |
| Format | Optional; `openai` (default) or `anthropic` | Wire format for streaming requests. |

Never print the raw API key in summaries, filenames, reports, shell traces, or GitHub comments. If the user pasted a key into chat, avoid repeating it and recommend rotating it after the benchmark if exposure matters.

## Standard Workflow

1. Confirm the target base URL, vendor (or explicit model list), and report output path.
2. Ensure the key is available as `$PERF_BENCH_KEY`. If it is missing, ask the user to set it via `.env` or agent env setup — not by committing it.
3. Download the standalone script into a temporary directory unless the current repo already contains `perf-bench.py`.
4. Run the benchmark and write HTML + JSON reports.
5. Summarize only evidence from the generated report. Do not overstate reliability or make policy promises.

## One-Shot Benchmark Recipe

Use this when the user provides a base URL and vendor:

```bash
set -euo pipefail

: "${PERF_BENCH_KEY:?Set PERF_BENCH_KEY via .env or agent secure env first}"
: "${PERF_BENCH_URL:?Set PERF_BENCH_URL to the relay base URL}"

VENDOR="${PERF_BENCH_VENDOR:-gpt}"
WORKDIR="$(mktemp -d)"
OUTDIR="${PWD}"

curl -fsSL \
  "https://raw.githubusercontent.com/gigi1121/audit_ai_api/main/perf-bench.py" \
  -o "$WORKDIR/perf-bench.py"

python3 "$WORKDIR/perf-bench.py" \
  --url "$PERF_BENCH_URL" \
  --key "$PERF_BENCH_KEY" \
  --vendor "$VENDOR" \
  --rounds 10 \
  --output "$OUTDIR/perf-report.html"

printf 'Reports written to %s/perf-report.{html,json}\n' "$OUTDIR"
```

If the current working tree is the `skills` repository and `perf-bench.py` exists, prefer the local file:

```bash
python3 perf-bench.py \
  --url "$PERF_BENCH_URL" \
  --key "$PERF_BENCH_KEY" \
  --vendor "${PERF_BENCH_VENDOR:-gpt}" \
  --rounds 10 \
  --output perf-report.html
```

### Multi-Endpoint JSON Config

For side-by-side relay comparison, use a JSON config file:

```json
{
  "test": {
    "prompt": "请介绍北京好吃的",
    "rounds": 10,
    "concurrency": 1,
    "timeout": 60,
    "max_tokens": 512,
    "format": "openai"
  },
  "default_models": ["gpt-5.5", "gpt-5.4", "claude-opus-4-7",  "claude-opus-4-8", "gemini-3.5-flash" , "gemini-3.1-pro-preview"],
  "endpoints": [
    {
      "name": "relay-a",
      "base_url": "https://relay-a.example.com",
      "api_key": "sk-REPLACE_ME_A"
    },
    {
      "name": "relay-b",
      "base_url": "https://relay-b.example.com",
      "api_key": "sk-REPLACE_ME_B"
    }
  ]
}
```

```bash
python3 perf-bench.py --config comparison.json --output reports/comparison.html
```

## CLI Flags Reference

| Flag | Default | Description |
|---|---|---|
| `--url` | (required) | Single endpoint base URL |
| `--key` | (required) | Single endpoint API key |
| `--vendor` | — | `gpt` or `claude` preset |
| `--model` | — | Explicit model ID (repeatable) |
| `--format` | `openai` | `openai` or `anthropic` wire format |
| `--prompt` | `请介绍北京好吃的` | Test prompt (benign, common Chinese query) |
| `--prompts-file` | — | File with one prompt per line (round-robin across rounds) |
| `--rounds` | `10` | Rounds per (endpoint, model) combination |
| `--concurrency` | `1` | Parallel streamed rounds |
| `--timeout` | `60` | Per-request timeout in seconds |
| `--max-tokens` | `512` | `max_tokens` per request |
| `--temperature` | (omitted) | Only set if explicitly passed; newer models reject any value |
| `--system` | — | Optional system prompt |
| `--config` | — | JSON config path (mutually exclusive with `--url`/`--key`) |
| `--output` | `perf-report.html` | HTML report path |
| `--json` | auto | JSON output path (defaults to sibling of HTML) |
| `--title` | auto | Override report title |
| `--quiet` | off | Less stderr noise |

### Quick Reference: Invocation Styles

```bash
# 1. Shortest — positional
python3 perf-bench.py https://relay.example.com sk-... gpt

# 2. Flag form
python3 perf-bench.py --url https://relay.example.com --key sk-... \
    --vendor claude --rounds 5

# 3. JSON config (multi-endpoint)
python3 perf-bench.py --config comparison.json --output report.html
```

## Cost Controls

| Scenario | Recommended flags |
|---|---|
| Quick smoke test | `--rounds 3 --max-tokens 64` |
| Normal benchmark | `--rounds 10` |
| High-confidence latency measurement | `--rounds 30` |
| Batch stress test | `--concurrency 4 --rounds 20` |
| Anthropic native format only | `--format anthropic` |
| Single model only | `--model gpt-4o-mini` |

## What the Detection Items Cover

| Item | Area | Purpose |
|---|---|---|
| Identity Leak | Response self-identification | Detects non-Claude/non-OpenAI identities (GLM, DeepSeek, Qwen, GPT, ERNIE, etc.) via 26 keywords with strict/lax/CJK/context-strict four-tier matching. Requires an identity anchor phrase ("I am", "我是", etc.) for common-English keywords. |
| System Prompt Leak | Template token leakage | Detects `[INST]`, `<|im_start|>`, `you are a helpful assistant`, `ignore previous instructions`, and other relay-injected template artefacts. |
| Relay Internal Token | Credential leakage | Flags `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `Bearer sk-`, `x-api-key`, `internal_only`, `DEBUG_PROMPT`, and other sentinel tokens that should never appear in a relayed response. |
| Empty Response | Silent failure | Detects completely empty or whitespace-only responses. |
| Refusal | Unexpected rejection | Flags English refusal phrases (`I cannot`, `I'm unable to`) and Chinese refusal phrases (`抱歉无法`, `对不起不能`) on a benign cuisine prompt. |
| Language Mismatch | Prompt/response language mismatch | When the prompt is mostly Chinese, flags responses that are mostly English (>80% non-CJK characters, with ≥60 chars). Catches relays that ignore the user's language. |

## Purity Verdict Logic

The verdict is aggregated across all rounds for each (endpoint, model) pair:

| Verdict | Condition |
|---|---|
| `clean` | All rounds succeeded with no issues, or no injection markers found |
| `suspicious` | Majority refusals, majority language mismatches, frequent empty responses, or >50% failed rounds (but no injection markers) |
| `injected` | Identity leak, system-prompt leak, or relay-internal token found in any response |
| `failed` | Every round errored upstream (0 OK rounds) |

## Performance Metrics

| Metric | Description |
|---|---|
| **TTFT** | Time to first token — measured via `time.perf_counter()` from request start to first SSE delta content |
| **Total latency** | Wall-clock time from request start to end-of-stream |
| **p50 / p90 / p95 / p99** | Linear-interpolation percentiles (numpy-compatible) |
| **stdev** | Sample standard deviation |
| **Success rate** | Fraction of rounds that completed without transport/HTTP error |
| **Output chars** | Response text character count distribution |
| **Chunk count** | Number of SSE data chunks observed |

## Report Output

Two files are always produced:

- **HTML** (`perf-report.html`) — Self-contained, single-file report with no external dependencies. Embeds the full JSON data inline and renders side-by-side comparison tables, per-endpoint detail panels, latency distribution grids, purity summaries, and per-round drill-down with text previews.
- **JSON** (`perf-report.json`) — Machine-readable structured result with schema version 1. Contains all raw metrics, purity records, per-round details, and model-list data. Suitable for CI pipelines or custom dashboards.

Open the HTML file directly in a browser — no server required.

## Report Summary Template

After running the benchmark, summarize in this format:

```markdown
## Perf Bench Result: <relay host>

Vendor: gpt / claude | Format: openai / anthropic
Rounds per model: 10 | Concurrency: 1

| Model | TTFT avg | TTFT p95 | Total avg | Total p95 | Purity |
|---|---|---|---|---|---|
| gpt-4o-mini | 0.23s | 0.45s | 2.1s | 3.2s | clean |
| gpt-5.5 | 0.18s | 0.35s | 1.9s | 2.8s | clean |
| claude-opus-4-7 | 0.41s | 0.82s | 4.5s | 7.1s | clean |

Overall success rate: 100%
Purity issues: none
```

If purity issues are found, include the specific verdict and reason. If latency is bimodal (large gap between p50 and p95), flag it as a possible A/B routing signal.

## Common Pitfalls

1. Do not treat "clean" purity as proof of safety. The purity check is heuristic, not exhaustive — use `api-relay-audit` for deep security validation.
2. Do not paste or repeat API keys in chat. Prefer `$PERF_BENCH_KEY`.
3. The HTML report embeds all data inline — it can be up to several MB for large benchmarks. Share via file, not inline in chat.
4. `temperature` is omitted from request bodies by default because newer models (e.g., `claude-opus-4-7`) reject any value with HTTP 400.
5. TTFT is measured at the SSE byte level — it captures the relay's first response, not the upstream model's first token. A relay that buffers before streaming will show inflated TTFT.
6. Do not promise latency SLAs or product comparisons from a single benchmark run. Network conditions and relay load change over time.
7. The `--vendor` flag uses hardcoded model lists that may become outdated. For critical benchmarks, use explicit `--model` flags instead.

## Verification Checklist

- [ ] `api-relay-perf-bench/SKILL.md` frontmatter has `name`, `description`, `version`, `author`, `license`, and `metadata.tags`.
- [ ] Description is under 1024 characters and starts with "Use when".
- [ ] The benchmark command uses `$PERF_BENCH_KEY`, not a literal key.
- [ ] Both HTML and JSON reports were generated and the key was not echoed.
- [ ] JSON config files (if used) use placeholder keys (`sk-REPLACE_ME_*`), not real credentials.
- [ ] Any public reply or GitHub comment is grounded only in the report or current code.
- [ ] The skill notes that `perf-bench.py` is zero-dependency (Python 3 + curl only) and complements, not replaces, `api-relay-audit`.

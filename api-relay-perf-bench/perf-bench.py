#!/usr/bin/env python3
"""Zero-dependency perf benchmark for AI API relays.

Single-file, stdlib + curl only. No pip install needed.

Usage::

    # Shortest form (positional)
    python3 perf-bench.py https://relay.example.com sk-... gpt
    python3 perf-bench.py https://relay.example.com sk-... claude

    # Single endpoint, flag form
    python3 perf-bench.py --url https://relay.example.com --key sk-... \\
        --vendor claude --rounds 3

    # Multi-endpoint JSON config
    python3 perf-bench.py --config config.json --output reports/comparison.html

Dependencies: python3, curl (system).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import html
import json
import math
import os
import re
import ssl
import subprocess
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from typing import Iterable, Optional
from urllib.parse import urlparse

# ============================================================================
# Section 1 — Identity patterns (inlined from identity_patterns.py)
# ============================================================================

NON_CLAUDE_IDENTITY_KEYWORDS = (
    "amazon", "kiro", "aws",
    "glm", "z.ai", "deepseek", "qwen", "minimax", "grok", "gpt",
    "antigravity", "deepmind",
    "warp", "windsurf",
    "zhipu", "tongyi", "ernie", "doubao", "moonshot", "kimi",
    "通义", "千问", "智谱", "豆包", "文心", "月之暗面",
)

_STRICT_ASCII_KEYWORDS = frozenset({
    "amazon", "kiro", "aws", "grok", "gpt", "ernie", "kimi",
})

_CONTEXT_STRICT_KEYWORDS = frozenset({
    "warp", "windsurf",
})

_IDENTITY_ANCHOR_ALTERNATION = (
    r"i am|i'm|i am a|i'm a|i am an|i'm an|i am the|i'm the|"
    r"i was made|i was created|i was developed|i was built|i was trained|"
    r"i was released|i was fine[- ]?tuned|"
    r"made by|created by|developed by|built by|trained by|powered by|"
    r"released by|fine[- ]?tuned by|"
    r"my name is|my name's|call me|you can call me|"
    r"we are|we're|"
    r"我是|我叫|本人是|我的名字|我是一个|我是个|本 ?ai"
)

_IDENTITY_SUFFIX_PATTERN = (
    r"(?:"
    r"\s*[,.:;!?)\-—，。！？；）]"
    r"|\s+(?:assistant|ai|model|bot|chatbot|agent|by|from|made|created|"
    r"developed|built|designed|trained|powered|an?\s)"
    r"|\s*$"
    r")"
)

_CJK_ANCHOR_ALTERNATION = r"我是|我叫|本人是|我的名字是?|我是一个|我是个|本 ?ai"


def _build_strict_pattern(keyword):
    return re.compile(
        r"(?:" + _IDENTITY_ANCHOR_ALTERNATION + r")"
        r"\s+(?:(?!not\s|isn'?t\s|aren'?t\s|wasn'?t\s|weren'?t\s|unlike\s)\w+\s+){0,6}?"
        r"\b" + re.escape(keyword) + r"(?![a-zA-Z])",
        re.IGNORECASE,
    )


def _build_context_strict_pattern(keyword):
    return re.compile(
        r"(?:" + _IDENTITY_ANCHOR_ALTERNATION + r")"
        r"\s+(?:(?!not\s|isn'?t\s|aren'?t\s|wasn'?t\s|weren'?t\s|unlike\s)\w+\s+){0,6}?"
        r"\b" + re.escape(keyword) + r"(?![a-zA-Z])"
        + _IDENTITY_SUFFIX_PATTERN,
        re.IGNORECASE,
    )


_STRICT_ASCII_PATTERNS = tuple(
    (kw, _build_strict_pattern(kw))
    for kw in NON_CLAUDE_IDENTITY_KEYWORDS
    if kw in _STRICT_ASCII_KEYWORDS
)
_CONTEXT_STRICT_PATTERNS = tuple(
    (kw, _build_context_strict_pattern(kw))
    for kw in NON_CLAUDE_IDENTITY_KEYWORDS
    if kw in _CONTEXT_STRICT_KEYWORDS
)
_LAX_ASCII_PATTERNS = tuple(
    (kw, re.compile(r"\b" + re.escape(kw) + r"(?![a-zA-Z])", re.IGNORECASE))
    for kw in NON_CLAUDE_IDENTITY_KEYWORDS
    if kw.isascii() and kw not in _STRICT_ASCII_KEYWORDS
    and kw not in _CONTEXT_STRICT_KEYWORDS
)
_CJK_KEYWORDS = tuple(
    kw for kw in NON_CLAUDE_IDENTITY_KEYWORDS if not kw.isascii()
)
_CJK_STRICT_PATTERNS = tuple(
    (kw, re.compile(
        r"(?:" + _CJK_ANCHOR_ALTERNATION + r")"
        r"\s*" + re.escape(kw) + r"(?![a-zA-Z])",
        re.IGNORECASE,
    ))
    for kw in NON_CLAUDE_IDENTITY_KEYWORDS
    if kw in _STRICT_ASCII_KEYWORDS
)
_CJK_CONTEXT_STRICT_PATTERNS = tuple(
    (kw, re.compile(
        r"(?:" + _CJK_ANCHOR_ALTERNATION + r")"
        r"\s*" + re.escape(kw) + r"(?![a-zA-Z])"
        + _IDENTITY_SUFFIX_PATTERN,
        re.IGNORECASE,
    ))
    for kw in NON_CLAUDE_IDENTITY_KEYWORDS
    if kw in _CONTEXT_STRICT_KEYWORDS
)

_IDENTITY_ANCHORS = [
    r"\bi\s+am\b", r"\bi'?m\b", r"\bmy\s+name\s+is\b",
    r"\bcalled\b", r"i\s+was\s+made\s+by",
    r"我是", r"本人是", r"我叫", r"我的名字是", r"我由",
]
_IDENTITY_ANCHOR_RX = re.compile("|".join(_IDENTITY_ANCHORS), re.I)


def find_non_claude_identities(text: str) -> list:
    """Return sorted list of non-Claude identity keywords found in text."""
    if not text:
        return []
    matched = []
    for keyword, pattern in _STRICT_ASCII_PATTERNS:
        if pattern.search(text):
            matched.append(keyword)
    for keyword, pattern in _CONTEXT_STRICT_PATTERNS:
        if pattern.search(text):
            matched.append(keyword)
    for keyword, pattern in _CJK_STRICT_PATTERNS:
        if keyword not in matched and pattern.search(text):
            matched.append(keyword)
    for keyword, pattern in _CJK_CONTEXT_STRICT_PATTERNS:
        if keyword not in matched and pattern.search(text):
            matched.append(keyword)
    for keyword, pattern in _LAX_ASCII_PATTERNS:
        if pattern.search(text):
            matched.append(keyword)
    for keyword in _CJK_KEYWORDS:
        if keyword in text:
            matched.append(keyword)
    return sorted(matched)


def _identity_anchored(text: str, keyword: str) -> bool:
    """Return True iff an identity-claim anchor occurs near keyword."""
    lower = text.lower()
    kw = keyword.lower()
    idx = 0
    while True:
        pos = lower.find(kw, idx)
        if pos < 0:
            return False
        window = text[max(0, pos - 80): pos + len(keyword)]
        if _IDENTITY_ANCHOR_RX.search(window):
            return True
        idx = pos + len(keyword)


# ============================================================================
# Section 2 — Purity analysis (inlined from purity.py)
# ============================================================================

SYSTEM_LEAK_PATTERNS = [
    re.compile(r"you are (?:a|an) (?:helpful|harmless|honest)", re.I),
    re.compile(r"\bsystem\s*[:：]\s*you", re.I),
    re.compile(r"<\|(?:im_start|im_end|system|user|assistant)\|>", re.I),
    re.compile(r"\[INST\]|\[/INST\]"),
    re.compile(r"<\|begin_of_text\|>|<\|end_of_text\|>"),
    re.compile(r"忽略.{0,15}(?:之前|上面|以上).{0,15}指令", re.I),
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions", re.I),
]

REFUSAL_PATTERNS = [
    re.compile(r"\b(?:i\s*can(?:not|'t)|i\s*am\s*unable\s*to|i\s*won'?t)\b", re.I),
    re.compile(r"抱歉.{0,10}(?:无法|不能|不可以)", re.I),
    re.compile(r"对不起.{0,10}(?:无法|不能)", re.I),
    re.compile(r"我没有(?:相关|这方面)?(?:的)?(?:能力|信息)", re.I),
]

LEAKAGE_TOKENS = [
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "Bearer sk-",
    "x-api-key", "internal_only", "DEBUG_PROMPT",
    "===SYSTEM===", "###SYSTEM###",
]


def _ratio_chinese(text: str) -> float:
    if not text:
        return 0.0
    cn = 0
    total = 0
    for ch in text:
        if ch.isspace():
            continue
        total += 1
        if "CJK" in unicodedata.name(ch, ""):
            cn += 1
    return cn / total if total else 0.0


def analyze_response(text: str, *, prompt: str, model: str,
                     ok: bool, round_index: int) -> dict:
    """Examine one streamed response, return a flat purity record dict."""
    issues: list[str] = []
    identities: list[str] = []
    refusal = False
    empty = False
    language_mismatch = False
    text_preview = (text or "")[:400]

    if not ok:
        issues.append("upstream_error")
        return dict(round_index=round_index, ok=ok, text_preview=text_preview,
                    issues=issues, identities=identities, refusal=refusal,
                    empty=empty, language_mismatch=language_mismatch)
    if not text or not text.strip():
        empty = True
        issues.append("empty_response")
        return dict(round_index=round_index, ok=ok, text_preview=text_preview,
                    issues=issues, identities=identities, refusal=refusal,
                    empty=empty, language_mismatch=language_mismatch)

    # Identity leakage
    found = find_non_claude_identities(text)
    if found:
        anchored = [kw for kw in found if _identity_anchored(text, kw)]
        if anchored:
            identities = anchored
            issues.append("identity_leak")

    # System-prompt leakage
    for pat in SYSTEM_LEAK_PATTERNS:
        if pat.search(text):
            issues.append("system_prompt_leak")
            break
    for token in LEAKAGE_TOKENS:
        if token in text:
            issues.append("relay_internal_token")
            break

    # Refusals
    for pat in REFUSAL_PATTERNS:
        if pat.search(text):
            refusal = True
            issues.append("refusal")
            break

    # Language mismatch
    if _ratio_chinese(prompt) >= 0.5:
        if len(text) >= 60 and _ratio_chinese(text) < 0.2:
            language_mismatch = True
            issues.append("language_mismatch")

    return dict(round_index=round_index, ok=ok, text_preview=text_preview,
                issues=issues, identities=identities, refusal=refusal,
                empty=empty, language_mismatch=language_mismatch)


def analyze_purity(records: list[dict]) -> dict:
    """Aggregate purity records into a summary dict."""
    total = len(records)
    ok_count = sum(1 for r in records if r["ok"])
    clean = sum(1 for r in records if r["ok"] and not r["issues"])

    issue_counts: dict[str, int] = {}
    identities_seen: dict[str, int] = {}
    refusal_count = empty_count = lang_count = 0
    for r in records:
        for iss in r["issues"]:
            issue_counts[iss] = issue_counts.get(iss, 0) + 1
        for kw in r["identities"]:
            identities_seen[kw] = identities_seen.get(kw, 0) + 1
        if r["refusal"]:
            refusal_count += 1
        if r["empty"]:
            empty_count += 1
        if r["language_mismatch"]:
            lang_count += 1

    # Verdict logic
    verdict, reason = "unknown", ""
    if total == 0:
        verdict, reason = "failed", "no rounds"
    elif ok_count == 0:
        verdict, reason = "failed", "every round errored upstream"
    elif issue_counts.get("identity_leak"):
        kws = sorted(identities_seen.keys())
        verdict, reason = "injected", f"identity leak detected ({', '.join(kws)})"
    elif issue_counts.get("system_prompt_leak"):
        verdict, reason = "injected", "system prompt / template tokens leaked"
    elif issue_counts.get("relay_internal_token"):
        verdict, reason = "injected", "relay-internal token found in response"
    elif issue_counts.get("language_mismatch", 0) > ok_count * 0.5:
        verdict, reason = "suspicious", "majority of responses ignored the prompt language"
    elif issue_counts.get("refusal", 0) > ok_count * 0.5:
        verdict, reason = "suspicious", "majority refusals on a benign prompt"
    elif empty_count > ok_count * 0.3:
        verdict, reason = "suspicious", "frequent empty responses"
    elif ok_count < total * 0.5:
        verdict, reason = "suspicious", f"only {ok_count}/{total} rounds succeeded"
    elif clean == ok_count and ok_count == total:
        verdict, reason = "clean", "all rounds responded coherently with no markers"
    else:
        verdict, reason = "clean", f"{clean}/{total} clean rounds, no injection markers"

    return {
        "rounds_total": total, "rounds_ok": ok_count, "rounds_clean": clean,
        "issue_counts": issue_counts, "identities_seen": identities_seen,
        "refusal_count": refusal_count, "empty_count": empty_count,
        "language_mismatch_count": lang_count,
        "verdict": verdict, "verdict_reason": reason,
    }


# ============================================================================
# Section 3 — Metrics (inlined from metrics.py)
# ============================================================================

def percentile(values: list[float], pct: float) -> Optional[float]:
    """Linear-interpolation percentile (numpy-compatible)."""
    if not values:
        return None
    if len(values) == 1:
        return float(values[0])
    s = sorted(values)
    rank = (pct / 100.0) * (len(s) - 1)
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return float(s[lo])
    frac = rank - lo
    return float(s[lo] + (s[hi] - s[lo]) * frac)


def summarize_latencies(values: Iterable[float]) -> dict:
    """Return count/min/avg/max/p50/p90/p95/p99/stdev dict."""
    clean = [v for v in values if v is not None]
    if not clean:
        return {"count": 0, "min": None, "avg": None, "max": None,
                "p50": None, "p90": None, "p95": None, "p99": None,
                "stdev": None}
    n = len(clean)
    avg = sum(clean) / n
    stdev = math.sqrt(sum((x - avg) ** 2 for x in clean) / (n - 1)) if n > 1 else 0.0
    return {
        "count": n, "min": float(min(clean)), "avg": float(avg),
        "max": float(max(clean)),
        "p50": percentile(clean, 50), "p90": percentile(clean, 90),
        "p95": percentile(clean, 95), "p99": percentile(clean, 99),
        "stdev": float(stdev),
    }


# ============================================================================
# Section 4 — Streaming client via curl
# ============================================================================

CURL_STATUS_SENTINEL = "__PERF_BENCH_HTTP_STATUS__:"
LOOPBACK_NO_PROXY = "localhost,127.0.0.1,::1"
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _curl_loopback_no_proxy_args(url: str) -> list:
    if urlparse(url).hostname in LOOPBACK_HOSTS:
        return ["--noproxy", LOOPBACK_NO_PROXY]
    return []


def _curl_get_json(url: str, headers_list: list[tuple[str, str]],
                   timeout: float = 15.0) -> tuple[int, dict, str]:
    """GET JSON through curl. Returns (status_code, parsed_json_dict, error)."""
    cmd = ["curl", "-sk", *_curl_loopback_no_proxy_args(url),
           url, "--max-time", str(int(timeout))]
    for k, v in headers_list:
        cmd.extend(["-H", f"{k}: {v}"])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
        if r.returncode != 0:
            return 0, {}, f"curl failed: {r.stderr[:200]}"
        try:
            return 200, json.loads(r.stdout), ""
        except json.JSONDecodeError:
            return 200, {}, f"invalid JSON: {r.stdout[:200]}"
    except subprocess.TimeoutExpired:
        return 0, {}, "timeout"
    except Exception as e:
        return 0, {}, f"{type(e).__name__}: {e}"


def stream_call_openai(base_url: str, api_key: str, model: str, prompt: str,
                       system: Optional[str], max_tokens: int,
                       temperature: Optional[float], timeout: float) -> dict:
    """Stream an OpenAI-format chat completion via curl, return result dict."""
    url = base_url.rstrip("/")
    if not url.endswith("/v1"):
        url += "/v1"
    url += "/chat/completions"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = {"model": model, "messages": messages, "max_tokens": max_tokens,
            "stream": True}
    if temperature is not None:
        body["temperature"] = temperature

    headers = [
        ("Authorization", f"Bearer {api_key}"),
        ("content-type", "application/json"),
        ("accept", "text/event-stream"),
    ]
    return _curl_stream(url, headers, body, model, "openai", timeout)


def stream_call_anthropic(base_url: str, api_key: str, model: str, prompt: str,
                          system: Optional[str], max_tokens: int,
                          temperature: Optional[float], timeout: float) -> dict:
    """Stream an Anthropic-format message via curl, return result dict."""
    url = base_url.rstrip("/")
    if url.endswith("/v1"):
        url = url[:-3]
    url += "/v1/messages"

    body = {"model": model, "max_tokens": max_tokens, "stream": True,
            "messages": [{"role": "user", "content": prompt}]}
    if temperature is not None:
        body["temperature"] = temperature
    if system:
        body["system"] = system

    headers = [
        ("x-api-key", api_key),
        ("anthropic-version", "2023-06-01"),
        ("content-type", "application/json"),
        ("accept", "text/event-stream"),
    ]
    return _curl_stream(url, headers, body, model, "anthropic", timeout)


def _curl_stream(url: str, headers: list[tuple[str, str]], body: dict,
                 model: str, format: str, timeout: float) -> dict:
    """Core curl streaming: POST body via stdin, parse SSE from stdout.

    Uses ``curl -N --no-buffer`` to disable output buffering so SSE events
    arrive as they're sent. The HTTP status code is extracted from a ``-w``
    sentinel line appended by curl after the response body.

    Returns a flat dict with keys: ok, ttft, total_time, text, chunk_count,
    finish_reason, status_code, error, format, model, response_headers.
    """
    cmd = [
        "curl", "-sk", *_curl_loopback_no_proxy_args(url),
        "-N", "--no-buffer", "-X", "POST", url,
        "--max-time", str(timeout),
        "-w", f"\n{CURL_STATUS_SENTINEL}%{{http_code}}\n",
        "--data-binary", "@-",
    ]
    for k, v in headers:
        cmd.extend(["-H", f"{k}: {v}"])

    start = time.perf_counter()
    ttft = None
    text_parts: list[str] = []
    chunk_count = 0
    finish_reason: Optional[str] = None
    status_code = 0
    error: Optional[str] = None
    response_headers: dict[str, str] = {}
    first_chunk_raw = None

    try:
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            proc.stdin.write(json.dumps(body).encode("utf-8"))
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass

        http_status = [None]
        non_sse_preview: list[str] = []
        status_prefix = CURL_STATUS_SENTINEL.encode("utf-8")

        while True:
            line = proc.stdout.readline()
            if not line:
                break
            stripped = line.strip()
            if stripped.startswith(status_prefix):
                try:
                    http_status[0] = int(
                        stripped[len(status_prefix):].decode("ascii",
                                                              errors="ignore"))
                except ValueError:
                    pass
                continue
            decoded = line.decode("utf-8", errors="replace").strip()
            if not decoded.startswith("data:"):
                if decoded and len(non_sse_preview) < 4:
                    non_sse_preview.append(decoded)
                continue
            data = decoded[5:].strip()
            if data == "[DONE]":
                break
            try:
                evt = json.loads(data)
            except json.JSONDecodeError:
                continue
            chunk_count += 1
            if first_chunk_raw is None:
                first_chunk_raw = data[:500]
            # Extract delta text based on format
            delta_text = ""
            if format == "openai":
                delta_text = _openai_delta_text(evt)
                fr = _openai_finish_reason(evt)
            else:
                delta_text = _anthropic_delta_text(evt)
                fr = _anthropic_stop_reason(evt)
            if delta_text:
                if ttft is None:
                    ttft = time.perf_counter() - start
                text_parts.append(delta_text)
            if fr:
                finish_reason = fr

        proc.wait(timeout=timeout + 10)

        if http_status[0] is not None:
            status_code = http_status[0]
            if status_code >= 400:
                preview = " ".join(non_sse_preview)[:200]
                if error is None:
                    error = (f"HTTP {status_code} on stream open "
                             f"(non-SSE body: {preview})" if preview
                             else f"HTTP {status_code} on stream open")
        elif chunk_count == 0 and non_sse_preview:
            status_code = 0
            if error is None:
                error = f"Non-SSE stream response: {' '.join(non_sse_preview)[:200]}"

        if proc.returncode != 0:
            curl_err = proc.stderr.read().decode("utf-8", errors="replace")[:200]
            if error is None:
                error = f"curl failed: {curl_err}"
            if status_code == 0:
                status_code = proc.returncode

    except subprocess.TimeoutExpired:
        if error is None:
            error = "curl stream timeout"
        try:
            proc.kill()
        except Exception:
            pass
    except Exception as e:
        if error is None:
            error = f"{type(e).__name__}: {e}"

    total_time = time.perf_counter() - start
    return {
        "ok": error is None and status_code == 200,
        "ttft": ttft,
        "total_time": total_time,
        "text": "".join(text_parts),
        "chunk_count": chunk_count,
        "finish_reason": finish_reason,
        "status_code": status_code,
        "error": error,
        "format": format,
        "model": model,
        "raw_first_chunk": first_chunk_raw,
        "response_headers": response_headers,
    }


def _openai_delta_text(evt: dict) -> str:
    choices = evt.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    delta = choices[0].get("delta") or {}
    content = delta.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for block in content:
            if isinstance(block, dict) and isinstance(block.get("text"), str):
                out.append(block["text"])
        return "".join(out)
    msg = choices[0].get("message")
    if isinstance(msg, dict) and isinstance(msg.get("content"), str):
        return msg["content"]
    return ""


def _openai_finish_reason(evt: dict) -> Optional[str]:
    choices = evt.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    return choices[0].get("finish_reason")


def _anthropic_delta_text(evt: dict) -> str:
    if (evt.get("type") == "content_block_delta"
            and evt.get("delta", {}).get("type") == "text_delta"):
        return evt["delta"].get("text", "")
    return ""


def _anthropic_stop_reason(evt: dict) -> Optional[str]:
    if evt.get("type") == "message_delta":
        return evt.get("delta", {}).get("stop_reason")
    return None


def fetch_models(base_url: str, api_key: str) -> tuple[list[str], Optional[str]]:
    """Best-effort /v1/models lookup via curl. Returns (model_ids, error)."""
    base = base_url.rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    url = base + "/models"
    header_sets = [
        [("Authorization", f"Bearer {api_key}")],
        [("x-api-key", api_key), ("anthropic-version", "2023-06-01")],
    ]
    last_err = None
    for hdrs in header_sets:
        status, payload, err = _curl_get_json(url, hdrs)
        if status == 200:
            data = payload.get("data") or payload
            if isinstance(data, list):
                ids = []
                for item in data:
                    if isinstance(item, dict):
                        mid = item.get("id") or item.get("model")
                        if isinstance(mid, str):
                            ids.append(mid)
                    elif isinstance(item, str):
                        ids.append(item)
                if ids:
                    return ids, None
            last_err = f"HTTP {status}: empty model list"
        else:
            last_err = err or f"HTTP {status}"
    return [], last_err


# ============================================================================
# Section 5 — Benchmark runner
# ============================================================================

DEFAULT_PROMPT = "请介绍北京好吃的"
DEFAULT_ROUNDS = 10
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_TOKENS = 512
DEFAULT_CONCURRENCY = 1

VENDOR_MODELS: dict[str, list[str]] = {
    "gpt": ["gpt-5.2", "gpt-5.3-codex", "gpt-5.5"],
    "claude": ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-7"],
}
DEFAULT_MODELS: list[str] = VENDOR_MODELS["gpt"] + VENDOR_MODELS["claude"]


def vendor_models(vendor: str) -> list[str]:
    key = (vendor or "").strip().lower()
    if key not in VENDOR_MODELS:
        raise ValueError(
            f"unknown vendor {vendor!r}; choose from {sorted(VENDOR_MODELS)}")
    return list(VENDOR_MODELS[key])


def _short_host(url: str) -> str:
    h = url.split("//", 1)[-1].split("/", 1)[0]
    return h.replace(":", "_")


def load_config(path: str) -> dict:
    """Load a JSON benchmark config file.

    Config schema::

        {
          "test": {                           // optional, all keys have defaults
            "prompt": "请介绍北京好吃的",
            "rounds": 10,
            "concurrency": 1,
            "timeout": 60,
            "max_tokens": 512,
            "format": "openai",
            "system": null,
            "prompts": ["prompt1", ...]       // optional, overrides prompt
          },
          "default_models": ["model1", ...],  // optional
          "endpoints": [
            {
              "name": "my-relay",
              "base_url": "https://...",
              "api_key": "sk-...",
              "models": ["gpt-4o", ...],      // optional
              "vendor": "gpt",                // optional, overrides models
              "format": "openai"              // optional, default "openai"
            }
          ]
        }
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"config root must be a mapping, got {type(raw).__name__}")

    test_raw = raw.get("test") or {}
    temperature = test_raw.get("temperature")

    cfg = {
        "test": {
            "prompt": test_raw.get("prompt", DEFAULT_PROMPT),
            "rounds": int(test_raw.get("rounds", DEFAULT_ROUNDS)),
            "timeout": float(test_raw.get("timeout", DEFAULT_TIMEOUT)),
            "max_tokens": int(test_raw.get("max_tokens", DEFAULT_MAX_TOKENS)),
            "temperature": None if temperature is None else float(temperature),
            "concurrency": int(test_raw.get("concurrency", DEFAULT_CONCURRENCY)),
            "format": test_raw.get("format", "openai"),
            "system": test_raw.get("system"),
            "prompts": test_raw.get("prompts"),
        },
        "default_models": list(raw.get("default_models", [])),
        "endpoints": [],
    }

    for ep in raw.get("endpoints", []):
        if not isinstance(ep, dict):
            continue
        if not ep.get("base_url") or not ep.get("api_key"):
            raise ValueError(f"endpoint missing base_url/api_key: {ep!r}")
        explicit_models = list(ep.get("models", []))
        vendor = ep.get("vendor")
        if not explicit_models and vendor:
            explicit_models = vendor_models(vendor)
        default_name = _short_host(ep["base_url"])
        if vendor:
            default_name = f"{default_name}-{vendor}"
        cfg["endpoints"].append({
            "name": ep.get("name") or default_name,
            "base_url": ep["base_url"],
            "api_key": ep["api_key"],
            "models": explicit_models or None,
            "format": ep.get("format", cfg["test"]["format"]),
            "vendor": vendor,
        })
    if not cfg["endpoints"]:
        raise ValueError("config must define at least one endpoint")
    return cfg


def _execute_one(endpoint: dict, model: str, prompt: str, system: Optional[str],
                 max_tokens: int, temperature: Optional[float],
                 timeout: float, format: str) -> dict:
    """Execute a single streaming call, return StreamResult-like flat dict."""
    if format == "anthropic":
        return stream_call_anthropic(
            endpoint["base_url"], endpoint["api_key"], model, prompt,
            system, max_tokens, temperature, timeout)
    return stream_call_openai(
        endpoint["base_url"], endpoint["api_key"], model, prompt,
        system, max_tokens, temperature, timeout)


def _run_rounds_for_model(*, endpoint: dict, model: str, test: dict, log) -> dict:
    """Run all rounds for one (endpoint, model) pair."""
    rounds = test["rounds"]
    concurrency = max(1, test["concurrency"])
    prompts: list[str] = test.get("prompts") or [test["prompt"]]
    timeout = test["timeout"]
    max_tokens = test["max_tokens"]
    temperature = test["temperature"]
    system = test.get("system")
    fmt = endpoint["format"]

    results: list[Optional[dict]] = [None] * rounds

    def _run(idx: int) -> None:
        prompt = prompts[idx % len(prompts)]
        log(f"    round {idx + 1}/{rounds} prompt={prompt[:24]!r}")
        results[idx] = _execute_one(
            endpoint, model, prompt, system, max_tokens, temperature, timeout, fmt)

    if concurrency == 1:
        for i in range(rounds):
            _run(i)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
            list(ex.map(_run, range(rounds)))

    rows: list[dict] = []
    purity_records: list[dict] = []
    ttft_values: list[float] = []
    total_values: list[float] = []
    output_chars: list[int] = []

    for idx, r in enumerate(results):
        if r is None:
            r = {"ok": False, "ttft": None, "total_time": 0, "text": "",
                 "chunk_count": 0, "finish_reason": None, "status_code": 0,
                 "error": "internal: result was None", "format": fmt, "model": model}
        prompt = prompts[idx % len(prompts)]
        rec = analyze_response(r.get("text", ""), prompt=prompt, model=model,
                               ok=r["ok"], round_index=idx + 1)
        purity_records.append(rec)
        if r["ok"] and r["ttft"] is not None:
            ttft_values.append(r["ttft"])
        if r["ok"]:
            total_values.append(r["total_time"])
        if r.get("text"):
            output_chars.append(len(r["text"]))
        rows.append({
            "round": idx + 1,
            "ok": r["ok"],
            "status_code": r.get("status_code", 0),
            "ttft_seconds": r["ttft"],
            "total_seconds": r["total_time"],
            "output_chars": len(r.get("text", "") or ""),
            "chunk_count": r.get("chunk_count", 0),
            "finish_reason": r.get("finish_reason"),
            "error": r.get("error"),
            "format": r.get("format", fmt),
            "text_preview": (r.get("text", "") or "")[:280],
            "issues": list(rec["issues"]),
            "language_mismatch": rec["language_mismatch"],
            "identities_detected": list(rec["identities"]),
        })

    purity = analyze_purity(purity_records)

    return {
        "model": model,
        "rounds": rows,
        "errors": [row["error"] for row in rows if not row["ok"]],
        "metrics": {
            "ttft_seconds": summarize_latencies(ttft_values),
            "total_seconds": summarize_latencies(total_values),
            "output_chars": summarize_latencies(output_chars),
            "success_rate": (sum(1 for row in rows if row["ok"]) / len(rows)
                             if rows else 0.0),
            "successful_rounds": sum(1 for row in rows if row["ok"]),
            "failed_rounds": sum(1 for row in rows if not row["ok"]),
        },
        "purity": purity,
    }


def run_benchmark(config: dict, *, model_filter: Optional[list[str]] = None,
                  log_fn=None) -> dict:
    """Run the full benchmark matrix, return JSON-serialisable result."""
    log = log_fn or (lambda msg: print(msg, file=sys.stderr))
    started = time.perf_counter()
    started_iso = datetime.now(timezone.utc).isoformat()

    test = config["test"]
    default_models = config.get("default_models") or DEFAULT_MODELS

    endpoint_results = []
    for ep in config["endpoints"]:
        log(f"[endpoint] {ep['name']} -> {ep['base_url']}")
        listed_models, list_err = fetch_models(ep["base_url"], ep["api_key"])
        if list_err:
            log(f"  /v1/models failed: {list_err}")
        else:
            log(f"  /v1/models returned {len(listed_models)} ids")

        models = ep["models"] or default_models
        if model_filter:
            models = [m for m in models if m in set(model_filter)]
        log(f"  testing models: {models}")

        per_model = []
        for model in models:
            log(f"  [model] {model}")
            try:
                row = _run_rounds_for_model(endpoint=ep, model=model,
                                            test=test, log=log)
            except Exception as e:
                log(f"    fatal error during model {model}: {e}")
                row = {
                    "model": model, "rounds": [], "errors": [f"{type(e).__name__}: {e}"],
                    "metrics": None, "purity": None, "fatal": True,
                }
            per_model.append(row)

        endpoint_results.append({
            "name": ep["name"], "base_url": ep["base_url"],
            "format": ep["format"], "vendor": ep.get("vendor"),
            "models_tested": models, "models_listed": listed_models,
            "models_listed_error": list_err,
            "results": per_model,
        })

    elapsed = time.perf_counter() - started
    return {
        "schema_version": 1,
        "tool": "api-relay-audit perf-bench (zero-dep)",
        "generated_at": started_iso,
        "elapsed_seconds": elapsed,
        "test": {**test, "default_models": default_models},
        "endpoints": endpoint_results,
    }


# ============================================================================
# Section 6 — Report writers (inlined from report.py)
# ============================================================================

def write_json_report(result: dict, path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def write_html_report(result: dict, path: str, *, title: str = "") -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    title = title or _default_title(result)
    payload = json.dumps(result, ensure_ascii=False)
    payload_safe = payload.replace("</", "<\\/")
    html_doc = _HTML_TEMPLATE.replace("{{TITLE}}", html.escape(title))\
        .replace("{{DATA}}", payload_safe)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html_doc)


def _default_title(result: dict) -> str:
    eps = result.get("endpoints", [])
    names = [ep.get("name", "?") for ep in eps]
    when = result.get("generated_at", datetime.utcnow().isoformat())
    return f"API Relay Perf Comparison — {' vs '.join(names)} ({when[:16]})"


_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{{TITLE}}</title>
<style>
  :root {
    --bg: #0c0d10; --panel: #15171c; --border: #2a2e36;
    --fg: #e8e8e8; --muted: #9aa1ad; --accent: #4dd2ff;
    --green: #4cd28a; --yellow: #f3c969; --red: #ff6b6b;
    --grey: #5a606e;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 24px 28px 60px;
    background: var(--bg); color: var(--fg);
    font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI",
                  "PingFang SC", "Helvetica Neue", Arial, sans-serif;
  }
  h1 { font-size: 22px; margin: 0 0 4px; }
  h2 { font-size: 16px; margin: 24px 0 12px; color: var(--accent); }
  h3 { font-size: 14px; margin: 18px 0 8px; }
  .meta { color: var(--muted); font-size: 12px; margin-bottom: 18px; }
  .panel {
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 8px; padding: 16px 18px; margin-bottom: 18px;
  }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td {
    padding: 6px 10px; border-bottom: 1px solid var(--border);
    text-align: left; vertical-align: top;
  }
  th { color: var(--muted); font-weight: 500; }
  tr:last-child td { border-bottom: none; }
  td.num { font-variant-numeric: tabular-nums; text-align: right; }
  .pill {
    display: inline-block; padding: 2px 8px; border-radius: 999px;
    font-size: 11px; font-weight: 600; letter-spacing: .02em;
  }
  .pill.clean      { background: rgba(76,210,138,.16); color: var(--green); }
  .pill.suspicious { background: rgba(243,201,105,.18); color: var(--yellow); }
  .pill.injected   { background: rgba(255,107,107,.20); color: var(--red); }
  .pill.failed     { background: rgba(90,96,110,.30); color: var(--muted); }
  .pill.unknown    { background: rgba(90,96,110,.30); color: var(--muted); }
  .err { color: var(--red); font-family: ui-monospace, SFMono-Regular,
         Menlo, monospace; font-size: 12px; word-break: break-all; }
  details { margin-top: 6px; }
  details summary { cursor: pointer; color: var(--muted); }
  details pre {
    background: #0a0a0c; border: 1px solid var(--border);
    padding: 10px 12px; border-radius: 6px;
    white-space: pre-wrap; word-wrap: break-word;
    font: 12px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace;
    color: #d6d6d6; max-height: 380px; overflow: auto;
  }
  .grid {
    display: grid; gap: 14px;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  }
  .stat .v { font-size: 22px; font-weight: 600; }
  .stat .l { color: var(--muted); font-size: 11px; text-transform: uppercase;
             letter-spacing: .08em; margin-top: 4px; }
  .endpoint-head {
    display: flex; align-items: baseline; gap: 12px;
    flex-wrap: wrap; margin-bottom: 6px;
  }
  .endpoint-head .url { color: var(--muted); font-family: ui-monospace,
                         SFMono-Regular, Menlo, monospace; font-size: 12px; }
  .bar-wrap { background: #1d2027; border-radius: 4px; height: 8px;
              overflow: hidden; margin-top: 4px; }
  .bar { height: 100%; }
  .bar.green { background: var(--green); }
  .bar.yellow { background: var(--yellow); }
  .bar.red { background: var(--red); }
  .legend { color: var(--muted); font-size: 12px; }
  .small { color: var(--muted); font-size: 12px; }
  .nav { display: flex; gap: 16px; margin: 12px 0 22px; flex-wrap: wrap; }
  .nav a { color: var(--accent); text-decoration: none; font-size: 13px; }
  .nav a:hover { text-decoration: underline; }
  .ok { color: var(--green); }
  .bad { color: var(--red); }
  .warn { color: var(--yellow); }
  .footnote { color: var(--muted); font-size: 11px; margin-top: 28px; }
  .col-flex { display: flex; gap: 18px; flex-wrap: wrap; }
  .col-flex > .panel { flex: 1; min-width: 320px; }
</style>
</head>
<body>
<h1>{{TITLE}}</h1>
<div class="meta" id="meta"></div>

<div class="nav" id="nav"></div>

<div id="overview"></div>
<div id="comparison"></div>
<div id="endpoints"></div>

<div class="footnote">
  Generated by <code>perf-bench.py</code> (zero-dep) &middot;
  api-relay-audit perf extension &middot; data is embedded inline in this file.
</div>

<script>
window.__BENCH_DATA__ = {{DATA}};
</script>

<script>
(function () {
  const data = window.__BENCH_DATA__;
  const $ = (id) => document.getElementById(id);

  const fmt = {
    secs(v) {
      if (v == null) return "—";
      if (v < 1) return (v * 1000).toFixed(0) + " ms";
      return v.toFixed(2) + " s";
    },
    pct(v) { return v == null ? "—" : (v * 100).toFixed(1) + "%"; },
    int(v) { return v == null ? "—" : Number(v).toLocaleString(); },
    ratio(num, den) {
      if (!den) return "—";
      return ((num / den) * 100).toFixed(0) + "%";
    },
    text(v, max) {
      max = max || 220;
      if (!v) return "";
      v = String(v);
      return v.length > max ? v.slice(0, max) + "…" : v;
    },
  };

  function pill(verdict) {
    const v = verdict || "unknown";
    return `<span class="pill ${v}">${v.toUpperCase()}</span>`;
  }

  // ----- meta block -------------------------------------------------------
  const meta = $("meta");
  const t = data.test || {};
  meta.innerHTML = [
    `Generated: <b>${data.generated_at || "?"}</b>`,
    `Total elapsed: <b>${fmt.secs(data.elapsed_seconds)}</b>`,
    `Prompt: <code>${(t.prompts && t.prompts[0]) || t.prompt || ""}</code>`,
    `Rounds: <b>${t.rounds}</b>`,
    `Concurrency: <b>${t.concurrency}</b>`,
    `Timeout: <b>${t.timeout}s</b>`,
    `Max tokens: <b>${t.max_tokens}</b>`,
  ].map(s => `<span style="margin-right:18px">${s}</span>`).join("");

  // ----- nav --------------------------------------------------------------
  const nav = $("nav");
  nav.innerHTML = [
    `<a href="#overview-section">Overview</a>`,
    `<a href="#comparison-section">Comparison</a>`,
    ...data.endpoints.map((ep, i) =>
      `<a href="#endpoint-${i}">${ep.name}</a>`)
  ].join("");

  // ----- overview ---------------------------------------------------------
  const allEndpoints = data.endpoints || [];
  let totalRounds = 0, okRounds = 0, errRounds = 0, modelCount = 0;
  for (const ep of allEndpoints) {
    for (const r of ep.results) {
      modelCount += 1;
      const m = r.metrics || {};
      const succ = m.successful_rounds || 0;
      const fail = m.failed_rounds || 0;
      okRounds += succ;
      errRounds += fail;
      totalRounds += succ + fail;
    }
  }
  $("overview").innerHTML = `
    <h2 id="overview-section">Overview</h2>
    <div class="panel grid">
      <div class="stat"><div class="v">${allEndpoints.length}</div>
        <div class="l">Endpoints tested</div></div>
      <div class="stat"><div class="v">${modelCount}</div>
        <div class="l">Endpoint x Model bench rows</div></div>
      <div class="stat"><div class="v">${totalRounds}</div>
        <div class="l">Total rounds</div></div>
      <div class="stat"><div class="v">${fmt.ratio(okRounds, totalRounds)}</div>
        <div class="l">Overall success rate</div></div>
      <div class="stat"><div class="v ${errRounds ? "bad" : "ok"}">${errRounds}</div>
        <div class="l">Failed rounds</div></div>
    </div>`;

  // ----- comparison table ------------------------------------------------
  const compRows = [];
  for (const ep of allEndpoints) {
    for (const r of ep.results) {
      const m = r.metrics || {};
      const ttft = m.ttft_seconds || {};
      const tot = m.total_seconds || {};
      const purity = r.purity || {};
      compRows.push({
        endpoint: ep.name, model: r.model,
        succ: m.successful_rounds || 0,
        fail: m.failed_rounds || 0,
        rate: m.success_rate,
        ttftAvg: ttft.avg, ttftP95: ttft.p95, ttftP99: ttft.p99,
        totAvg: tot.avg, totP95: tot.p95, totP99: tot.p99,
        verdict: purity.verdict || "unknown",
      });
    }
  }
  const compTable = compRows.map(r => `
    <tr>
      <td>${r.endpoint}</td>
      <td><code>${r.model}</code></td>
      <td class="num">${r.succ}/${r.succ + r.fail}</td>
      <td class="num">${fmt.secs(r.ttftAvg)}</td>
      <td class="num">${fmt.secs(r.ttftP95)}</td>
      <td class="num">${fmt.secs(r.ttftP99)}</td>
      <td class="num">${fmt.secs(r.totAvg)}</td>
      <td class="num">${fmt.secs(r.totP95)}</td>
      <td class="num">${fmt.secs(r.totP99)}</td>
      <td>${pill(r.verdict)}</td>
    </tr>`).join("");
  $("comparison").innerHTML = `
    <h2 id="comparison-section">Side-by-side comparison</h2>
    <div class="panel">
      <table>
        <thead><tr>
          <th>Endpoint</th><th>Model</th><th>OK / Total</th>
          <th>TTFT avg</th><th>TTFT p95</th><th>TTFT p99</th>
          <th>Total avg</th><th>Total p95</th><th>Total p99</th>
          <th>Purity</th>
        </tr></thead>
        <tbody>${compTable || `<tr><td colspan="10" class="small">No data</td></tr>`}</tbody>
      </table>
      <div class="legend" style="margin-top:10px">
        <b>TTFT</b> = time to first token (streaming).
        <b>Total</b> = total wall-clock time of the streamed response.
        <b>Purity</b>:
        ${pill("clean")} no injection markers detected,
        ${pill("suspicious")} unusual patterns,
        ${pill("injected")} prompt-injection / identity leak detected,
        ${pill("failed")} every round errored.
      </div>
    </div>`;

  // ----- per endpoint -----------------------------------------------------
  const epHtml = allEndpoints.map((ep, i) => {
    const blocks = ep.results.map((r, j) => modelBlock(ep, r, i, j)).join("");
    const listed = (ep.models_listed || []).slice(0, 80);
    const listedStr = listed.length
      ? listed.map(x => `<code>${x}</code>`).join(", ")
      : `<span class="small">/v1/models unavailable: ${ep.models_listed_error || "no data"}</span>`;
    return `
      <h2 id="endpoint-${i}">Endpoint: ${ep.name}</h2>
      <div class="panel">
        <div class="endpoint-head">
          <div><b>${ep.name}</b></div>
          <div class="url">${ep.base_url}</div>
          <div class="small">format: ${ep.format}${ep.vendor ? ` &middot; vendor: <b>${ep.vendor}</b>` : ""}</div>
        </div>
        <div class="small" style="margin-top:6px">
          <b>Models advertised by /v1/models</b>: ${listedStr}
          ${listed.length === 80 ? "… (truncated)" : ""}
        </div>
      </div>
      ${blocks}
    `;
  }).join("");
  $("endpoints").innerHTML = epHtml;

  function modelBlock(ep, r, epIdx, modelIdx) {
    const m = r.metrics || {};
    const purity = r.purity || {};
    const ttft = m.ttft_seconds || {};
    const tot = m.total_seconds || {};
    const out = m.output_chars || {};

    const errs = (r.errors || []).filter(Boolean);
    const errPanel = errs.length
      ? `<div class="panel" style="margin-top:8px">
           <div class="warn"><b>${errs.length} failed rounds</b></div>
           <ul>${errs.slice(0, 8).map(e => `<li class="err">${escapeHtml(e)}</li>`).join("")}</ul>
           ${errs.length > 8 ? `<div class="small">… and ${errs.length - 8} more</div>` : ""}
         </div>`
      : "";

    const issueRows = Object.entries(purity.issue_counts || {})
      .map(([k, v]) => `<li><b>${k}</b>: ${v}</li>`).join("")
      || `<li class="small">no purity issues</li>`;

    const idRows = Object.entries(purity.identities_seen || {})
      .map(([k, v]) => `<li><b>${k}</b> seen ${v}x</li>`).join("");

    const roundRows = (r.rounds || []).map(rd => `
      <tr>
        <td class="num">${rd.round}</td>
        <td>${rd.ok ? `<span class="ok">OK</span>` : `<span class="bad">ERR</span>`}</td>
        <td class="num">${fmt.secs(rd.ttft_seconds)}</td>
        <td class="num">${fmt.secs(rd.total_seconds)}</td>
        <td class="num">${fmt.int(rd.output_chars)}</td>
        <td class="num">${rd.chunk_count}</td>
        <td>${rd.finish_reason || ""}</td>
        <td>${(rd.issues || []).map(i => `<span class="pill suspicious">${i}</span>`).join(" ")}</td>
        <td>
          ${rd.error ? `<span class="err">${escapeHtml(fmt.text(rd.error, 200))}</span>` : ""}
          ${rd.text_preview ? `<details><summary>preview</summary><pre>${escapeHtml(rd.text_preview)}</pre></details>` : ""}
        </td>
      </tr>`).join("");

    return `
      <div class="panel" id="endpoint-${epIdx}-model-${modelIdx}">
        <h3><code>${r.model}</code> ${pill(purity.verdict)}
          <span class="small">${purity.verdict_reason || ""}</span></h3>

        <div class="grid">
          <div class="stat"><div class="v">${m.successful_rounds || 0}/${(m.successful_rounds||0)+(m.failed_rounds||0)}</div>
            <div class="l">Successful rounds</div></div>
          <div class="stat"><div class="v">${fmt.secs(ttft.avg)}</div>
            <div class="l">TTFT avg</div></div>
          <div class="stat"><div class="v">${fmt.secs(ttft.p95)}</div>
            <div class="l">TTFT p95</div></div>
          <div class="stat"><div class="v">${fmt.secs(ttft.p99)}</div>
            <div class="l">TTFT p99</div></div>
          <div class="stat"><div class="v">${fmt.secs(tot.avg)}</div>
            <div class="l">Total avg</div></div>
          <div class="stat"><div class="v">${fmt.secs(tot.p95)}</div>
            <div class="l">Total p95</div></div>
          <div class="stat"><div class="v">${fmt.secs(tot.p99)}</div>
            <div class="l">Total p99</div></div>
          <div class="stat"><div class="v">${fmt.int(out.avg && Math.round(out.avg))}</div>
            <div class="l">Avg output chars</div></div>
        </div>

        <div class="col-flex" style="margin-top:14px">
          <div class="panel" style="background:#10131a">
            <div class="small">Latency distribution (s)</div>
            <table>
              <thead><tr><th></th><th>min</th><th>avg</th><th>p50</th>
                <th>p90</th><th>p95</th><th>p99</th><th>max</th><th>stdev</th></tr></thead>
              <tbody>
                <tr><td>TTFT</td>
                  <td class="num">${fmt.secs(ttft.min)}</td>
                  <td class="num">${fmt.secs(ttft.avg)}</td>
                  <td class="num">${fmt.secs(ttft.p50)}</td>
                  <td class="num">${fmt.secs(ttft.p90)}</td>
                  <td class="num">${fmt.secs(ttft.p95)}</td>
                  <td class="num">${fmt.secs(ttft.p99)}</td>
                  <td class="num">${fmt.secs(ttft.max)}</td>
                  <td class="num">${fmt.secs(ttft.stdev)}</td></tr>
                <tr><td>Total</td>
                  <td class="num">${fmt.secs(tot.min)}</td>
                  <td class="num">${fmt.secs(tot.avg)}</td>
                  <td class="num">${fmt.secs(tot.p50)}</td>
                  <td class="num">${fmt.secs(tot.p90)}</td>
                  <td class="num">${fmt.secs(tot.p95)}</td>
                  <td class="num">${fmt.secs(tot.p99)}</td>
                  <td class="num">${fmt.secs(tot.max)}</td>
                  <td class="num">${fmt.secs(tot.stdev)}</td></tr>
              </tbody>
            </table>
          </div>
          <div class="panel" style="background:#10131a">
            <div class="small">Purity</div>
            <p>Verdict: ${pill(purity.verdict)} <span class="small">${purity.verdict_reason || ""}</span></p>
            <p>Clean rounds: <b>${purity.rounds_clean}</b> / ${purity.rounds_total}
               (ok: ${purity.rounds_ok}, refusals: ${purity.refusal_count},
               empty: ${purity.empty_count}, language-mismatch: ${purity.language_mismatch_count})</p>
            <ul>${issueRows}</ul>
            ${idRows ? `<p class="warn">Identity leakage:</p><ul>${idRows}</ul>` : ""}
          </div>
        </div>

        ${errPanel}

        <details style="margin-top:10px">
          <summary>Per-round detail (${(r.rounds || []).length})</summary>
          <table>
            <thead><tr>
              <th>#</th><th>status</th><th>ttft</th><th>total</th>
              <th>chars</th><th>chunks</th><th>finish</th>
              <th>issues</th><th>response / error</th>
            </tr></thead>
            <tbody>${roundRows}</tbody>
          </table>
        </details>
      </div>`;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;",
      "\"": "&quot;", "'": "&#39;"
    }[c]));
  }
})();
</script>
</body>
</html>
"""


# ============================================================================
# Section 7 — CLI entry point
# ============================================================================

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Performance + purity benchmark for AI API relays. "
                    "Zero dependencies: stdlib + curl only.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Shortest form (positional): "
            "perf-bench.py <url> <key> <vendor>\n"
            f"Vendors: {', '.join(sorted(VENDOR_MODELS))}"
        ),
    )

    p.add_argument("positional", nargs="*",
                   help="Optional shorthand: <url> <key> <vendor>")

    g_cfg = p.add_argument_group("config (mutually exclusive with positional)")
    g_cfg.add_argument("--config", help="JSON config path")
    g_cfg.add_argument("--url", help="Single endpoint base URL")
    g_cfg.add_argument("--key", help="Single endpoint API key")
    g_cfg.add_argument("--vendor", choices=sorted(VENDOR_MODELS),
                       help="Vendor preset (selects representative models)")
    g_cfg.add_argument("--name", default=None,
                       help="Endpoint label for reports (default: hostname[-vendor])")
    g_cfg.add_argument("--format", choices=["openai", "anthropic"],
                       default="openai",
                       help="Wire format for streaming (default: openai)")

    g_test = p.add_argument_group("test parameters")
    g_test.add_argument("--prompt", default=DEFAULT_PROMPT,
                        help=f"Default test prompt (default: {DEFAULT_PROMPT!r})")
    g_test.add_argument("--prompts-file",
                        help="File with one prompt per line; round i uses line i mod N")
    g_test.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS,
                        help=f"Rounds per (endpoint, model) (default: {DEFAULT_ROUNDS})")
    g_test.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                        help=f"Parallel rounds (default: {DEFAULT_CONCURRENCY})")
    g_test.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help=f"Per-request timeout in seconds (default: {DEFAULT_TIMEOUT})")
    g_test.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
                        help=f"max_tokens per request (default: {DEFAULT_MAX_TOKENS})")
    g_test.add_argument("--temperature", type=float, default=None,
                        help="Temperature (default: omitted from request body)")
    g_test.add_argument("--model", action="append", default=[],
                        help="Explicit model id (repeatable). "
                             "Overrides --vendor / DEFAULT_MODELS.")
    g_test.add_argument("--system", default=None, help="Optional system prompt")

    g_out = p.add_argument_group("output")
    g_out.add_argument("--output", default="perf-report.html",
                       help="HTML report path (default: perf-report.html)")
    g_out.add_argument("--json", default=None,
                       help="Optional JSON output path. "
                            "Defaults to <output basename>.json next to HTML.")
    g_out.add_argument("--title", default="", help="Override report title")
    g_out.add_argument("--quiet", action="store_true", help="Less stderr noise")

    return p.parse_args()


def _absorb_positional(args: argparse.Namespace) -> None:
    pos = args.positional or []
    if not pos:
        return
    if args.config:
        sys.exit("error: positional <url> <key> <vendor> is mutually "
                 "exclusive with --config")
    if len(pos) < 2:
        sys.exit("error: positional form needs at least <url> <key>")
    if len(pos) > 3:
        sys.exit("error: positional form is <url> <key> [vendor], extras given")
    url, key, *rest = pos
    if args.url and args.url != url:
        sys.exit("error: positional URL conflicts with --url")
    if args.key and args.key != key:
        sys.exit("error: positional KEY conflicts with --key")
    args.url = args.url or url
    args.key = args.key or key
    if rest:
        v = rest[0].strip().lower()
        if v not in VENDOR_MODELS:
            sys.exit(f"error: unknown vendor {rest[0]!r}; "
                     f"choose from {sorted(VENDOR_MODELS)}")
        if args.vendor and args.vendor != v:
            sys.exit("error: positional vendor conflicts with --vendor")
        args.vendor = v


def main() -> int:
    args = parse_args()
    _absorb_positional(args)

    if args.config and (args.url or args.key):
        sys.exit("error: --config is mutually exclusive with --url/--key")
    if not args.config and not (args.url and args.key):
        sys.exit("error: provide either --config or <url> <key> [vendor] "
                 "(or --url and --key)")

    if args.config:
        cfg = load_config(args.config)
        if args.rounds != DEFAULT_ROUNDS:
            cfg["test"]["rounds"] = args.rounds
        if args.timeout != DEFAULT_TIMEOUT:
            cfg["test"]["timeout"] = args.timeout
        if args.prompt != DEFAULT_PROMPT and not cfg["test"].get("prompts"):
            cfg["test"]["prompt"] = args.prompt
        if args.concurrency != DEFAULT_CONCURRENCY:
            cfg["test"]["concurrency"] = args.concurrency
        if args.max_tokens != DEFAULT_MAX_TOKENS:
            cfg["test"]["max_tokens"] = args.max_tokens
    else:
        if args.model:
            models = list(args.model)
            default_models = list(args.model)
        elif args.vendor:
            models = vendor_models(args.vendor)
            default_models = models
        else:
            models = None
            default_models = list(DEFAULT_MODELS)

        ep_name = args.name or _short_host(args.url)
        if args.vendor and not args.name:
            ep_name = f"{ep_name}-{args.vendor}"

        cfg = {
            "test": {
                "prompt": args.prompt,
                "rounds": args.rounds,
                "timeout": args.timeout,
                "max_tokens": args.max_tokens,
                "temperature": args.temperature,
                "concurrency": args.concurrency,
                "format": args.format,
                "system": args.system,
                "prompts": None,
            },
            "default_models": default_models,
            "endpoints": [{
                "name": ep_name,
                "base_url": args.url,
                "api_key": args.key,
                "models": models,
                "format": args.format,
                "vendor": args.vendor,
            }],
        }

    if args.prompts_file:
        with open(args.prompts_file, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        if lines:
            cfg["test"]["prompts"] = lines

    log = (lambda _msg: None) if args.quiet else \
          (lambda msg: print(msg, file=sys.stderr))

    result = run_benchmark(cfg, log_fn=log)

    out_html = args.output
    out_json = args.json or os.path.splitext(out_html)[0] + ".json"

    write_json_report(result, out_json)
    write_html_report(result, out_html, title=args.title)

    if not args.quiet:
        print(f"\nWrote JSON: {out_json}", file=sys.stderr)
        print(f"Wrote HTML: {out_html}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

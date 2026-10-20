---
name: moli-jev
description: "Use when a web task needs real clicking, form filling, option selection, or multi-step navigation: drive Moli's CDP browser with the vendored jev goal loop, with fallbacks for unsupported CDP surfaces."
version: 1.1.0
author: yujipeng
license: MIT
metadata:
  hermes:
    tags:
      - browser
      - automation
      - moli
      - jev
      - cdp
    related_skills:
      - moli-webfetch
      - moli-websearch
      - moli-cdp-server
required_environment_variables:
  - TYPESAFE_API_KEY
  - TEXT_MODEL_API_KEY
---

# Drive Moli with jev

Use this skill when a web task needs real interaction: clicking, filling forms,
selecting options, or multi-step navigation. `moli-webfetch` only retrieves a
page; jev supplies the goal-driven decision loop on top of Moli's CDP endpoint.

## Layout

jev is vendored under this skill, so no separate checkout is required:

```
moli-jev/
├── SKILL.md
├── .gitignore
└── jev-ultrafast/              # browser-use/jev-ultrafast @ 1231850 (2026-09-18), MIT
    ├── .env                    # local credentials only, git-ignored
    ├── .env.example
    ├── examples/run.py
    ├── jev_ultrafast/
    └── pyproject.toml
```

Resolve both paths once per session. `SKILL_DIR` is the directory containing
this file; `JEV_DIR` defaults to its `jev-ultrafast/` subdirectory:

```bash
SKILL_DIR="${SKILL_DIR:?directory containing this SKILL.md}"
JEV_DIR="${JEV_DIR:-$SKILL_DIR/jev-ultrafast}"
```

Set `JEV_DIR` explicitly only to test against a different jev build.

## When not to use it

- Known URL, keyword search, or static reading: use `moli-webfetch` or
  `moli-websearch` first. They need no model calls and are faster.
- Screenshots, PDFs, full-page captures: use `moli fetch --layout`.
- Sensitive or authenticated pages: jev sends page structure and element labels
  to the TypeSafe cloud. Do not use it for data that must stay local.

## Prerequisites

- `moli` on `PATH` (`moli --version`). If missing, install the latest prebuilt
  release:

  ```bash
  curl --proto '=https' --tlsv1.2 -fsSL \
    https://github.com/lexmount/moli/releases/latest/download/moli-installer.sh | sh
  ```

  The fallback location is `~/.local/bin/moli`.
- Python 3.12+ and `uv`. jev is not published on PyPI; always run it from the
  vendored directory, never `pip install jev-ultrafast`.
- One-time setup of the vendored jev:

  ```bash
  cd "$JEV_DIR"
  uv sync
  [ -f .env ] || cp .env.example .env
  ```

  Then fill `TYPESAFE_API_KEY` and `TEXT_MODEL_API_KEY` in `.env`. `uv sync`
  creates `$JEV_DIR/.venv`; both `.env` and `.venv` are git-ignored.
- `.env` holds real credentials. Never commit it, print it, or paste it into a
  report or shell log.
- `--layout` on the Moli server: jev needs real geometry, coordinate input and
  screenshots.

## Workflow

1. Start Moli and keep its PID:

   ```bash
   moli serve --layout --port 9333 -t 300 &
   MOLI_PID=$!
   ```

   `-t` is the server timeout in seconds. Raise it for long agent runs.

2. Verify discovery before connecting:

   ```bash
   curl -s http://127.0.0.1:9333/json/version
   ```

   The response must contain `webSocketDebuggerUrl`.

3. Point Browser Harness at Moli. Use a dedicated `BU_NAME` so this daemon does
   not collide with a Chrome-backed `default` daemon:

   ```bash
   export BU_NAME=moli-jev
   export BU_CDP_URL=http://127.0.0.1:9333
   ```

   Browser Harness resolves the WebSocket through `/json/version`; do not
   hard-code a `/devtools/...` path. `BU_CDP_WS` also works if the WebSocket URL
   is already known.

4. Run jev, either as the full agent or as a deterministic library call.

   Full agent (calls TypeSafe and the text model):

   ```bash
   cd "$JEV_DIR"
   uv run --env-file .env python examples/run.py \
     --url "https://www.google.com/travel/flights?hl=en" \
     --goal "Find one-way flights from Zurich to London on 2026-09-20 for one adult."
   ```

   Deterministic library call (observe and act without model calls):

   ```python
   import os
   os.environ["BU_NAME"] = "moli-jev"
   os.environ["BU_CDP_URL"] = "http://127.0.0.1:9333"

   from jev_ultrafast.browser import Browser

   browser = Browser("https://www.bing.com/?setlang=en")
   page = browser.observe(screenshot=False)
   fill = next(a for a in page["actions"] if a["kind"] == "fill")
   browser.act(fill, page, text="moli browser")
   ```

   Run the script from `$JEV_DIR` so the vendored package and its virtualenv
   resolve:

   ```bash
   cd "$JEV_DIR"
   uv run --no-sync --env-file .env python /path/to/script.py
   ```

5. Handle the known gaps below, then close cleanly.

## Verified compatibility

Tested against Moli 1.1.18 (`moli serve --layout`) with the vendored jev
(`1231850`) and its Browser Harness:

| Layer | Result |
| --- | --- |
| `Browser.getVersion`, `Target.createTarget`, `Target.attachToTarget` | pass |
| `Emulation.setDeviceMetricsOverride`, `setFocusEmulationEnabled` | pass |
| `Page.navigate`, `Runtime.evaluate`, `Page.captureScreenshot` | pass |
| `Input.dispatchMouseEvent`, `Input.insertText`, `Input.dispatchKeyEvent` | pass |
| jev `observe()` action space | pass |
| Click navigation on a real page | pass |
| Fill a real search box | pass |

## Known gaps and workarounds

- **Input wrapped in `<label>`**: Moli's `document.elementFromPoint` can return
  the `LABEL` instead of the `INPUT`, so jev's occlusion check raises
  `StalePage: Target changed or is covered`. Prefer a target that is not wrapped
  by a label; otherwise fill it through raw CDP (`Runtime.evaluate` to focus +
  `Input.insertText`). A local patch to jev's check is possible but is lost on
  the next vendored update.
- **No Enter key in jev's action space**: after `fill`, submit with raw CDP:

  ```python
  browser.call("Input.dispatchKeyEvent", type="keyDown", key="Enter", code="Enter", windowsVirtualKeyCode=13)
  browser.call("Input.dispatchKeyEvent", type="keyUp", key="Enter", code="Enter", windowsVirtualKeyCode=13)
  ```

  This only works when the page submits on Enter; otherwise click a search
  button that actually appears in the action space.
- **Moli's CDP is a subset of Chrome's**: if a method returns an explicit
  unsupported error, treat it as a capability boundary. Shadow DOM, iframes,
  uploads, native selects and nested scrolling are only partially covered by
  jev as well.
- **Latency and cost**: decisions still call TypeSafe plus the text model. Moli
  reduces browser weight and CDP round trips, not model cost.

## Cleanup

```bash
kill "$MOLI_PID"
```

Stop the Browser Harness daemon for `BU_NAME=moli-jev` as well. If other harness
sessions may be running, find its PID first rather than killing every
`browser_harness.daemon` process.

## Fallback

If jev cannot complete the task (no suitable action, blocked model, or an
unsupported CDP method), fall back to `moli-webfetch` for retrieval and report
the interaction that failed. Do not invent page state.

---
name: multica-server-setup
description: Use when setting up or updating AI coding-agent runtimes for Multica on Linux servers (or a macOS dev machine): installing dsh with its web/tui/multica profiles, building and wiring the @multica-ai/dsh-runtime bridge plugin, installing reasonix, codex, and Claude Code when missing, configuring DeepSeek API keys, verifying with `dsh --profile multica --probe`, creating agents in Multica Web, and deploying scheduled self-updates via crontab / systemd / launchd. Everything installs into the current user's home directory only — never into root's.
version: 1.0.0
author: yujipeng
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [multica, dsh, deepseek, agent-runtime, linux, devops, automation, self-update]
    related_skills: [web-access]
required_environment_variables:
  - name: DEEPSEEK_API_KEY
    prompt: DeepSeek API key
    help: Model-inference credential for dsh. Multica does not hold it. Never paste it into chat or logs.
    required_for: Running the dsh agent runtime (model inference)
  - name: MULTICA_DSH_PATH
    prompt: Absolute path to dsh binary
    help: Optional but recommended — the daemon's PATH may differ from the terminal's. Example /home/user/.local/bin/dsh
    required_for: Ensuring the daemon finds the right dsh
  - name: MULTICA_DSH_MODEL
    prompt: Default model id (provider/model)
    help: Optional. Must be a full id from `dsh --profile multica --list-models`, e.g. deepseek-official/deepseek-chat
    required_for: Selecting a default model for Multica agents
---

# Skill: Multica Server-Side Agent Setup & Scheduled Updates

## Purpose

安装并维护 Multica 的服务器端 agent 运行时（Linux 服务器为主，macOS 开发机可选），并把定时自动更新跑起来。覆盖四类工作：

1. **初始工具安装检查**：`reasonix`、`codex`、`claude`（Claude Code）缺失时自动安装（当前用户目录，禁止 root / sudo）。
2. **dsh 三 profile 安装**：默认 `web` profile + `tui` profile（`@huiliyi37/dsh-tianshu-tui`）+ `multica` profile（本地构建 `@multica-ai/dsh-runtime` 桥插件）。
3. **Multica 运行时接线**：DeepSeek API Key、`--probe` 验证、daemon 启动、Multica Web 创建智能体。
4. **定时更新**：每周自动更新 dsh / multica（服务器精简版），或开发机全套工具（完整版），crontab / systemd / launchd 任选。

## 硬性规则（必须遵守）

- **所有安装一律在当前用户目录**：nvm（`~/.nvm`，npm prefix 天然用户可写）或 `npm config set prefix ~/.local`（非 nvm，写入 `~/.npmrc`；bin 即 `~/.local/bin`，与 multica 用户版同目录），multica 用户版 `~/.local/bin/multica`。**全程禁止 sudo / root 安装**；脚本开头校验 `EUID != 0`，且自动把系统目录 prefix 修复为用户级 `~/.local`。
- **dsh 版本无需固定**：装 `@deepseek-ai/dsh` latest（与桥插件兼容性以 `--probe` 验证为准）；更新脚本更新后必须重新验证 `dsh --profile multica --probe`，失败自动回退更新前版本。
- **profile 隔离**：`multica` profile 只允许 `@deepseek-ai/dsh-base` + `@multica-ai/dsh-runtime` 两个 bundle；TUI 插件一律装 `tui` profile，禁止混入 multica profile（否则 `--probe` 被参数解析器拦截）。
- **API key 只经环境变量 / 凭据文件传入**，禁止出现在日志、crontab 明文、systemd unit 之外的可共享文件或提交中。
- 国内网络（阿里云 ECS 等）：脚本无代理时自动把 npm/pnpm 切到 npmmirror 镜像（`npm_config_registry`，等价 `--registry=https://registry.npmmirror.com/`）；nvm 下载镜像见 `docs/install-linux.md`。

## 使用流程

### 1. 准备（只读检查）

```bash
ssh user@server
id -u                                   # 必须非 0；脚本也会自检
node -v && npm -v                       # Node 需 22.19+ 或 24+
```

### 2. 一键安装（推荐）

```bash
bash skills/multica-server-setup/scripts/setup-agent.sh
```

脚本幂等，可重复执行。安装内容（全部用户目录）：

- Node（nvm 缺失时安装）→ npm prefix 用户可写校验
- **reasonix / codex / claude code 缺失时安装**（`npm install -g reasonix`、`npm install -g @openai/codex`、`npm install -g @anthropic-ai/claude-code`）
- pnpm → dsh（latest）→ multica 用户版 → 桥插件本地构建装入 multica profile → `tui` profile 装 `@huiliyi37/dsh-tianshu-tui`
- `DEEPSEEK_API_KEY` 提示配置 → `--probe` 验证 → daemon start

需要分步/手工执行时，按 `docs/install-linux.md`（含阿里云特化）与 `docs/runtime-and-web.md` 操作。

### 3. 验证

```bash
dsh --version                              # 输出当前版本即可（无需固定）
dsh --profile multica --probe              # 必须成功（protocol version 1）
dsh --profile multica --list-models        # 输出 provider/model 完整 id
multica daemon status                      # 运行时在线；离线则 daemon restart
```

### 4. Multica Web 创建智能体

按 `docs/runtime-and-web.md` 第 9 节：运行时页确认 **DeepSeek Harness 在线** → 创建智能体并选择该运行时 → 选完整模型 id（如 `deepseek-official/deepseek-chat`）。

### 5. 配置定时更新

```bash
# 服务器：只更新 dsh + multica（更新后自动 --probe 验证）
bash skills/multica-server-setup/scripts/agent-weekly-update.sh
# crontab 每周日 03:00 执行（模板：templates/weekly-update.cron）
crontab -e   # 或按模板内容安装

# 开发机完整版：reasonix/codex/claude/dsh/multica 全更新
bash skills/multica-server-setup/scripts/agent-weekly-update-full.sh

# systemd 常驻（可选）：templates/multica-daemon.service
# macOS 开发机 dsh web 常驻（可选）：templates/dsh-web-launchd.plist
```

### 6. 故障排查

常见问题（`--probe` 报 unknown option、EACCES、Node 版本、运行时不在线等）的处理见 `docs/runtime-and-web.md` 故障排查表。

## 文件索引

| 文件 | 作用 |
|---|---|
| `scripts/setup-agent.sh` | 幂等一键安装（用户目录，禁 root） |
| `scripts/agent-weekly-update.sh` | 服务器精简版更新：dsh + multica，更新后 `--probe` 验证 |
| `scripts/agent-weekly-update-full.sh` | 开发机完整版更新：reasonix / codex / claude / dsh / multica |
| `docs/install-linux.md` | 通用 Linux + 阿里云 ECS 安装教程（镜像、EACCES、安全组） |
| `docs/runtime-and-web.md` | 三 profile、验证、daemon、Web 智能体、故障排查 |
| `templates/weekly-update.cron` | crontab 每周日示例 |
| `templates/multica-daemon.service` | systemd 常驻单元（nvm / ~/.local 两种 PATH 写法） |
| `templates/dsh-web-launchd.plist` | macOS 开发机 dsh web 常驻（可选） |

## 安全

- `DEEPSEEK_API_KEY` 通过环境变量传入；写入 `~/.dsh/.credentials.yaml` 时确保文件权限 `600`。
- systemd unit / launchd plist 中含 key 时，文件权限收紧为仅属主可读；crontab 内容避免明文 key。
- 更新脚本日志写入 `~/.local/state/weekly-update.log`，不含 key。

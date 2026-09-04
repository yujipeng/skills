# 运行时、Web 智能体与故障排查

> 承接 `install-linux.md`。本文档覆盖：dsh 三 profile 说明、运行时验证标准、daemon 启动硬性规则、Multica Web 创建智能体、常用 daemon 配置、故障排查表。

---

## 0. 初始工具安装检查与禁止 root 清单

本 skill 的**所有安装都在当前用户目录**（nvm bin / `~/.local/bin`），**全程禁止 sudo / root**。每次在服务器上操作前先过一遍清单：

- [ ] `id -u` 输出非 0（root 直接退出，改用普通用户执行）
- [ ] reasonix / codex / claude code 缺失时 `npm install -g`（用户目录 npm 全局）：
  ```bash
  command -v reasonix || npm install -g reasonix
  command -v codex    || npm install -g @openai/codex
  command -v claude   || npm install -g @anthropic-ai/claude-code
  ```
- [ ] PATH 前置：nvm bin 或 `~/.local/bin`（`command -v` 必须命中用户可写副本）
- [ ] 不用 sudo 执行任何 npm / pnpm / dsh / multica 命令（sudo 走 secure_path，找不到用户目录命令）

完整安装步骤见 `install-linux.md`（第 0 节硬性规则、第 5 步 reasonix/claude code）。

## 1. dsh 三 profile（web / tui / multica）

| Profile | 用途 | 安装命令 | 调用方式 |
|---|---|---|---|
| `web` | 内置默认，Web UI | 无需安装（内置 `@deepseek-ai/dsh-base`） | `dsh web` |
| `tui` | 终端 UI | `dsh plugin --profile tui add @huiliyi37/dsh-tianshu-tui` | `dsh --profile tui` |
| `multica` | Multica 桥（headless 一次性会话） | `dsh plugin --profile multica add <本地 checkout 路径>` | `dsh --profile multica --probe` |

三个 profile 相互独立、互不干扰。**禁止**把 TUI / find-plugin 等装进 `multica` profile（详见故障排查 1）。

multica profile 的期望内容（`~/.dsh/profiles/multica/package.json`）：

```json
{
  "name": "dsh-profile-multica",
  "private": true,
  "dependencies": {
    "@multica-ai/dsh-runtime": "link:/home/<你的用户>/dsh-multica-runtime"
  },
  "dsh": {
    "profile": {
      "bundles": [
        "@deepseek-ai/dsh-base",
        "@multica-ai/dsh-runtime"
      ]
    }
  }
}
```

> 桥插件不在 npm 发布（`private: true`），必须源码构建后以本地路径装入；`dist/` 目录必须存在（`index.js` / `protocol.js` / `environment.js` / `task-env.js`）。

## 2. 运行时验证标准

```bash
dsh --version                      # 输出当前版本即可（无需固定，兼容性以 --probe 为准）
dsh --profile multica --probe      # 退出码 0、输出 protocol version 1（诊断走 stderr）
dsh --profile multica --list-models  # provider/model 完整 id，如 deepseek-official/deepseek-chat
multica daemon status              # 运行时在线；心跳约 15 秒
```

- 模型 id 必须用完整形式（`provider/model`），Multica Web 选模型时要用。
- `--list-models` 为空：先查 `DEEPSEEK_API_KEY` 是否配置且有效、`--probe` 是否正常。

## 3. daemon 启动硬性规则

1. **启动时必须先检测到至少一款内置支持的 CLI**（dsh 满足）；自定义运行时配置不能作为空白机器唯一条件。
2. 装完新工具后必须 `multica daemon restart` 重新检测。
3. 守护进程与终端 PATH 可能不同，推荐显式指定：

```bash
export MULTICA_DSH_PATH=$(which dsh)
export MULTICA_DSH_MODEL=deepseek-official/deepseek-chat
multica daemon start     # 或 restart
multica daemon status
multica daemon logs -f
```

常用配置（可选）：

```bash
multica config set workspaces_root /data/multica_workspaces   # 任务工作目录根
multica config set max_concurrent_tasks 20                    # 并发上限
multica config show
```

配置优先级：命令行 flag → 环境变量 → `~/.multica/config.json` → 内置默认。

## 4. Multica Web 创建智能体

1. **运行时页面**：打开 Multica →「运行时（Runtimes）」→ 目标服务器下出现 **DeepSeek Harness**，状态**在线**。
2. **创建智能体**：「智能体」→「创建」→ 运行时选择这条 **DeepSeek Harness**。
3. **选模型**：用 `dsh --profile multica --list-models` 的结果选**完整 id**（如 `deepseek-official/deepseek-chat`）；不选则用 dsh 默认。列表为空时先确认运行时在线、API Key 已配置，再刷新。
4. 能力支持：MCP ✓（转译 stdio/streamable-HTTP 客户端）、Skills ✓（注入执行工作区 `.dsh/skills/`，结束后清理，仓库同名 skill 不被覆盖）、会话恢复 ✓、无交互审批（权限遵循 dsh `workspace-write` 默认预设）。

之后：创建 issue → 分配/指派给该智能体 → 在 Multica 查看执行进度与结果。

## 5. 定时更新与常驻

| 场景 | 方式 | 文件 |
|---|---|---|
| 服务器：每周更新 dsh + multica | crontab | `scripts/agent-weekly-update.sh` + `templates/weekly-update.cron` |
| 服务器：daemon 开机自启 | systemd | `templates/multica-daemon.service` |
| macOS 开发机：dsh web 常驻 | launchd | `templates/dsh-web-launchd.plist` |
| 开发机：reasonix/codex/claude/dsh/multica 全更新 | crontab | `scripts/agent-weekly-update-full.sh` |

> 更新脚本在 crontab 环境运行，PATH 必须显式给全（nvm bin 或 `~/.local/bin` 在最前），脚本内已处理。

## 6. 故障排查

### 1. `dsh --profile multica --probe` 报 `error: unknown option '--probe' (Did you mean --preset?)`
multica profile 里装了带命令行解析器的其他插件（如 `deepseek-harness-tui` 定义了 `--preset`）。移除多余插件，只留 runtime：

```bash
dsh plugin --profile multica remove deepseek-harness-tui
dsh plugin --profile multica remove dsh-find-plugin
dsh --profile multica --probe
```

### 2. `dsh --version` 异常或版本与桥插件不兼容
```bash
which -a dsh      # 排查同名命令（apt 的 dsh / 旧残留）
npm ls -g --depth=0 | grep -i dsh
npm install -g @deepseek-ai/dsh    # 重装/升级到最新
export PATH="$(npm prefix -g)/bin:$PATH"
hash -r
```

### 3. `dsh plugin add` 报 `Repository not found` / `git+ssh://`
- 官方文档示例 `github:deepseek-harness/turtle-ui` 是虚构示例，仓库不存在；
- `github:` 前缀走 SSH 协议，公开仓库用 npm 包名或 `git+https://`；
- 桥插件不在 npm，必须本地 checkout 安装。

### 4. `dsh plugin add` 报 allowBuilds 相关错误
Git 托管插件带 `prepare` 构建脚本时 pnpm ≥ 10 会拦截；本地 checkout（桥插件）安装不需要 allowBuilds。

### 5. `--probe` 成功但 Multica 运行时不在线
```bash
multica daemon restart
multica daemon logs -f      # 看版本/路径/认证错误
command -v dsh && dsh --version
export MULTICA_DSH_PATH=$(which dsh)
```

### 6. Node 版本过低导致奇怪行为
桥插件 `engines` 要求 `^22.19.0 || >=24.0.0`，Multica 文档写 20+ 但以 dsh 官方为准。`nvm install 22 && nvm use 22`。

### 7. `--list-models` 为空
确认 `DEEPSEEK_API_KEY` 已配置且有效、`--probe` 正常；模型 id 用完整形式。

### 8. `npm install -g` 报 EACCES
npm 全局目录无写权限。非 nvm 场景执行 `npm config set prefix ~/.local`（见 `install-linux.md` 第 2 步，写入 `~/.npmrc` 永久生效）；nvm 场景不要 sudo。

### 9. 安全组相关疑问
Multica + dsh 全链路出站（WSS 443 / HTTPS 443），无需开入站端口；运行时不在线先查 daemon 是否在跑，不是安全组问题。

### 10. 更新后 `--probe` 失败（新版 dsh 与桥插件不兼容）
dsh 版本**无需固定**；升级到新版后若 `--probe` 失败，回退到此前可用的版本（`agent-weekly-update.sh` 会自动回退更新前版本）：
```bash
npm install -g @deepseek-ai/dsh@<此前可用版本>   # 例：0.1.0-rc.6
dsh --profile multica --probe
multica daemon restart
```

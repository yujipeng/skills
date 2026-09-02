# Linux 安装教程（通用 + 阿里云 ECS 特化）

> 适用：Ubuntu 22.04 / 24.04 / Debian 12 / Alibaba Cloud Linux 3（以 Ubuntu 24.04 为例）
> 版本基准：Node `22.19+ / 24+`、pnpm ≥ 10、`@deepseek-ai/dsh@0.1.0-rc.6`、`@huiliyi37/dsh-tianshu-tui@0.1.2-rc.x`、multica 最新版
> 本文档与 `scripts/setup-agent.sh` 内容一致（脚本是幂等自动化版）；需要手工分步时按本文档执行

---

## 0. 硬性规则（先读）

- **一切安装都在当前用户目录**：nvm（`~/.nvm`）、npm 全局（nvm bin 或 `~/.npm-global/bin`）、multica 用户版（`~/.local/bin/multica`）。
- **全程禁止 `sudo` / root 安装**。理由：root 装的包与用户配置混在一起，后续自动更新全是坑（EACCES / secure_path 找不到命令）。先确认：
  ```bash
  id -u          # 必须非 0
  ```
- 本教程所有命令都以普通用户身份执行。

## 0.1 架构速览

```
┌──────────────────┐   WSS 出站连接    ┌────────────────────────┐
│  Multica 服务器   │ ◄──────────────► │  multica 守护进程        │
│  (multica.ai)    │   (无需入站端口!) │  (用户后台进程)          │
└──────────────────┘                   └───────────┬────────────┘
                                                   │ stdio JSONL
                                                   ▼
                              ┌────────────────────────┐
                              │ dsh --profile multica   │
                              │  = dsh-base             │
                              │  + @multica-ai/dsh-runtime│
                              └───────────┬────────────┘
                                          ▼
                              DeepSeek API（出站 HTTPS）
```

- **dsh 三个 profile 相互独立**：`web`（内置，`dsh web`）、`tui`（终端 UI 插件）、`multica`（Multica 桥插件，headless 一次性会话）。
- 守护进程**只有 `dsh --profile multica --probe` 成功后**才注册 DeepSeek Harness 运行时。
- 所有连接都是出站的，安全组**无需开放任何入站端口**。

---

## 第 1 步：安装 Node.js

**阿里云系统镜像自带 Node 版本不够**（22.04 = Node 12、24.04 = Node 18），需 `22.19+` 或 `24+`。两种方案任选：

### 方案 A：nvm（推荐）

```bash
# 国内加速：nvm 从 npmmirror 下载 Node（建议写入 ~/.bashrc / ~/.zshrc）
export NVM_NODEJS_ORG_MIRROR=https://npmmirror.com/mirrors/node/

curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc        # zsh 用户 source ~/.zshrc

nvm install 22
nvm alias default 22
node -v && npm -v       # node >= 22.19
```

> nvm 场景 npm 全局 bin 在 `~/.nvm/versions/node/v22.x.x/bin/`，**天然用户目录，不要改 prefix，绝不要 sudo**。

### 方案 B：国内镜像手动下载（不想用 nvm）

```bash
cd /tmp
wget https://npmmirror.com/mirrors/node/v22.23.0/node-v22.23.0-linux-x64.tar.xz
sudo tar -xJf node-v22.23.0-linux-x64.tar.xz -C /usr/local --strip-components=1
node -v && npm -v
```

> 方案 B 后**必须做第 2 步**（否则 `npm install -g` 报 EACCES）。

## 第 2 步：配置 npm 全局目录（非 nvm 场景必做，避免 EACCES）

npm 默认全局目录 `/usr/local/lib/node_modules` 普通用户不可写。改到用户目录，之后所有 `npm -g` 免 sudo：

```bash
npm config set prefix ~/.npm-global
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc   # zsh 写 ~/.zshrc
source ~/.bashrc
npm bin -g     # 应输出 /home/<用户>/.npm-global/bin
```

> nvm 方案（A）跳过本步。

## 第 3 步：npm registry 镜像（阿里云关键）

**推荐做法**：本 skill 的脚本（`setup-agent.sh`、两个更新脚本）已内置代理检测——检测到 clash 代理（127.0.0.1:7890）时用官方源，**无代理时自动把 npm/pnpm 切到 npmmirror 镜像**（`export npm_config_registry=https://registry.npmmirror.com/`，等价于每条 `npm install` 加 `--registry=https://registry.npmmirror.com/`），无需手工配置。

手工持久化配置（可选）：

```bash
npm config set registry https://registry.npmmirror.com
npm config get registry    # 确认输出 npmmirror
```

单次安装不想改全局配置时：

```bash
npm install -g @deepseek-ai/dsh@0.1.0-rc.6 --registry=https://registry.npmmirror.com/
```

## 第 4 步：安装 pnpm 与 git

apt/二进制版 Node 裁剪了 corepack，直接用 npm 装：

```bash
npm install -g pnpm
pnpm --version    # 10.x
git --version     # 通常已有，没有则：sudo apt install -y git
```

## 第 5 步：初始工具安装检查：reasonix / codex / claude code

缺失才安装，全部走用户目录 npm 全局：

```bash
# reasonix（Cache-first DeepSeek coding agent）—— npm 包名就是 reasonix
command -v reasonix || npm install -g reasonix
# codex（OpenAI 官方 CLI）
command -v codex    || npm install -g @openai/codex
# claude（Claude Code）
command -v claude   || npm install -g @anthropic-ai/claude-code

reasonix --version
codex --version
claude --version
```

> 若 PATH 上有其他同名命令（apt 的 dsh / 旧残留），先 `which -a <cmd>` 排查，把 nvm bin / `~/.npm-global/bin` 放到 PATH 最前。

## 第 6 步：安装 dsh CLI（固定 rc.6）

```bash
npm install -g @deepseek-ai/dsh@0.1.0-rc.6
dsh --version     # 必须输出 0.1.0-rc.6（与桥插件官方验证组合一致，不要装 rc.7+）
```

## 第 7 步：安装 Multica CLI（用户版，免 root 自更新）

```bash
curl -fsSL https://raw.githubusercontent.com/multica-ai/multica/main/scripts/install.sh | bash
# 脚本默认装系统目录；本 skill 强制用户版（可被自己的 update 替换，无需 sudo）：
# 若已装到 /usr/local/bin，则复制用户版：
mkdir -p ~/.local/bin
cp /usr/local/bin/multica ~/.local/bin/multica && chmod +x ~/.local/bin/multica
export PATH="$HOME/.local/bin:$PATH"    # 写进 ~/.bashrc
multica version
```

**无浏览器环境登录**（纯服务器）：在 Multica Web「设置」创建**个人访问令牌（PAT）**，然后：

```bash
multica login --token
# 按提示粘贴令牌（避免留在 shell history）
multica auth status
```

## 第 8 步：构建并安装 Multica 运行时桥插件

桥插件 `@multica-ai/dsh-runtime` **不在 npm 发布**（`private: true`），源码构建后装入 multica profile：

```bash
# GitHub 慢时用加速前缀：https://gitclone.com/github.com/multica-ai/dsh-multica-runtime.git
git clone https://github.com/multica-ai/dsh-multica-runtime.git
cd dsh-multica-runtime

pnpm install
pnpm check        # check = typecheck + test + build；至少保证 pnpm build 成功，dist/ 必须存在

dsh plugin --profile multica add "$PWD"
```

核对 profile——**bundles 只允许 base + runtime 两个**：

```bash
cat ~/.dsh/profiles/multica/package.json
# "bundles": ["@deepseek-ai/dsh-base", "@multica-ai/dsh-runtime"]
```

> ⚠️ 不要往 multica profile 装任何 TUI / find-plugin：它们自带命令行解析器，会拦截 `--probe` 报 `error: unknown option '--probe' (Did you mean --preset?)`。真装了就移除：
> ```bash
> dsh plugin --profile multica remove deepseek-harness-tui
> dsh plugin --profile multica remove dsh-find-plugin
> ```

## 第 9 步：安装 tui profile（可选，终端 UI）

```bash
dsh plugin --profile tui add @huiliyi37/dsh-tianshu-tui
# 使用：dsh --profile tui
```

> tui 与 multica 互不干扰：TUI 插件只在 `tui` profile；`dsh web` 用内置 web profile。

## 第 10 步：配置 DeepSeek API Key

方式一：环境变量（推荐，daemon 启动前设置，写进 ~/.bashrc）：

```bash
export DEEPSEEK_API_KEY=sk-你的key
```

方式二：dsh 凭据文件（`$DSH_HOME` 默认 `~/.dsh`）：

```bash
mkdir -p ~/.dsh && chmod 700 ~/.dsh
cat > ~/.dsh/.credentials.yaml <<'EOF'
deepseek:
  apiKey: sk-你的key
EOF
chmod 600 ~/.dsh/.credentials.yaml
```

> 凭据解析优先级：环境变量 → `$DSH_HOME/.credentials.yaml` → 启动目录 `.env` → `$DSH_HOME/.env`。

## 第 11 步：验证插件

```bash
# 必须成功（protocol version 1），Multica 才注册运行时
dsh --profile multica --probe

# 列出模型 id（provider/model 形式）
dsh --profile multica --list-models
# 期望能看到 deepseek-official/deepseek-chat 等完整 id
```

## 第 12 步：启动守护进程

```bash
export MULTICA_DSH_PATH=$(which dsh)                       # 推荐：显式指定
export MULTICA_DSH_MODEL=deepseek-official/deepseek-chat   # 推荐：默认模型

multica daemon start       # 已运行时用 restart（重新检测本机工具）
multica daemon status
multica daemon logs -f
```

> 硬性规则：守护进程启动时必须先检测到至少一款内置支持的 CLI（dsh 满足）；装完新工具后必须 `multica daemon restart`。

## 阿里云场景速查

| 问题 | 处理 |
|---|---|
| npm / git 下载慢 | `npm config set registry https://registry.npmmirror.com`；clone 用 gitclone/ghproxy 前缀 |
| nvm 下载 Node 慢 | `export NVM_NODEJS_ORG_MIRROR=https://npmmirror.com/mirrors/node/` |
| `npm install -g` EACCES | 执行第 2 步改 prefix 到 `~/.npm-global`，**不要 sudo** |
| `corepack enable` 找不到 | apt/二进制版 Node 裁剪了 corepack，`npm install -g pnpm` |
| 安全组 | 全链路出站（WSS 443/HTTPS 443），**无需开入站端口**；运行时不在线先查 daemon |
| nvm 下 sudo | 禁止：sudo 走 secure_path 找不到 nvm 命令 |

## 后续

- 在 Multica Web 创建智能体 → `docs/runtime-and-web.md` 第 9 节
- 配置定时更新 → `scripts/agent-weekly-update.sh` + `templates/weekly-update.cron`
- systemd 常驻 → `templates/multica-daemon.service`

## 参考链接

- [DeepSeek Harness 官方仓库](https://github.com/deepseek-ai/deepseek-harness)
- [Multica：安装 AI 编程工具](https://multica.ai/docs/zh/install-agent-runtime)
- [multica-ai/dsh-multica-runtime](https://github.com/multica-ai/dsh-multica-runtime)
- [nvm](https://github.com/nvm-sh/nvm) / [npmmirror](https://npmmirror.com)

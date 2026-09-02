#!/usr/bin/env bash
# =============================================================================
# setup-agent.sh — Multica 服务器端 agent 幂等一键安装（全部在当前用户目录）
#
# 安装内容（缺失才装，可重复执行）：
#   1. reasonix / codex / claude code（初始安装检查，缺失则 npm install -g）
#   2. pnpm
#   3. dsh CLI（固定 @deepseek-ai/dsh@0.1.0-rc.6，与桥插件验证组合一致）
#   4. multica 用户版（~/.local/bin/multica，免 root 自更新）
#   5. 桥插件本地构建并装入 multica profile（@multica-ai/dsh-runtime）
#   6. tui profile（@huiliyi37/dsh-tianshu-tui）
#   7. DeepSeek API Key 配置提示
#   8. 验证 dsh --profile multica --probe
#   9. multica daemon restart
#
# 硬性规则：全程禁止 sudo / root；所有安装路径都在当前用户目录下。
# 手工分步版见 docs/install-linux.md。
# =============================================================================

set -u

log() { echo "[$(date '+%F %T')] $*"; }
failures=0
fail() { log "!! $*"; failures=$((failures + 1)); }

# 超时包装：Linux 有 timeout 则用，避免卡死
run_timeout() {
    if command -v timeout >/dev/null 2>&1; then
        timeout 600 "$@"
    else
        "$@"
    fi
}

# ---------- 0. 前置校验：禁止 root / sudo ----------
if [ "$(id -u)" -eq 0 ]; then
    echo "!! 禁止以 root 安装。请用普通用户执行（所有安装都在用户目录下）："
    echo "   su - <你的用户> && bash setup-agent.sh"
    exit 1
fi

# PATH 前置：nvm bin 或 ~/.npm-global/bin + ~/.local/bin，保证 command -v 命中用户可写副本
NPM_GLOBAL_BIN="$(npm prefix -g 2>/dev/null)/bin"
[ -n "$NPM_GLOBAL_BIN" ] && [ -d "$(dirname "$NPM_GLOBAL_BIN")" ] || NPM_GLOBAL_BIN="$HOME/.npm-global/bin"
case ":$PATH:" in
    *":$NPM_GLOBAL_BIN:"*) ;;
    *) export PATH="$NPM_GLOBAL_BIN:$PATH" ;;
esac
case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) export PATH="$HOME/.local/bin:$PATH" ;;
esac

log "==> 安装前置检查（非 root，PATH=$PATH）"

# ---------- 0.2 npm 源：有代理用官方源，无代理自动切 npmmirror 镜像 ----------
# npm_config_registry 环境变量等价于给每条 npm install 加
# --registry=https://registry.npmmirror.com/（pnpm 同样识别该变量）
if (exec 3<>/dev/tcp/127.0.0.1/7890) 2>/dev/null; then
    export https_proxy="http://127.0.0.1:7890" http_proxy="http://127.0.0.1:7890" all_proxy="socks5://127.0.0.1:7891"
    log "==> 检测到 clash 代理(127.0.0.1:7890)，npm/pnpm 使用官方源"
else
    export npm_config_registry="https://registry.npmmirror.com/"
    log "==> 无代理，npm/pnpm 自动使用 npmmirror 镜像源"
fi

# ---------- 0.1 Node 检查（22.19+ 或 24+） ----------
if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    log "!! 未找到 node/npm。请先按 docs/install-linux.md 第 1 步安装 Node（推荐 nvm），再重跑本脚本"
    exit 1
fi
node_ver="$(node -v)"; npm_ver="$(npm -v)"
node_major="${node_ver#v}"; node_major="${node_major%%.*}"
log "==> Node $node_ver / npm $npm_ver"
if [ "$node_major" -lt 22 ]; then
    log "!! Node 版本过低（需 22.19+ 或 24+）：nvm install 22 && nvm use 22"
    exit 1
fi

# ---------- 1. reasonix / codex / claude code 初始安装检查 ----------
if command -v reasonix >/dev/null 2>&1; then
    log "==> reasonix 已安装: $(command -v reasonix)"
else
    log "==> reasonix 未安装，npm install -g reasonix"
    run_timeout npm install -g reasonix || fail "reasonix 安装失败（退出码 $?）"
fi

if command -v claude >/dev/null 2>&1; then
    log "==> claude (Claude Code) 已安装: $(command -v claude)"
else
    log "==> claude 未安装，npm install -g @anthropic-ai/claude-code"
    run_timeout npm install -g @anthropic-ai/claude-code || fail "claude 安装失败（退出码 $?）"
fi

if command -v codex >/dev/null 2>&1; then
    log "==> codex 已安装: $(command -v codex)"
else
    log "==> codex 未安装，npm install -g @openai/codex"
    run_timeout npm install -g @openai/codex || fail "codex 安装失败（退出码 $?）"
fi

# ---------- 2. pnpm ----------
if command -v pnpm >/dev/null 2>&1; then
    log "==> pnpm 已安装: $(pnpm --version)"
else
    log "==> pnpm 未安装，npm install -g pnpm"
    run_timeout npm install -g pnpm || fail "pnpm 安装失败（退出码 $?）"
fi

# ---------- 3. dsh CLI（固定 0.1.0-rc.6） ----------
DSH_VER_REQUIRED="0.1.0-rc.6"
if command -v dsh >/dev/null 2>&1 && [ "$(dsh --version 2>/dev/null)" = "$DSH_VER_REQUIRED" ]; then
    log "==> dsh 已安装且版本正确: $(dsh --version)"
else
    log "==> 安装 dsh@$DSH_VER_REQUIRED（与桥插件验证组合一致）"
    run_timeout npm install -g "@deepseek-ai/dsh@$DSH_VER_REQUIRED" || fail "dsh 安装失败（退出码 $?）"
    hash -r 2>/dev/null || true
fi
if ! command -v dsh >/dev/null 2>&1 || [ "$(dsh --version 2>/dev/null)" != "$DSH_VER_REQUIRED" ]; then
    log "!! dsh 安装后校验失败（期望 $DSH_VER_REQUIRED），请检查 PATH: $(command -v dsh || echo none)"
    exit 1
fi

# ---------- 4. multica 用户版（~/.local/bin/multica） ----------
MULTICA_USER_BIN="$HOME/.local/bin/multica"
mkdir -p "$HOME/.local/bin"
if [ -x "$MULTICA_USER_BIN" ]; then
    log "==> multica 用户版已存在: $MULTICA_USER_BIN"
elif command -v multica >/dev/null 2>&1; then
    log "==> 复制系统版 multica 到用户目录"
    cp "$(command -v multica)" "$MULTICA_USER_BIN" && chmod +x "$MULTICA_USER_BIN" \
        || fail "复制 multica 到 $MULTICA_USER_BIN 失败"
else
    log "==> 安装 multica（官方脚本），随后部署用户版"
    curl -fsSL https://raw.githubusercontent.com/multica-ai/multica/main/scripts/install.sh | bash \
        && cp "$(command -v multica)" "$MULTICA_USER_BIN" && chmod +x "$MULTICA_USER_BIN" \
        || fail "multica 安装失败；请按 docs/install-linux.md 第 7 步处理"
fi

if [ -x "$MULTICA_USER_BIN" ] && command -v multica >/dev/null 2>&1 \
   && [ "$(command -v multica)" != "$MULTICA_USER_BIN" ]; then
    log "==> 已将 ~/.local/bin 前置，multica 命中用户版: $(command -v multica)"
fi

# 无浏览器环境：引导 PAT 登录（已有 token 则跳过）
if ! "$MULTICA_USER_BIN" auth status >/dev/null 2>&1; then
    log "!! 尚未登录 Multica。无浏览器环境请先创建 PAT 再执行: multica login --token"
    log "   有浏览器环境可执行: multica setup"
fi

# ---------- 5. 桥插件本地构建并装入 multica profile ----------
RUNTIME_SRC="$HOME/dsh-multica-runtime"
if [ -d "$RUNTIME_SRC/.git" ]; then
    log "==> 更新桥插件源码: $RUNTIME_SRC"
    (cd "$RUNTIME_SRC" && git pull --ff-only) >/dev/null 2>&1 || log "!! git pull 失败，继续使用本地源码"
else
    log "==> clone 桥插件（GitHub 慢可用加速前缀，见 docs/install-linux.md）"
    run_timeout git clone --depth 1 https://github.com/multica-ai/dsh-multica-runtime.git "$RUNTIME_SRC" \
        || { log "!! clone 失败，改用加速前缀重试..."; \
             run_timeout git clone --depth 1 https://gitclone.com/github.com/multica-ai/dsh-multica-runtime.git "$RUNTIME_SRC" \
                || fail "桥插件 clone 失败"; }
fi

if [ -f "$RUNTIME_SRC/package.json" ] && [ ! -d "$RUNTIME_SRC/node_modules" ]; then
    log "==> pnpm install（桥插件依赖）"
    (cd "$RUNTIME_SRC" && run_timeout pnpm install) || fail "桥插件 pnpm install 失败"
fi
if [ -f "$RUNTIME_SRC/package.json" ] && [ ! -d "$RUNTIME_SRC/dist" ]; then
    log "==> pnpm build（生成 dist/）"
    (cd "$RUNTIME_SRC" && run_timeout pnpm build) || fail "桥插件 pnpm build 失败"
fi

if grep -q '"@multica-ai/dsh-runtime"' "$HOME/.dsh/profiles/multica/package.json" 2>/dev/null; then
    log "==> multica profile 已包含桥插件"
else
    log "==> 装入 multica profile: dsh plugin --profile multica add $RUNTIME_SRC"
    dsh plugin --profile multica add "$RUNTIME_SRC" || fail "桥插件装入 multica profile 失败"
fi

# ---------- 6. tui profile（终端 UI） ----------
if [ -f "$HOME/.dsh/profiles/tui/package.json" ] \
   && grep -q '@huiliyi37/dsh-tianshu-tui' "$HOME/.dsh/profiles/tui/package.json" 2>/dev/null; then
    log "==> tui profile 已包含 @huiliyi37/dsh-tianshu-tui"
else
    log "==> 安装 tui profile: dsh plugin --profile tui add @huiliyi37/dsh-tianshu-tui"
    run_timeout dsh plugin --profile tui add @huiliyi37/dsh-tianshu-tui || fail "tui profile 安装失败"
fi

# ---------- 7. DeepSeek API Key 配置提示 ----------
if [ -z "${DEEPSEEK_API_KEY:-}" ] && [ ! -f "$HOME/.dsh/.credentials.yaml" ]; then
    log "!! 未检测到 DEEPSEEK_API_KEY，模型推理将不可用。二选一："
    log "   1) export DEEPSEEK_API_KEY=sk-... （建议写入 ~/.bashrc）"
    log "   2) 写入 ~/.dsh/.credentials.yaml（chmod 600），格式见 docs/install-linux.md 第 10 步"
fi

# ---------- 8. 验证 ----------
log "==> 验证 dsh --profile multica --probe"
if dsh --profile multica --probe >/dev/null 2>&1; then
    log "==> --probe 成功（protocol version 1）"
else
    fail "--probe 失败。请检查：profile 是否混入多余插件、dsh 版本是否为 $DSH_VER_REQUIRED"
    log "   排查见 docs/runtime-and-web.md 故障排查 1/2"
fi

# ---------- 9. daemon restart ----------
if [ -x "$MULTICA_USER_BIN" ]; then
    log "==> multica daemon restart"
    "$MULTICA_USER_BIN" daemon restart >/dev/null 2>&1 \
        && log "==> daemon 已重启" || log "!! daemon restart 失败，可稍后手动执行 multica daemon start"
fi

# ---------- 汇总 ----------
if [ "$failures" -gt 0 ]; then
    log "==> 安装完成，但有 $failures 个步骤失败（详见上方日志）"
    exit 1
else
    log "==> 安装全部完成。下一步：Multica Web 创建智能体（docs/runtime-and-web.md 第 4 节）"
    exit 0
fi

#!/usr/bin/env bash
# 开发机全套工具每周自动升级（reasonix / codex / claude / dsh / multica）
# 来源：tests/agent-weekly-update.sh（本仓库开发机实测脚本），保留原逻辑与注释。
# 服务器端只更新 dsh + multica 的轻量版见同目录 agent-weekly-update.sh。
# 参照手动升级记录：先启用 clash 代理，再逐个 update，最后重启 multica daemon
# 由 crontab 每周日执行，输出同时写入 ~/.local/state/weekly-update.log
#
# 环境检验结论（本机实测）：
#   - reasonix/codex/claude/dsh 均在 ~/.nvm/versions/node/v24.14.1/bin 下 ✓
#   - multica 在 /usr/local/bin（nobody:nogroup 所有，普通用户不可写），
#     但 multica update 按 os.Executable 替换"自身所在路径"：已部署用户目录版
#     ~/.local/bin/multica，免 root 即可自动更新（实测 0.4.35 -> 0.4.37 成功），
#     无需 sudo / NOPASSWD sudoers ✓
#   - clash 127.0.0.1:7890/7891 可达时启用代理 ✓
#   - 注意：容器内 crontab 命令不可用（/var/spool/cron 无写权限），
#     crontab 记录需在宿主机或具备权限的环境安装（见 templates/weekly-update.cron）

set -u

LOG_DIR="$HOME/.local/state"
LOG_FILE="$LOG_DIR/weekly-update.log"
mkdir -p "$LOG_DIR"
touch "$LOG_FILE"

# crontab 环境 PATH 精简：nvm 的 bin 必须在最前（保证 codex/claude update
# 内部调用的 npm 是 nvm 的，prefix 指向用户可写目录），系统目录兜底放最后
NVM_BIN="$(ls -d "$HOME"/.nvm/versions/node/*/bin 2>/dev/null | sort -V | tail -1)"
[ -n "$NVM_BIN" ] && export PATH="$NVM_BIN:$PATH"
# 用户本地工具目录前置（multica 用户版等），保证 command -v 命中用户可写副本
export PATH="$HOME/.local/bin:$PATH:/usr/local/bin:/usr/bin:/bin"

PROXY_HTTP="http://127.0.0.1:7890"
PROXY_SOCKS="socks5://127.0.0.1:7891"

# 所有输出同时进终端和日志
exec > >(tee -a "$LOG_FILE") 2>&1

log() { echo "[$(date '+%F %T')] $*"; }

failures=0

# ---------- 1. 代理：clash 端口可达才启用 ----------
if (exec 3<>/dev/tcp/127.0.0.1/7890) 2>/dev/null; then
    export https_proxy="$PROXY_HTTP" http_proxy="$PROXY_HTTP" all_proxy="$PROXY_SOCKS"
    log "==> 代理已启用: $PROXY_HTTP"
else
    # 无代理：npm/pnpm 自动切 npmmirror 镜像（等价于 npm install 加 --registry）
    export npm_config_registry="https://registry.npmmirror.com/"
    log "!! 警告: clash 代理不可达(127.0.0.1:7890)，直连更新；npm 已自动改用 npmmirror 镜像源"
fi

# ---------- 2. reasonix ----------
if command -v reasonix >/dev/null 2>&1; then
    log "==> reasonix update"
    timeout 600 reasonix update || { rc=$?; log "!! reasonix update 失败(退出码 $rc)"; failures=$((failures + 1)); }
else
    log "!! 未找到 reasonix，跳过"
fi

# ---------- 3. codex (npm 全局包) ----------
if command -v codex >/dev/null 2>&1; then
    log "==> codex update"
    timeout 600 codex update || { rc=$?; log "!! codex update 失败(退出码 $rc)"; failures=$((failures + 1)); }
else
    log "!! 未找到 codex，跳过"
fi

# ---------- 4. claude ----------
if command -v claude >/dev/null 2>&1; then
    log "==> claude update"
    timeout 600 claude update || { rc=$?; log "!! claude update 失败(退出码 $rc)"; failures=$((failures + 1)); }
else
    log "!! 未找到 claude，跳过"
fi

# ---------- 5. dsh (npm 全局包，无自带 update 子命令) ----------
if command -v dsh >/dev/null 2>&1; then
    log "==> dsh update (npm install -g @deepseek-ai/dsh@latest)"
    timeout 600 npm install -g "@deepseek-ai/dsh@latest" || { rc=$?; log "!! dsh update 失败(退出码 $rc)"; failures=$((failures + 1)); }
    # npm 更新偶发丢失 bin 链接（曾出现只留 .dsh-* 临时链接），自愈：丢失则重装一次
    if ! command -v dsh >/dev/null 2>&1; then
        log "!! dsh 命令在更新后丢失，自动重装..."
        timeout 600 npm install -g "@deepseek-ai/dsh@latest" && log "!! dsh 重装成功" || { rc=$?; log "!! dsh 重装失败(退出码 $rc)"; failures=$((failures + 1)); }
    fi
else
    log "!! 未找到 dsh，跳过"
fi

# ---------- 6. multica ----------
# multica update 会替换"被调用二进制所在路径"(os.Executable)。
# 实测：将 multica 装在用户可写的 ~/.local/bin 后，
# `~/.local/bin/multica update` 免 root 即可更新，
# /usr/local/bin 下的旧版不受影响，因此无需 sudo / NOPASSWD sudoers。
MULTICA_USER_BIN="$HOME/.local/bin/multica"
if [ -x "$MULTICA_USER_BIN" ]; then
    log "==> multica update (用户目录版 $MULTICA_USER_BIN，免 root)"
    timeout 600 "$MULTICA_USER_BIN" update || { rc=$?; log "!! multica update 失败(退出码 $rc)"; failures=$((failures + 1)); }
elif [ -x /usr/local/bin/multica ]; then
    log "==> 首次部署 multica 用户版 (cp /usr/local/bin/multica -> $MULTICA_USER_BIN)"
    if cp /usr/local/bin/multica "$MULTICA_USER_BIN" && chmod +x "$MULTICA_USER_BIN"; then
        timeout 600 "$MULTICA_USER_BIN" update || { rc=$?; log "!! multica update 失败(退出码 $rc)"; failures=$((failures + 1)); }
    else
        log "!! 复制 multica 到用户目录失败，无法自动更新；请手动执行: sudo multica update"
        failures=$((failures + 1))
    fi
else
    log "!! 未找到 multica，跳过"
fi
if [ -x "$MULTICA_USER_BIN" ]; then
    # daemon 由 PATH 中的 multica 拉起新二进制，普通用户即可重启
    log "==> multica daemon restart"
    "$MULTICA_USER_BIN" daemon restart || { rc=$?; log "!! multica daemon restart 失败(退出码 $rc)"; failures=$((failures + 1)); }
fi

# ---------- 汇总 ----------
if [ "$failures" -gt 0 ]; then
    log "==> 本轮更新完成，但有 $failures 个步骤失败（详见上方日志）"
    exit 1
else
    log "==> 本轮更新全部完成"
    exit 0
fi

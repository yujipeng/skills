#!/usr/bin/env bash
# =============================================================================
# agent-weekly-update.sh — 服务器端 multica agent 每周自动更新（精简版）
#
# 只更新与 multica agent 相关的组件（全部当前用户目录，无需 root）：
#   1. dsh CLI（npm 全局包，更新到 latest 后强制验证 --probe，失败自动回退更新前版本）
#   2. multica 用户版（~/.local/bin/multica update，免 root）
#   3. multica daemon restart（拉起新二进制）
#
# 由 crontab 每周执行，输出同时写入 ~/.local/state/weekly-update.log。
# crontab 模板见 templates/weekly-update.cron。
# 开发机完整版（reasonix/codex/claude/dsh/multica）见 agent-weekly-update-full.sh。
# =============================================================================

set -u

LOG_DIR="$HOME/.local/state"
LOG_FILE="$LOG_DIR/weekly-update.log"
mkdir -p "$LOG_DIR"
touch "$LOG_FILE"

# crontab 环境 PATH 精简：npm 全局 bin（nvm bin 或 ~/.local/bin）在最前，
# 保证 dsh / npm 命中用户可写副本，系统目录兜底放最后
NPM_GLOBAL_BIN="$(npm prefix -g 2>/dev/null)/bin"
case "$NPM_GLOBAL_BIN" in
    "$HOME"/*) ;;                               # nvm bin / ~/.local/bin，直接前置
    *) NPM_GLOBAL_BIN="$HOME/.local/bin" ;;     # prefix 在系统目录时不前置，回退用户级 ~/.local/bin
esac
export PATH="$NPM_GLOBAL_BIN:$HOME/.local/bin:$PATH:/usr/local/bin:/usr/bin:/bin"

PROXY_HTTP="http://127.0.0.1:7890"
PROXY_SOCKS="socks5://127.0.0.1:7891"

# 所有输出同时进终端和日志
exec > >(tee -a "$LOG_FILE") 2>&1

log() { echo "[$(date '+%F %T')] $*"; }

failures=0

# ---------- 0. 非 root 校验（本脚本设计为普通用户执行） ----------
if [ "$(id -u)" -eq 0 ]; then
    log "!! 禁止以 root 执行本脚本（用户目录更新脚本只跑普通用户）"
    exit 1
fi

# ---------- 1. 代理 / npm 源：clash 可达用代理+官方源；无代理自动切 npmmirror 镜像 ----------
if (exec 3<>/dev/tcp/127.0.0.1/7890) 2>/dev/null; then
    export https_proxy="$PROXY_HTTP" http_proxy="$PROXY_HTTP" all_proxy="$PROXY_SOCKS"
    log "==> 代理已启用: $PROXY_HTTP"
else
    export npm_config_registry="https://registry.npmmirror.com/"
    log "==> 无代理(clash 127.0.0.1:7890 不可达)，npm 自动使用 npmmirror 镜像源"
fi

# ---------- 2. dsh ----------
if command -v dsh >/dev/null 2>&1; then
    DSH_OLD_VER="$(dsh --version 2>/dev/null)"
    log "==> dsh update (当前 $DSH_OLD_VER -> latest)"
    timeout 600 npm install -g "@deepseek-ai/dsh@latest" || { rc=$?; log "!! dsh update 失败(退出码 $rc)"; failures=$((failures + 1)); }

    # 更新后强制验证：--probe 必须成功（Multica 注册运行时的前提）
    if dsh --profile multica --probe >/dev/null 2>&1; then
        log "==> dsh $(dsh --version 2>/dev/null) --probe 验证通过"
    else
        log "!! dsh 更新后 --probe 失败（可能与桥插件不兼容），回退到更新前版本 $DSH_OLD_VER"
        timeout 600 npm install -g "@deepseek-ai/dsh@$DSH_OLD_VER" \
            && dsh --profile multica --probe >/dev/null 2>&1 \
            && log "==> 已回退 $DSH_OLD_VER 且 --probe 通过" \
            || { log "!! 回退失败，请按 docs/runtime-and-web.md 故障排查处理"; failures=$((failures + 1)); }
    fi
else
    log "!! 未找到 dsh，跳过（可先执行 setup-agent.sh 安装）"
fi

# ---------- 3. multica（用户版，免 root） ----------
MULTICA_USER_BIN="$HOME/.local/bin/multica"
if [ -x "$MULTICA_USER_BIN" ]; then
    log "==> multica update (用户目录版 $MULTICA_USER_BIN，免 root)"
    timeout 600 "$MULTICA_USER_BIN" update || { rc=$?; log "!! multica update 失败(退出码 $rc)"; failures=$((failures + 1)); }
elif [ -x /usr/local/bin/multica ]; then
    log "==> 首次部署 multica 用户版 (cp /usr/local/bin/multica -> $MULTICA_USER_BIN)"
    if cp /usr/local/bin/multica "$MULTICA_USER_BIN" && chmod +x "$MULTICA_USER_BIN"; then
        timeout 600 "$MULTICA_USER_BIN" update || { rc=$?; log "!! multica update 失败(退出码 $rc)"; failures=$((failures + 1)); }
    else
        log "!! 复制 multica 到用户目录失败，请手动执行: sudo multica update"
        failures=$((failures + 1))
    fi
else
    log "!! 未找到 multica，跳过"
fi

# ---------- 4. daemon restart（拉起新二进制并重新检测工具） ----------
if [ -x "$MULTICA_USER_BIN" ]; then
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

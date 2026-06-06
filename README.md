# skills

个人 Agent Skills 收藏仓库。每个子目录是一个独立的 skill，包含 `SKILL.md` 及其依赖文件。

## 已收录

### `api-relay-audit/`

第三方 AI API 中转 / 代理服务的安全审计工具（红队向）。

- **来源**：[toby-bridges/api-relay-audit](https://github.com/toby-bridges/api-relay-audit)
- **版本**：v2.3.0
- **License**：AGPL-3.0-only（作者 Toby Bridges，再分发注意传染性条款）
- **依赖**：Python 3 + `curl`，零第三方库

检测项：隐藏 prompt 注入、prompt 泄漏、指令覆盖、上下文截断、tool-call 替换、包安装指令篡改、上游凭证 / 内部 header 泄漏、Anthropic SSE 流损坏、上游 channel 偷换、Web3 钱包安全注入、基础设施指纹、延迟方差。

**运行**：

```bash
python3 api-relay-audit/audit.py \
  --key "$API_RELAY_AUDIT_KEY" \
  --url "https://你的中转地址/v1" \
  --model claude-opus-4-6 \
  --profile general \
  --output api-relay-audit-report.md
```

`--profile` 支持 `general` / `web3` / `full`。`audit.py` 已随仓库本地化，运行时无需再联网拉取脚本。

> 切勿在报告、文件名、shell 记录或提交中泄露原始 API key；建议使用临时 / 低权限 key，审计后视情况轮换。

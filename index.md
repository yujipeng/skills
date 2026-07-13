# Skills Index

本仓库收录 14 个 Agent Skills。每个目录保留自己的上游许可证和运行要求；使用前请阅读对应的 `SKILL.md`。

| Skill | 作用 | 来源 / 版本 |
|---|---|---|
| [`api-relay-audit`](api-relay-audit/) | 审计第三方 AI API relay 的注入、泄漏、模型替换和流式异常 | `toby-bridges/api-relay-audit` v2.3.0 |
| [`api-relay-perf-bench`](api-relay-perf-bench/) | 测量 relay 的 TTFT、延迟分位数及响应纯度 | `gigi1121/audit_ai_api` v1.0.0 |
| [`browser-act`](browser-act/) | 通过 BrowserAct CLI 操作动态网页和浏览器会话 | BrowserAct v2.0.2 |
| [`browser-act-skill-forge`](browser-act-skill-forge/) | 从网站探索结果生成可重复使用的数据提取或操作 skill | BrowserAct v1.0.6 |
| [`fireworks-tech-graph`](fireworks-tech-graph/) | 生成并校验 SVG + PNG 架构图、流程图、UML、ER 图和 AI 系统图 | `yizhiyanhua-ai/fireworks-tech-graph` v1.0.5 |
| [`frontend-design`](frontend-design/) | 为新建或改造的前端界面制定有辨识度的视觉方向和实现原则 | `anthropics/skills` main |
| [`guizang-ppt-skill`](guizang-ppt-skill/) | 生成电子杂志或瑞士风 HTML 演示、PPT 配图和社交平台封面 | `op7418/guizang-ppt-skill` main |
| [`humanizer`](humanizer/) | 识别并减少文本中的 AI 写作痕迹，同时保留原意、语气和有效的人类写作特征 | `blader/humanizer` v2.8.2 |
| [`humanizer-zh`](humanizer-zh/) | 针对中文表达识别并重写 AI 写作痕迹 | `op7418/Humanizer-zh` main |
| [`prototype-html`](prototype-html/) | 生成带交互和说明的单文件 HTML 产品原型 | `vagerent/prototype-html` v1.0.0 |
| [`self-improving`](self-improving/) | 通过反思、纠错和持久化记忆改进 Agent 行为 | Clawic v1.2.16 |
| [`tc-exam-solver`](tc-exam-solver/) | 通过 Chrome 会话完成 tcredit AI 知识考试 | 内部 v1.0.0 |
| [`tc-protohub`](tc-protohub/) | 打包、发布、更新和查询 ProtoHub 原型 | `airclear/skills` main，本地 URL 适配 |
| [`web-access`](web-access/) | 提供搜索、网页提取和基于 CDP 的浏览器联网能力 | `eze-is/web-access` v2.5.3 |

## 运行时提示

- `browser-act` 需要 Python 3.12 和 `uv` 安装的 `browser-act-cli`。
- `fireworks-tech-graph` 推荐使用 `cairosvg`，也可回退到 `rsvg-convert` 或 Puppeteer 导出 PNG。
- `guizang-ppt-skill` 输出可直接打开的单文件 HTML；瑞士风演示可使用自带 Node.js 校验脚本。
- `web-access` 需要 Node.js 22+；浏览器交互模式还需要 Chrome 或 Edge 开启远程调试。
- API relay 相关 skill 的密钥必须通过环境变量传入，禁止提交真实密钥。

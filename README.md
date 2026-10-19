# skills

个人 Agent Skills 收藏仓库。每个子目录是一个独立的 skill，包含 `SKILL.md` 及其依赖文件。

兼容：**Claude Code / OpenClaw**（SKILL.md 原生）、**Hermes**（tap install）、**Codex / 通用**（clone 后直接运行）。

## 已收录

### `api-relay-audit/`

第三方 AI API 中转 / 代理服务的安全审计工具（红队向）。

- **来源**：[toby-bridges/api-relay-audit](https://github.com/toby-bridges/api-relay-audit)
- **版本**：v2.4.0
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

---

### `api-relay-perf-bench/`

第三方 AI API 中转服务的性能基准 + 响应纯净度检测工具。

- **创意来源**：[gigi1121/audit_ai_api](https://github.com/gigi1121/audit_ai_api)
- **版本**：v1.0.0
- **License**：AGPL-3.0-only
- **依赖**：Python 3 + `curl`，零第三方库

测量项：流式 TTFT、p50/p90/p95/p99 延迟、身份泄漏、系统提示泄漏、中转内部 token、语言不匹配、拒绝响应、空响应。输出自包含 HTML + JSON 报告。

**运行**：

```bash
# 单端点
python3 api-relay-perf-bench/perf-bench.py \
  --url "$PERF_BENCH_URL" \
  --key "$PERF_BENCH_KEY" \
  --vendor gpt \
  --rounds 10 \
  --output perf-report.html

# 多端点对比（JSON 配置，自备 config 文件）
python3 api-relay-perf-bench/perf-bench.py \
  --config your-endpoints.json \
  --output perf-report.html
```

> 与 `api-relay-audit` 互补：audit 做安全深查，perf-bench 做速度和纯净度快检。建议两者配合使用。

---

### `browser-act/`

Browser automation CLI for AI agents。提供 Stealth 反检测浏览器、Chrome 导入、无头浏览器自动化能力，支持数据提取、表单填写、截图、网络请求捕获、多浏览器并行、验证码自动处理等。

- **来源**：[BrowserAct](https://www.browseract.com)
- **安装**：`uv tool install browser-act-cli --python 3.12`
- **版本**：v2.0.2
- **License**：详见 SKILL.md
- **依赖**：Python 3.12+、uv package manager

核心功能：`stealth-extract`（反检测内容提取）、session 管理（多窗口隔离）、network request 捕获、solve-captcha。

> 参考用法见本仓库 `browser-act/SKILL.md`。browser-act 的 Stealth 浏览器可绕过 X/Twitter、Reddit 等站点的反爬检测。

---

### `browser-act-skill-forge/`

将任意网站的数据提取或操作需求转化为可复用的 Agent Skill 包（SKILL.md + Python 脚本）。先探索（API 优先，DOM 兜底），再生成已验证的 Skill 包，后续调用无需重复探索。

- **来源**：[BrowserAct](https://www.browseract.com)
- **版本**：v1.0.6
- **License**：详见 SKILL.md

典型场景：批量提取（数百/数千条记录）、网站内部 API 逆向、将现有爬虫/SaaS 工具复现为 Skill。

---

### `web-access/`

给 AI Agent 装上完整联网能力的 Skill — 联网策略 + CDP 浏览器操作 + 站点经验积累，兼容所有支持 SKILL.md 的 Agent（Claude Code、Cursor、Gemini CLI、Codex CLI 等）。

- **来源**：[eze-is/web-access](https://github.com/eze-is/web-access)
- **版本**：v2.5.4
- **License**：MIT
- **依赖**：Node.js 22+（原生 WebSocket）、Chrome / Edge / Chromium 系浏览器

核心能力：联网工具自动选择（WebSearch / WebFetch / curl / Jina / CDP）、CDP Proxy 直连用户日常浏览器（天然登录态）、三种点击方式（JS click / 真实鼠标事件 / 文件上传）、本地书签/历史检索、多目标并行子 Agent 分治、站点经验跨 session 积累。

> 与 `browser-act` 互补：`browser-act` 提供独立的 Stealth 反检测浏览器环境，`web-access` 直连用户日常浏览器并侧重联网策略调度。

---

### `humanizer/`

将 AI 生成文本改写为更自然人类风格的 Skill。基于 Wikipedia「AI 写作特征」指南，系统检测并修正：浮夸象征手法、推广性语言、空洞 -ing 分析、模糊归因、em dash 滥用、三段式、AI 特征词汇、负向平行句、过量连接短语等。

- **版本**：v2.11.1
- **来源**：[blader/humanizer](https://github.com/blader/humanizer)
- **依赖**：无（纯提示工程）

---

### `life-decision-guide/`

按《高性价比人生指南》回答具体人生决策的 Skill：先到书里把相关条目查出来，再照书自己的算账方式（成本 = 钱 + 时间 + 毅力，收益量级，证据等级 A/B/C）排序作答，每条注明出自第几节第几条；查不到就直说，不凭记忆补数字、补法条。急症、自杀念头、法律程序等情形先走对应的应急分支。

- **来源**：[eternity4719/HowToLiveBetter](https://github.com/eternity4719/HowToLiveBetter) 的 `skills/life-decision-guide/`
- **版本**：v1.0.0
- **License**：CC-BY-4.0（正文著作权归上游；仓库代码部分为 MIT）
- **依赖**：无（纯提示工程）；正文约 1.3 MB 不随本仓库分发，运行时按需 `git clone --depth 1` 整取或 `curl` 单文件取

---

### `prototype-html/`

根据产品需求生成可交互的单文件 HTML 原型。适合快速验证 UI 布局、交互逻辑和功能演示，无需搭建前端环境。

- **版本**：v1.0.0
- **依赖**：无（生成纯 HTML，浏览器直接打开）

---

### `huashu-design/`

用 HTML 做设计的全流程 skill：高保真交互原型、HTML deck（可导出可编辑 PPTX）、信息图 / 数据可视化、时间轴动画（MP4 / GIF），以及设计方向顾问和 5 维评审。核心机制是先出三个真实方向让用户选，再执行。

- **来源**：[alchaincyf/huashu-design](https://github.com/alchaincyf/huashu-design)
- **版本**：v3.0.0
- **License**：MIT（2026-05-14 起；早期版本为 Personal Use License）
- **依赖**：Node.js + npm 包 `playwright` / `sharp` / `pptxgenjs` / `pdf-lib`；FFmpeg；Python 3 + `playwright` / `pillow`（截图、设计体检）
- **引用关系**：根目录 `SKILL.md` 即 skill 入口，直接引用 `references/`、`assets/`、`scripts/`、`demos/` 四个子目录；`scripts/capabilities.py` 会把 `huashu-motion` 识别为兄弟 skill。与 `frontend-design`、`guizang-ppt-skill`、`prototype-html` 功能有重叠，但覆盖面更广、运行时更重。

核心能力：84 种 HTML 原生风格库（网页 / PPT / 信息图 / App / 中文与东亚）、品牌资产五步协议、三方向门、可编辑 PPTX 导出、`design_lint.py` 设计体检与外观账本。

**运行**：

```bash
# 安装到 agent（任选其一）
npx skills add alchaincyf/huashu-design

# 本仓库内直接探测本机能力
python3 huashu-design/scripts/capabilities.py
```

> 设计 → 渲染 → 导出的核心链路本地运行；`scripts/cloud/` 下的豆包 TTS / 火山方舟看片评审是可选云能力，需自备 key 并用 `--yes` 显式确认。

---

### `huashu-motion/`

用代码拍发布片 / 动效片的 skill：agent 写单文件 HTML + GSAP 时间线，本机 Chrome 逐帧渲染，FFmpeg 合成配乐、音效和视频；浏览器里的 studio 支持指着画面提修改。

- **来源**：[alchaincyf/huashu-motion](https://github.com/alchaincyf/huashu-motion)
- **版本**：v0.1.0（收录 commit `3e92780`，即 v0.1.0 之后 1 个提交）
- **License**：MIT；GSAP 为 GSAP Standard License，随附字体为 SIL OFL 1.1；「豆子花叔」角色不在 MIT 授权范围内，仅限本项目示范使用
- **依赖**：Node.js 22+、Chrome / Chromium / Edge、FFmpeg；可选真乐器采样（约 55 MB）、Kokoro 口播模型（约 325 MB）、`whisper-cpp`
- **引用关系**：`skills/huashu-motion/bin/om` 是 skill 入口，优先调用同级 `cli/om.js`，找不到时回退 `npx huashu-motion`；`runtime/`、`studio/`、`templates/`、`fonts/` 为运行时资产。`SKILL.md` 通过相对路径引用 `references/` 下的方法文档、运动语言库和示范谱。
- **注意**：本仓库收录的是完整上游项目，不是单文件 skill；`skills/huashu-motion/` 才是 skill 本体，其余目录是它能跑起来的依赖。

核心能力：导演规则与节奏单、20 种运动语言、10 个起步模板、23 种音效、ABC 记谱作曲、口播逐字对齐、`om check` / `om qa` 渲染前后检查、MP4 / MOV / WebM / GIF 导出。

**运行**：

```bash
# 环境检查（直接使用仓库内的 CLI）
huashu-motion/skills/huashu-motion/bin/om doctor

# 或使用 npm 发布版
npx huashu-motion doctor
```

---

### `self-improving/`

让 Agent 具备自我反思与持续学习能力的 Skill。当命令/工具失败、用户纠正、知识过时或发现更优方案时自动触发，将修正持久化写入本地记忆文件，下次对话直接应用。

- **版本**：v1.2.16
- **来源**：[clawic.com/skills/self-improving](https://clawic.com/skills/self-improving)
- **注意**：`corrections.md`、`memory.md`、`heartbeat-state.md`、`learning.md`、`reflections.md` 为运行时状态文件，已通过子目录 `.gitignore` 屏蔽，本地保留。

---

### `tc-exam-solver/`

自动完成 `ai-exam.tcredit.com` 飞书认证考试的 Skill。通过 CDP 直连用户已登录的 Chrome 浏览器，自动列出可选考试、逐题分析作答、二次核查后提交。

- **版本**：v1.0.0
- **依赖**：Python 3、Chrome 已登录飞书（保留 JWT）
- **注意**：必须等待 >5 分钟后再提交以规避机器人检测；PDF 培训材料为私有业务文件，仅本地保留。

**脚本说明**：

```
scripts/
  check_login.py    # 检查飞书登录态
  list_exams.py     # 列出可参加的考试
  start_exam.py     # 开始考试，返回题目
  get_questions.py  # 获取题目详情
  get_attempts.py   # 查看历史作答
  submit_exam.py    # 提交答案
```

---

### `tc-protohub/`

在 ProtoHub 私有沙箱管理 HTML 原型的 Skill。支持上传目录或 ZIP、更新现有原型、列出原型列表、获取预览链接，强制校验 `index.html` 入口文件。

- **版本**：v1.0.0
- **环境变量**：`PROTOHUB_API_KEY`、`PROTOHUB_URL`
- **依赖**：Python 3

> 与 `prototype-html` 配套使用：`prototype-html` 负责生成原型，`tc-protohub` 负责发布到 ProtoHub。

---

### `multica-server-setup/`

Multica 服务器端 agent 安装与定时更新 Skill（Linux 服务器为主，macOS 开发机可选）。引导安装 reasonix / codex / Claude Code（缺失时）、dsh 三 profile（web / tui / multica）、`@multica-ai/dsh-runtime` 桥插件、DeepSeek API Key 与 Multica Web 智能体创建，并配置每周自动更新（crontab / systemd / launchd）。

- **版本**：v1.0.0（内部 skill，源自本仓库 `tests/` 实测脚本与教程）
- **硬性规则**：所有安装限当前用户目录，全程禁止 sudo / root；dsh 固定 `0.1.0-rc.6`；multica profile 只允许 base + runtime 两个 bundle
- **环境变量**：`DEEPSEEK_API_KEY`（必填）、`MULTICA_DSH_PATH`、`MULTICA_DSH_MODEL`（推荐）
- **脚本**：`scripts/setup-agent.sh`（一键安装）、`agent-weekly-update.sh`（服务器精简更新）、`agent-weekly-update-full.sh`（开发机完整更新）
- **文档**：`docs/install-linux.md`（含阿里云 ECS 特化）、`docs/runtime-and-web.md`（验证 / Web 智能体 / 故障排查）
- **模板**：`templates/`（crontab / systemd / launchd）

---
name: tcredit-exam-solver
description: "自动完成 ai-exam.tcredit.com 考试的 Skill。通过 chrome-direct 控制用户自己的 Chrome 浏览器（保留飞书登录态），自动检查登录、列出可选考试系列、逐题分析作答、二次核查后提交。必须等待 >5 分钟才能提交，以避免机器人检测。"
metadata:
  site: ai-exam.tcredit.com
  browser_type: chrome-direct
  auth: 飞书 (Feishu) OAuth，JWT 存于 localStorage['token']
  version: "1.0.0"
---

# tcredit-exam-solver

自动完成 [ai-exam.tcredit.com](https://ai-exam.tcredit.com/exam) 上的 AI 知识考试。

**适用场景**：用户已在 Chrome 中用飞书账号登录过该网站，想让 Agent 自动答题并提交。

---

## 前置条件检查

在执行任何操作前，必须依次确认以下两项：

### 1. 检查 browser-act 是否已安装

```bash
browser-act --version
```

- **已安装**（显示版本号）→ 继续
- **未安装**（`command not found`）→ 提示用户安装：

  ```bash
  uv tool install browser-act-cli --python 3.12
  ```

  安装完成后重新验证 `browser-act --version`，确认成功后再继续。

  > 若未安装 `uv`，先执行：`curl -LsSf https://astral.sh/uv/install.sh | sh`

### 2. 确认 Chrome 浏览器正在运行

此 Skill 使用 `chrome-direct` 类型，**直接接管用户当前运行的 Chrome 进程**，必须满足：

- ✅ Chrome 浏览器已启动并处于运行状态
- ✅ Chrome 中已用**飞书账号**登录过 `ai-exam.tcredit.com`（存有有效 Cookie）

若 Chrome 未运行，提示用户：

> ⚠️ 请先打开 Chrome 浏览器，访问 https://ai-exam.tcredit.com/exam 并完成飞书登录，然后再执行此 Skill。

---

## 浏览器要求

必须使用 `chrome-direct` 类型的浏览器，直接接管用户正在运行的 Chrome，继承所有 Cookie 和登录态。

**已创建的浏览器**（优先复用）：
- ID: `direct_local_103005226035839153`
- 名称: `exam-tcredit`
- 类型: `chrome-direct`
- 描述: 直接控制用户Chrome，访问 ai-exam.tcredit.com，使用飞书账号于吉鹏完成业务问题定义考试

---

## 执行流程

```
Step 1: 检查登录状态
Step 2: 列出可选考试系列 → 请用户选择
Step 3: 检查是否有进行中的考试（恢复 or 新建）
Step 4: 获取所有题目和选项（按当前 attempt 的题目顺序）
Step 5: AI 逐题分析，生成答案列表（严格按 question_id 对应）
Step 6: 等待 >5 分钟（从考试开始计时，避免机器人检测）
Step 7: 二次核查答案 → 提交 → 报告成绩
```

---

## Step 1 — 检查登录状态

打开浏览器并导航到目标页面：

```bash
browser-act --session exam1 browser open direct_local_103005226035839153 https://ai-exam.tcredit.com/exam
browser-act --session exam1 wait stable
```

执行登录检查脚本：

```bash
browser-act --session exam1 eval "$(python scripts/check_login.py)"
```

**解读结果**：
- `logged_in: true` → 继续 Step 2
- `logged_in: false` → **停止，提示用户**：

> ⚠️ 检测到未登录状态。请先在 Chrome 中完成飞书扫码登录：
> 1. 打开 https://ai-exam.tcredit.com/exam
> 2. 点击「飞书登录」，用飞书 App 扫描二维码
> 3. 登录成功后，再次运行此 Skill

若用户需要在自动化浏览器中登录（而非已有的 Chrome），执行：

```bash
browser-act --session exam1 remote-assist --objective "请用飞书扫码完成登录，登录成功后点击确认"
```

**登录完成后**：重新执行 `check_login.py` 验证登录状态再继续。

---

## Step 2 — 列出考试系列，让用户选择

```bash
browser-act --session exam1 eval "$(python scripts/list_exams.py)"
```

将返回的 `exams` 数组格式化展示给用户，例如：

```
可选的考试系列：
1. [ID=29] 业务问题定义 - 40题，每题2分（is_open: true）
2. [ID=30] 系统架构设计 - 40题，每题2分（is_open: true）
...

请问您要参加哪个考试系列？（输入序号或考试名称）
```

**等待用户回复**后记录 `exam_id`，继续 Step 3。

---

## Step 3 — 检查并处理进行中的考试

```bash
browser-act --session exam1 eval "$(python scripts/get_attempts.py)"
```

**逻辑判断**：
- 若存在 `in_progress` 且 `exam_id` 匹配 → 使用该 `attempt_id`，跳过创建，直接 Step 4
- 若不存在 → 创建新考试：

```bash
browser-act --session exam1 eval "$(python scripts/start_exam.py <exam_id>)"
```

记录返回值：
- `attempt_id`：本次作答 ID（全程使用此 ID）
- `started_at`：考试开始时间（用于计算等待时间）
- `questions`：题目列表（可直接用，也可 Step 4 重新获取）

> ⚠️ **注意**：若收到 `HAS_IN_PROGRESS_ATTEMPT` 错误（HTTP 400），说明已有未提交的考试，必须恢复而非新建。重新调用 `get_attempts.py` 找到对应 attempt。

---

## Step 4 — 获取题目和选项（每次作答必须重新获取）

```bash
browser-act --session exam1 eval "$(python scripts/get_questions.py <exam_id> <attempt_id>)"
```

**关键约束**：
- **每个 attempt 的题目顺序和选项顺序（A/B/C/D）均独立随机**，绝对不能复用上一次 attempt 的答案映射
- 必须完整读取每道题的 `stem`、`option_a`、`option_b`、`option_c`、`option_d` 字段
- 按返回的 `questions` 数组顺序处理，记录每题的 `id`（即 `question_id`）

返回数据格式：
```json
{
  "attempt_id": 441,
  "questions": [
    {
      "id": 874,
      "exam_id": 30,
      "category": "状态流转",
      "stem": "状态流转约束的核心目标是：",
      "option_a": "...",
      "option_b": "...",
      "option_c": "...",
      "option_d": "...",
      "score": 2
    }
  ],
  "answers": [],
  "remaining_seconds": 3584
}
```

---

## Step 5 — 读取培训材料，逐题分析作答

### 5a. 读取培训材料原文

答题前必须先读取以下两份培训材料 PDF，以原始材料内容为准，不得仅依赖记忆或摘要。

四份文件已内置在 Skill 目录中，路径为（相对于本 SKILL.md 所在目录）：

```
第1期-业务定义问题培训材料 6.17.pdf   ← 业务问题定义工程
第2期-系统架构培训材料6.18.pdf        ← 系统架构设计工程
第3期-测试定义问题培训材料6.22.pdf    ← 测试定义问题工程
第4期-AI编排培训材料6.23.pdf          ← AI 编排工程
```

使用 Read 工具读取（路径基于本 Skill 的安装目录，Claude Code 原生支持读取 PDF）：

```
Read <skill_dir>/第1期-业务定义问题培训材料 6.17.pdf
Read <skill_dir>/第2期-系统架构培训材料6.18.pdf
Read <skill_dir>/第3期-测试定义问题培训材料6.22.pdf
Read <skill_dir>/第4期-AI编排培训材料6.23.pdf
```

> `<skill_dir>` 为本 SKILL.md 所在的绝对目录路径。若通过 `~/.claude/skills/tcredit-exam-solver/` 安装，则路径为：
> - `~/.claude/skills/tcredit-exam-solver/第1期-业务定义问题培训材料 6.17.pdf`
> - `~/.claude/skills/tcredit-exam-solver/第2期-系统架构培训材料6.18.pdf`
> - `~/.claude/skills/tcredit-exam-solver/第3期-测试定义问题培训材料6.22.pdf`
> - `~/.claude/skills/tcredit-exam-solver/第4期-AI编排培训材料6.23.pdf`

若文件不存在或无法读取，提示用户将 PDF 放回 Skill 目录后重试，并暂停执行。

### 5b. 逐题分析

读取材料后，对 Step 4 获取到的每道题进行独立分析：

**分析流程（每道题）**：
1. 读题干 → 识别关键概念，定位到材料中的对应章节
2. 从材料原文中找到最相关的定义或描述
3. 逐一对照 A/B/C/D 四个选项（注意：**每次考试选项顺序随机**，不能按字母猜测）
4. 选择与材料原文最吻合的选项
5. 记录：`{"question_id": <id>, "answer": "<A|B|C|D>"}`

**选项对照规则**：
- 选项与材料某处原话高度吻合 → 优先选择
- 多个选项表面相似 → 以材料中的精确定义为准，排除偷换概念的干扰项
- 材料中明确反对或不推荐的表述 → 排除

**构建答案列表时的顺序要求**：
- 必须保持与 `questions` 数组相同的顺序（按 `id` 对应）
- 答案列表格式：`[{"question_id": 874, "answer": "D"}, {"question_id": 873, "answer": "A"}, ...]`

---

## Step 6 — 等待 >5 分钟后才能提交

计算已用时间：`elapsed = (当前时间 - started_at的时间戳) 秒`

**强制等待规则**：
- 若 `elapsed < 300秒`（5分钟），必须等待 `300 - elapsed` 秒后再提交
- 原因：系统检测提交速度，过快会被识别为机器人
- 等待期间可告知用户：`⏳ 已答完所有题目，等待 X 秒后提交（避免机器人检测）...`

---

## Step 7 — 二次核查 + 提交

### 二次核查步骤

在提交前，对答案进行二次检查：

1. **完整性检查**：确认答案数量 = 题目数量，无遗漏
2. **ID 对应检查**：每个 `question_id` 都有对应答案，无重复或错位
3. **格式检查**：所有答案均为 A/B/C/D 之一，无空值
4. **抽查核验**：随机抽取 3-5 道题，重新确认题干与答案的对应关系

核查通过后，生成提交用的 JSON 字符串：

```bash
ANSWERS_JSON='[{"question_id":874,"answer":"D"},{"question_id":873,"answer":"A"}]'
```

### 提交

```bash
browser-act --session exam1 eval "$(python scripts/submit_exam.py <exam_id> <attempt_id> "$ANSWERS_JSON")"
```

**成功响应**：
```json
{
  "attempt_id": 441,
  "score": 100,
  "total_possible": 123,
  "passed": true,
  "pass_threshold": 90
}
```

**向用户报告**：
```
✅ 考试提交成功！
- 得分：100 / 123
- 通过状态：通过（pass_threshold: 90）
- Attempt ID：441
```

**失败情况处理**：
- `ALREADY_SUBMITTED`：该 attempt 已提交，查看 `get_attempts.py` 结果中的历史成绩
- `ATTEMPT_EXPIRED`：超时（60分钟），此次考试失效，需新建 attempt 重考
- 其他错误：展示错误信息，让用户决定下一步

---

## 关闭会话

完成后关闭浏览器会话（不影响用户的 Chrome 进程）：

```bash
browser-act session close exam1
```

---

## Scripts 参数速查

| 脚本 | 参数 | 功能 |
|------|------|------|
| `check_login.py` | 无 | 检查登录状态，返回 `logged_in` |
| `list_exams.py` | 无 | 列出所有开放考试，返回 `exams[]` |
| `get_attempts.py` | 无 | 查询用户考试记录，含 `in_progress` 列表 |
| `start_exam.py` | `<exam_id>` | 开始新考试，返回 `attempt_id + questions` |
| `get_questions.py` | `<exam_id> <attempt_id>` | 获取题目和选项（含已保存答案） |
| `submit_exam.py` | `<exam_id> <attempt_id> '<answers_json>'` | 提交答案，返回成绩 |

---

## 已知限制

- **chrome-direct 独占**：此 Skill 依赖用户的真实 Chrome 登录态，不支持 stealth 或普通 chrome 浏览器
- **选项顺序随机**：每次 attempt 的 A/B/C/D 顺序不同，必须重新分析，不可复用旧答案
- **单次提交限制**：每个 attempt 只能提交一次；提交后如需重考，需新建 attempt（exam 重新开放时）
- **60分钟时效**：attempt 创建后 60 分钟内必须提交，否则自动过期

---

## 常见错误排查

| 错误 | 原因 | 解决 |
|------|------|------|
| `HAS_IN_PROGRESS_ATTEMPT` | 已有未完成的考试 | 用 `get_attempts.py` 找到 attempt_id，直接恢复 |
| `ALREADY_SUBMITTED` | attempt 已提交过 | 查看历史成绩，无需再提交 |
| `ATTEMPT_EXPIRED` | 超过 60 分钟 | 等考试重新开放，新建 attempt 重考 |
| `no_token` / 401 | 未登录或 token 失效 | 重新飞书登录 |
| 分数异常低 | 复用了旧 attempt 的答案映射 | 重新获取当前 attempt 的题目顺序再分析 |

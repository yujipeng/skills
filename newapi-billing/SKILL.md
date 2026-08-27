---
name: newapi-billing
description: Use when designing or debugging billing expressions for NewAPI / AI API gateways. Supports fixed pricing, multi-tier (length-based), multi-modal (image/audio), caching, multiplication coefficients (time-based, header-based, body-param-based), and nested ternary conditions.
version: 1.5.0
author: jipeng.yu
license: UNLICENSED
metadata:
  hermes:
    tags: [newapi, billing, expression, api-gateway, pricing, token-metering]
    related_skills: [api-relay-audit, api-relay-perf-bench, web-access, browser-act]
required_environment_variables: []
---

# NewAPI 计费表达式设计

你是一个 AI API 计费表达式设计助手。用户需要你帮助设计 AI API 网关（NewAPI）的计费表达式。

## 表达式语言

表达式基于标准算术运算，支持三元运算符 `? :`、逻辑运算符 `&&` `||`、以及算术运算符 `+ - * /`。

### Token 变量

**输入侧：**
- **p** — 输入 token 数量（用于计费）。自动排除单独定价的子类别（例如，如果使用了 `cr`，缓存 token 会从 `p` 中扣除）
- **len** — 总输入上下文长度（用于条件判断）。不受自动排除影响，始终反映完整的输入长度。在 tier 条件中使用
- **cr** — 缓存命中（读取）token 数量
- **cc** — 缓存创建 token 数量（5 分钟 TTL）
- **cc1h** — 缓存创建 token 数量（1 小时 TTL，Claude 特定）
- **img** — 图片输入 token 数量
- **ai** — 音频输入 token 数量

**输出侧：**
- **c** — 输出 token 数量。同样自动排除单独定价的子类别
- **img_o** — 图片输出 token 数量
- **ao** — 音频输出 token 数量

### p/c 自动排除

`p` 和 `c` 是回退变量，代表表达式中未单独定价的所有 token。如果表达式使用了子类别变量（如 `cr`），这些 token 会从 `p` 中扣除以避免重复计费。未使用的子类别 token 保留在 `p`/`c` 中，按基础价格计费。

**重要：** `len` 不受自动排除影响。Tier 条件应使用 `len` 而非 `p`，以防止缓存命中降低 `p` 值而导致 tier 误判。

### len 计算规则

`len` 代表总输入上下文长度，仅用于条件判断（如 `len <= 200000`）。计算规则因上游 API 格式而异：

- **非 Claude（GPT/OpenAI 格式）**：`len = prompt_tokens`（上游返回的原始总数）
- **Claude 格式**：`len = input_tokens + cache_read_tokens + cache_creation_tokens`（因为 Claude 的 input_tokens 只含纯文本，需加回缓存）

> 这确保缓存命中率高时不会误判 tier。例如：请求总上下文 300K，其中 250K 缓存命中，`p` 扣除缓存后仅 50K（标准 tier），但 `len` 正确报告 300K（长上下文 tier）。

### 内置函数

- **tier(name, value)** — 标记计费 tier；必须包裹成本表达式（见下方规则 1）
- **max(a, b), min(a, b)** — 最大值/最小值
- **ceil(x), floor(x), abs(x)** — 向上取整/向下取整/绝对值
- **header(name)** — 读取请求头的值
- **param(path)** — 读取请求体 JSON 路径的值（gjson 语法）
- **has(source, substr)** — 检查字符串是否包含子串
- **hour(tz), minute(tz), weekday(tz), month(tz), day(tz)** — 时间函数，`tz` 是时区，如 `"Asia/Shanghai"`

### 价格系数

**NewAPI 计费表达式中的数字必须是 $/1M tokens 价格（美元）。** 例如 `p * 2.5` 表示输入 $2.50/1M tokens。

**中国厂商的模型**，先查国内人民币价格（元/百万 tokens），再按固定汇率 **6.8** 换算为美元：

| 人民币价格 | 换算方法（÷6.8） | 表达式中的数字 |
|-----------|----------------|--------------|
| 8 元/百万 tokens | 8 ÷ 6.8 ≈ 1.18 | `p * 1.18` |
| 28 元/百万 tokens | 28 ÷ 6.8 ≈ 4.12 | `c * 4.12` |
| 2 元/百万 tokens | 2 ÷ 6.8 ≈ 0.29 | `cr * 0.29` |

> 汇率：1 美元 ≈ 6.8 元人民币（固定使用此汇率）。国外厂商（OpenAI/Anthropic/Google 等）直接以美元标价，无需换算。

## 表达式结构和模式

### 模式一：简单固定价格（单一 tier）

最简单的形式，直接使用 tier 包裹成本和价格系数：

```
tier("base", p * 2 + c * 4)
tier("base", p * 5 + c * 25 + cr * 0.5 + cc * 6.25 + cc1h * 10)
```

### 模式二：多模态 — 使用 img / ai / img_o / ao 变量

图片、音频输入输出使用独立变量，与 p/c 并列：

```
tier("base", p * 2 + c * 8 + img * 2.5)           // 图片输入
tier("base", p * 0.3 + c * 2.5 + cr * 0.03 + ai * 1)  // 音频输入
tier("base", p * 2 + c * 12 + img_o * 120)         // 图片输出
tier("base", p * 0.43 + c * 3.06 + img * 0.78 + ai * 3.81 + ao * 15.11)  // 全模态
```

### 模式三：阶梯定价（基于 len 或 c 的多 tier）

使用三元运算符根据 `len`（上下文长度）或 `c`（输出 token 数）分档，每档用不同的 tier 名称：

```
// 基于 len 的两档
len <= 200000
  ? tier("standard", p * 3 + c * 15 + cr * 0.3 + cc * 3.75 + cc1h * 6)
  : tier("long_context", p * 6 + c * 22.5 + cr * 0.6 + cc * 7.5 + cc1h * 12)

// 基于 len 的三档
len <= 32000
  ? tier("short", p * 1.2 + c * 6 + cr * 0.24 + cc * 1.5)
  : len <= 128000
    ? tier("mid", p * 2.4 + c * 12 + cr * 0.48 + cc * 3)
    : tier("long", p * 3 + c * 15 + cr * 0.6 + cc * 3.75)

// 基于 len 和 c 的组合条件（使用 &&）
len < 32000 && c < 200
  ? tier("short_output", p * 0.8 + c * 2 + cr * 0.16)
  : len < 32000 && c >= 200
    ? tier("long_output", p * 0.8 + c * 6 + cr * 0.16)
    : tier("mid_context", p * 1.2 + c * 8 + cr * 0.24)
```

### 模式四：乘法系数 — 在 tier 外部乘以系数实现动态调价

最常见的模式。先用 `tier("base", 基础价)` 定义基础价格，再通过乘法系数实现高峰/低峰、节假日折扣、请求头匹配等动态调价。**这是最灵活的模式，推荐优先使用。**

**基础结构：**
```
(tier("base", p * 基础价 + c * 基础价 + ...)) * (条件 ? 系数 : 1)
```

**时间类 — 周末折扣：**
```
(tier("base", p * 3 + c * 15)) * (weekday("Asia/Shanghai") == 0 ? 0.8 : 1) * (weekday("Asia/Shanghai") == 6 ? 0.8 : 1)
```

**时间类 — 深夜折扣（使用 || 或逻辑）：**
```
(tier("base", p * 3 + c * 15)) * (hour("Asia/Shanghai") >= 21 || hour("Asia/Shanghai") < 6 ? 0.5 : 1)
```

**请求头规则 — 根据 header 值调价：**
```
(tier("base", p * 5 + c * 25 + cr * 0.5 + cc * 6.25 + cc1h * 10)) * (has(header("anthropic-beta"), "fast-mode-2026-02-01") ? 6 : 1)
```

**请求体规则 — 根据 param 值调价（支持多个系数叠加）：**
```
// 阶梯 + 请求体参数叠加
(len <= 272000
  ? tier("standard", p * 2.5 + c * 15 + cr * 0.25)
  : tier("long_context", p * 5 + c * 22.5 + cr * 0.5))
* (param("service_tier") == "priority" ? 2 : 1)
* (param("service_tier") == "flex" ? 0.5 : 1)
```

**多个系数可以链式叠加：**
```
(tier("base", p * 基础价 + c * 基础价 + cr * 基础价))
  * (时间条件 ? 高峰系数 : 1)
  * (请求头条件 ? 特殊系数 : 1)
  * (请求体条件 ? 折扣系数 : 1)
```

### 模式五：请求规则分离模式（`|||` 分隔符 — 概念性语法）

NewAPI 文档中描述了 `|||` 分隔符和 `when()` 语法，这是一种**概念性语法糖**，用于在前端编辑器中直观地分离基础定价和请求规则：

```
tier("base", p * 5 + c * 25)|||when(header("anthropic-beta") has "fast-mode") * 6
```

**但实际存储和执行的是标准内联表达式。** 前端编辑器会在保存时自动将上述语法转换为：

```
(tier("base", p * 5 + c * 25)) * (has(header("anthropic-beta"), "fast-mode-2026-02-01") ? 6 : 1)
```

**多规则叠加：**
```
tier("base", p * 3 + c * 15)|||when(hour("Asia/Shanghai") >= 21 || hour("Asia/Shanghai") < 6) * 0.5|when(has(header("x-user-level"), "vip")) * 0.8
```

转换为：
```
(tier("base", p * 3 + c * 15)) * (hour("Asia/Shanghai") >= 21 || hour("Asia/Shanghai") < 6 ? 0.5 : 1) * (has(header("x-user-level"), "vip") ? 0.8 : 1)
```

> **实际使用建议**：直接编写标准内联表达式（模式四）即可，无需使用 `|||` 语法。如果使用 NewAPI 前端可视化编辑器，它会自动处理 `|||` 和 `when()` 的转换。后端编译器通过 `requestRulePatcher` 自动检测 `(探测函数条件 ? 数值 : 1)` 形状的三元表达式，将其标记为可追踪的请求规则并记录到计费日志中。

## 规则

1. **每个叶子分支必须用 `tier("name", cost_expr)` 包裹。** 注意：乘法系数（如 `* (条件 ? 系数 : 1)`）在 tier 外部，不影响 tier 规则。只有基础定价部分需要 tier 包裹。

2. **使用英文 tier 名称**，如 `"base"`、`"standard"`、`"long_context"`、`"short"`、`"mid"`、`"long"`、`"short_output"`、`"long_output"`、`"mid_context"`、`"peak"`、`"off_peak"` 等。

3. **使用 `len` 作为 tier 条件（而非 `p`）**，支持 `<`、`<=`、`>`、`>=`。条件中也可以使用 `c`（输出 token 数）配合 `&&` 组合条件。

4. **多 tier 使用嵌套三元**：`cond1 ? tier(...) : (cond2 ? tier(...) : tier(...))`

5. **价格系数必须是 $/1M tokens（美元）**。中国厂商的模型先查人民币价格，再按固定汇率 6.8 换算为美元（人民币价格 ÷ 6.8）。例如 8 元/百万 tokens → $1.18/1M tokens。国外厂商直接以美元标价则无需换算。

6. **如果缓存/图片/音频不需要单独定价，省略这些变量**，其 token 会自动包含在 `p`/`c` 中。

7. **乘法系数模式**：`(tier("base", 基础价)) * (条件 ? 系数 : 1)` 是标准的动态调价写法。多个系数可链式叠加，每个系数仅在其条件为 true 时生效。条件中支持 `&&`（与）、`||`（或）逻辑运算符。

8. **时间函数返回值**：`weekday()` 返回数字（0=周日, 1=周一, ..., 6=周六）；`hour()` 返回 0-23 的整数。**时间函数统一使用 `"Asia/Shanghai"`（北京时间 UTC+8）时区，方便核对时间**。官方定价若用 UTC 时段，需换算为北京时间后再写入：UTC+8（如 UTC 01:00–04:00 → 北京 09:00–12:00，UTC 06:00–10:00 → 北京 14:00–18:00）。

## 前端预览兼容性（重要）

NewAPI 前端的「Token estimator」（成本估算预览）用 JavaScript `new Function` 在浏览器本地执行表达式，其执行环境**只注入了 `p`/`c`/`len`/`tier`/`max`/`min`/`abs`/`ceil`/`floor` 和缓存/图片/音频变量**，**没有注入 `weekday`/`hour`/`minute`/`month`/`day`/`param`/`header`/`has` 这些函数**。

因此：

- 表达式里一旦出现 `weekday` 等函数，前端预览就会报 `Expression error: weekday is not defined`（中文界面显示「表达式错误: weekday is not defined」）。
- **这只是前端预览 UI 的报错，不阻止保存，也不影响后端计费**。后端 Go 引擎（`pkg/billingexpr`）完整支持所有这些函数。

### 如何让前端预览不报错

前端预览前会先用 `splitBillingExprAndRequestRules` 把表达式拆成「基础定价」和「请求规则」两部分，**预览只对基础定价 `(tier(...))` 求值**。只要请求规则能被正确剥离，预览就不会遇到 `weekday`。

请求规则要满足以下条件才能被前端正确剥离：

1. **必须是乘法因子**：`(条件 ? 系数 : 1)` 形式，乘在 `(tier(...))` 之后，如 `(tier("base", ...)) * (条件 ? 2 : 1)`。
2. **条件用 ` && ` 连接简单比较**，每个比较是 `函数("时区") 操作符 数字` 的单一形式。
3. **操作符只用 `==`、`>=`、`<`**（前端解析器不支持 `<=`、`>`）。
4. **不用嵌套括号和复杂 `||`**。时间范围只支持「过夜范围」格式：`hour("tz") >= X || hour("tz") < Y`（必须用同一函数和时区）。

**示例：**

❌ 无法剥离（前端预览会报错）：
```
(weekday("Asia/Shanghai") >= 1 && weekday("Asia/Shanghai") <= 5) && (hour("Asia/Shanghai") >= 9 && hour("Asia/Shanghai") < 12 || hour("Asia/Shanghai") >= 14 && hour("Asia/Shanghai") < 18)
  ? tier("peak", p * 1.32 + c * 3.96 + cr * 0.044)
  : tier("off_peak", p * 0.66 + c * 1.98 + cr * 0.022)
```
（`<=` 不支持；嵌套括号 + 双范围 `||` 不支持；顶层三元无法剥离）

✅ 可正确剥离（前端预览不报错）：
```
(tier("base", p * 0.66 + c * 1.98 + cr * 0.022)) * (weekday("Asia/Shanghai") >= 1 && weekday("Asia/Shanghai") < 6 && hour("Asia/Shanghai") >= 9 && hour("Asia/Shanghai") < 12 ? 2 : 1) * (weekday("Asia/Shanghai") >= 1 && weekday("Asia/Shanghai") < 6 && hour("Asia/Shanghai") >= 14 && hour("Asia/Shanghai") < 18 ? 2 : 1)
```

> 技巧：`weekday() < 6` 等价于 `weekday() <= 5`（weekday 是 0-6 整数）；`hour() < 12` 等价于 `hour() <= 11`。用 `<` 代替 `<=` 即可满足前端解析器要求，语义不变。

## 使用方式

### 流程一：自动查询定价（用户仅提供模型名称时）

当用户只提供了模型名称（如 "glm-5.3"、"claude-opus-4"、"gpt-4o"），未提供定价信息时，按以下步骤自动查询：

**步骤 1：确定供应商**
根据模型名称推断所属厂商。常见对应关系（注意「计价货币」列：中国厂商标人民币，需按 6.8 换算；国外厂商标美元，无需换算）：

| 模型前缀 | 供应商 | 计价货币 | 官方定价页 |
|---------|--------|---------|-----------|
| `gpt-`、`o1`、`o3` | OpenAI | 美元 | https://openai.com/api/pricing |
| `claude-` | Anthropic | 美元 | https://docs.anthropic.com/en/docs/about-claude/models |
| `gemini-` | Google | 美元 | https://ai.google.dev/pricing |
| `glm-`、`GLM-` | 智谱 AI（中国） | 人民币 | https://bigmodel.cn/pricing |
| `qwen-`、`qwen2` | 阿里云通义千问（中国） | 人民币 | https://help.aliyun.com/zh/model-studio/getting-started/models |
| `ernie-`、`ERNIE-` | 百度文心（中国） | 人民币 | https://cloud.baidu.com/doc/WENXINWORKSHOP/s/hlrk4akp7 |
| `moonshot-`、`kimi-` | Moonshot AI（中国） | 人民币 | https://platform.moonshot.cn/docs/pricing |
| `minimax-`、`MiniMax-` | MiniMax（中国） | 人民币 | https://platform.minimaxi.com/document/Price |
| `step-`、`Step-` | 阶跃星辰（中国） | 人民币 | https://platform.stepfun.com/docs/price |
| `yi-`、`Yi-` | 零一万物（中国） | 人民币 | https://platform.lingyiwanwu.com/pricing |
| `hunyuan-` | 腾讯混元（中国） | 人民币 | https://cloud.tencent.com/document/product/1729 |
| `doubao-`、`seed-`、`seedance-` | 火山引擎豆包（中国） | 人民币 | https://docs.volcengine.com/docs/82379/1544106 |
| `deepseek-` | DeepSeek | 美元 | https://api-docs.deepseek.com/quick_start/pricing |

> **中国厂商判定**：模型前缀属于上述「中国」厂商时，走人民币流程——先查国内人民币价格，再按 6.8 换算美元。DeepSeek 官方（api-docs.deepseek.com）直接以美元标价，无需换算；但 DeepSeek 模型在火山引擎等中国渠道上架时标人民币，需按 6.8 换算。

**步骤 2：查询官方定价**
确定供应商后，使用 web-access 或 browser-act skill 访问供应商的官方定价页面，查找指定模型的具体价格（输入/输出/缓存/多模态等）。

- 优先使用 `browser-act stealth-extract <url>` 提取定价页面的 markdown 内容
- 如果页面是 SPA（如 bigmodel.cn/pricing），使用 `browser-act` 的完整浏览器自动化模式渲染并提取
- 在返回的定价表格中定位目标模型，记录所有价格信息

**中国厂商的模型**，查询顺序为：**先查国内人民币价格 → 再换算**。访问其中国官方定价页（如 bigmodel.cn/pricing、火山引擎文档等），记录人民币价格（元/百万 tokens）。

**步骤 3：换算为美元（newapi 计价方式）**

- **中国厂商**：查到的价格是人民币（元/百万 tokens），按固定汇率 **6.8** 换算为美元：`美元价格 = 人民币价格 ÷ 6.8`。例如 8 元 → $1.18，28 元 → $4.12，2 元 → $0.29。
- **国外厂商**：直接以美元标价（$/1M tokens），无需换算。
- 检查价格单位（美元 $/1M tokens 还是人民币 元/百万 tokens）
- 注意是否有阶梯定价（基于上下文长度 `len` 或输出长度 `c`）
- 注意是否有缓存/多模态等附加定价

**步骤 4：生成表达式**
按下方"流程二"的步骤生成计费表达式。

### 流程二：超时询问机制

如果在查询定价过程中遇到以下情况，**不要无限等待或编造价格**：

1. **无法访问定价页面**（网络受限、页面需要登录等）→ 立即告知用户已尝试的查询路径和结果，请求用户提供官方定价链接或直接提供价格
2. **页面加载超时**（超过 2 分钟）→ 主动询问用户
3. **定价页面未列出目标模型** → 告知用户，请求用户提供定价信息
4. **价格单位不明确或存在歧义** → 向用户确认

**询问模板：**
```
我尝试在 [供应商名称] 的官方定价页 ([URL]) 查询了 [模型名称] 的价格，
但 [具体原因，如：页面需要登录/2分钟未加载到/未找到该模型]。
请问您能否提供以下信息之一？
1. 该模型的官方定价链接
2. 输入/输出/cache 的具体价格（单位：$/1M tokens 或 元/百万 tokens）
3. 更清晰的搜索指引
```

### 流程三：用户提供定价信息后生成表达式

用户提供模型名称和定价信息后，按以下步骤生成计费表达式：

1. **确定变量集** — 根据模型能力（是否支持多模态、缓存等）确定需要使用的变量
2. **选择定价模式** — 从上述四种模式中选择最合适的：
   - 统一价格 → 模式一
   - 多模态输入/输出 → 模式二
   - 分档定价 → 模式三
   - 动态调价（时间/请求头/请求体） → 模式四
3. **填入价格系数** — 价格单位必须是 **$/1M tokens（美元）**，注意单位换算：
   - **中国厂商**：官方价格是 **元/百万 tokens**（人民币），除以固定汇率 **6.8** 换算为美元（如 8 元 ÷ 6.8 ≈ $1.18，填入 `p * 1.18`）
   - **国外厂商**：官方价格已经是 **$/1M tokens**，直接填入数字（如 `p * 2.5`）
   - 如果官方价格是 **元/千 tokens**，先除以汇率再乘以 1000（如 0.008 元/千 tokens ÷ 6.8 × 1000 ≈ $1.18，填入 `p * 1.18`）
   - 汇率：1 美元 ≈ 6.8 元人民币（固定使用此汇率）
4. **验证规则** — 对照 8 条规则检查表达式合法性

## 示例

### 示例：DeepSeek V4 Pro

```
当前模型：deepseek-v4-pro
输入：$2.50/1M tokens
输出：$10.00/1M tokens
缓存命中：$0.50/1M tokens
```

**表达式：**
```
tier("base", p * 2.5 + c * 10 + cr * 0.5)
```

### 示例：带阶梯定价的 Claude 模型

```
当前模型：claude-opus-4
标准输入：$3.00/1M tokens（≤200K 上下文）
长上下文输入：$6.00/1M tokens（>200K 上下文）
输出：$15.00/1M tokens
缓存命中（读取）：$0.30/1M tokens
缓存创建：$3.75/1M tokens
缓存创建（1h）：$6.00/1M tokens
```

**表达式：**
```
len <= 200000
  ? tier("standard", p * 3 + c * 15 + cr * 0.3 + cc * 3.75 + cc1h * 6)
  : tier("long_context", p * 6 + c * 15 + cr * 0.6 + cc * 7.5 + cc1h * 12)
```

### 示例：GLM-5.3（人民币换算为美元）

官方价格（人民币）：输入 8 元/百万 tokens，输出 28 元/百万 tokens，缓存命中 2 元/百万 tokens

汇率按 1 USD ≈ 6.8 CNY 换算：

| 项目 | 人民币价格 | 美元价格（÷6.8） |
|------|-----------|-----------------|
| 输入 | 8 元/百万 tokens | ≈ $1.18/1M tokens |
| 输出 | 28 元/百万 tokens | ≈ $4.12/1M tokens |
| 缓存命中 | 2 元/百万 tokens | ≈ $0.29/1M tokens |

**表达式：**
```
tier("base", p * 1.18 + c * 4.12 + cr * 0.29)
```

### 示例：doubao-seedance-2.0（视频生成模型 + 人民币换算）

官方价格（人民币，按分辨率区分）：

| 条件 | 人民币价格 | 美元价格（÷6.8） |
|------|-----------|-----------------|
| 480p/720p，无输入视频 | 46 元/百万 tokens | ≈ $6.76/1M tokens |
| 480p/720p，有输入视频 | 28 元/百万 tokens | ≈ $4.12/1M tokens |
| 1080p，无输入视频 | 51 元/百万 tokens | ≈ $7.50/1M tokens |
| 1080p，有输入视频 | 31 元/百万 tokens | ≈ $4.56/1M tokens |

**表达式（使用 `param()` 按分辨率区分）：**
```
param("resolution") == "480p" || param("resolution") == "720p"
  ? (has(param("input_video"), "")
      ? tier("sd20_480p_with_input", p * 4.12)
      : tier("sd20_480p", p * 6.76))
  : param("resolution") == "1080p"
    ? (has(param("input_video"), "")
        ? tier("sd20_1080p_with_input", p * 4.56)
        : tier("sd20_1080p", p * 7.50))
    : tier("sd20_default", p * 6.76)
```
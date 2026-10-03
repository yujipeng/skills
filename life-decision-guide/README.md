# life-decision-guide

让 AI 助手照《高性价比人生指南》回答具体问题：该不该做、值不值、怎么选、出事了先做什么、能领哪笔钱、这么干犯不犯法。

它做的事只有一件：**先把相关条目从正文里查出来，再照书的算账方式排序回答**，每条注明出自第几节第几条。查不到就说查不到，不凭记忆编数字。

## 来源与许可证

- 规则文件（`SKILL.md` 正文）逐字取自 [eternity4719/HowToLiveBetter](https://github.com/eternity4719/HowToLiveBetter) 的 `skills/life-decision-guide/`，未作改动；只有 YAML frontmatter 按本仓库 `AGENTS.md` 的规范补齐（`version` / `author` / `license` / `metadata.hermes` / `required_environment_variables`）。
- 上游作者 eternity4719。正文著作权归上游：《高性价比人生指南》文字部分为 **CC BY 4.0**，仓库代码部分为 **MIT**。本目录按 CC BY 4.0 标注，署名保留在上面的 frontmatter 与本节。
- 与上游同步时：只替换 `SKILL.md` 第 1 个 `---` 到第 2 个 `---` 之间的 frontmatter 之外的部分，保留本目录补齐的 frontmatter。

## 安装

放在本仓库里直接可用（本仓库根目录即 skills 集合）。想让全局生效，按所用工具复制或软链过去：

```bash
# Claude Code
mkdir -p ~/.claude/skills/life-decision-guide
cp life-decision-guide/SKILL.md ~/.claude/skills/life-decision-guide/SKILL.md

# Codex：用斜杠命令 /life-decision-guide 调用
mkdir -p ~/.codex/prompts
cp life-decision-guide/SKILL.md ~/.codex/prompts/life-decision-guide.md
```

## 正文从哪来

本 skill 只带规则，不带正文；回答时现取《高性价比人生指南》：

```bash
# 本地已有该仓库就读本地的 book/
git clone --depth 1 https://github.com/eternity4719/HowToLiveBetter.git "${TMPDIR:-/tmp}/hltb"
```

整本约 1.3 MB，浅克隆一次几秒。取不到网络就如实说取不到，不替代正文。

## 运行时要求

无环境变量、无脚本、无第三方依赖。只需要能读文件或联网取正文的工具（Grep / Read / Bash 之类）。

## 改动须知

`SKILL.md` 里不留任何会跟着正文漂的清单和数值：节的清单去读上游 `README.md` 的「这本书想回答的问题」表，性价比档的算法去读上游 `index.html` 里的 `COST_W` 和 `e.ratio` 两行。所以上游增删节、改档位规则都不用动这个目录。

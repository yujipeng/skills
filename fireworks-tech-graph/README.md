[English](README.md) | [中文](README.zh.md)

# fireworks-tech-graph

> **Stop drawing diagrams by hand.** Describe your system in English or Chinese — get publication-ready SVG + PNG technical diagrams in seconds.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-10a37f)](https://learn.chatgpt.com/docs/build-skills)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-d97757)](https://code.claude.com/docs/en/skills)
[![8 Visual Styles](https://img.shields.io/badge/Styles-8-purple)]()
[![14 Diagram Types](https://img.shields.io/badge/Diagram%20Types-14-green)]()
[![UML Support](https://img.shields.io/badge/UML-Full%20Support-orange)]()

---

## Overview

`fireworks-tech-graph` is one Agent Skill that works unchanged in **Codex and Claude Code**. It turns natural language descriptions into polished SVG diagrams, then exports them as high-resolution PNG via `cairosvg` (recommended), with `rsvg-convert` and `puppeteer` available as alternatives. It ships with **7 template styles** and **1 AI-authored style (Dark Luxury)** and deep knowledge of AI/Agent domain patterns (RAG, Agentic Search, Mem0, Multi-Agent, Tool Call flows), plus full support for all 14 UML diagram types.

```
User: "Generate a Mem0 memory architecture diagram, dark style"
  → Skill classifies: Memory Architecture Diagram, Style 2
  → Generates SVG with swim lanes, cylinders, semantic arrows
  → Exports 1920px PNG
  → Reports: mem0-architecture.svg / mem0-architecture.png
```

---

## Work With the Builder

This project is also a proof surface for a broader capability: turning vague AI/devtool workflows into constrained, reusable systems with validation, documentation, export paths, and product-facing polish.

If you are building agent infrastructure, AI IDEs, internal copilots, developer tools, technical documentation systems, or applied AI workflow products, I am open to scoped paid sprints, design-partner work, and founding engineer conversations.

- Founder-facing profile: https://bradzhang.dev/en
- Commercial case study: https://bradzhang.dev/en/case-studies/fireworks-tech-graph
- Work with me: https://bradzhang.dev/en/work-with-me

---

## Showcase

> All samples are exported at 1920px width (2× retina) by the regression pipeline. It prefers `cairosvg` and falls back to `rsvg-convert`. PNG keeps technical text and line work lossless.

### Style 1 — Flat Icon (default)
*Mem0 Memory Architecture — white background, semantic arrows, layered memory system*
![Style 1 — Flat Icon](assets/samples/sample-style1-flat.png)

### Style 2 — Dark Terminal
*Tool Call Flow — dark background, neon accents, monospace font*
![Style 2 — Dark Terminal](assets/samples/sample-style2-dark.png)

### Style 3 — Blueprint
*Microservices Architecture — deep blue background, grid lines, cyan strokes*
![Style 3 — Blueprint](assets/samples/sample-style3-blueprint.png)

### Style 4 — Notion Clean
*Agent Memory Types — minimal white, single accent color*
![Style 4 — Notion Clean](assets/samples/sample-style4-notion.png)

### Style 5 — Glassmorphism
*Multi-Agent Collaboration — dark gradient background, frosted glass cards*
![Style 5 — Glassmorphism](assets/samples/sample-style5-glass.png)

### Style 6 — Claude Official
*System Architecture — warm cream background (#f8f6f3), Anthropic brand colors, clean professional aesthetic*
![Style 6 — Claude Official](assets/samples/sample-style6-claude.png)

### Style 7 — OpenAI Official
*API Integration Flow — pure white background, OpenAI brand palette, modern minimalist design*
![Style 7 — OpenAI Official](assets/samples/sample-style7-openai.png)

### Style 8 — Dark Luxury *(AI-authored)*
*Agent Runtime Architecture — control plane, execution and state layers, champagne-gold structure, semantic color buckets*
![Style 8 — Dark Luxury](assets/samples/sample-style8-dark-luxury.png)

---

## Stable Prompt Recipes

Use prompts like these when you want the model to stay close to the repo's strongest regression-tested outputs:

### Style 1 — Flat Icon
```text
Draw a Mem0 memory architecture diagram in style 1 (Flat Icon).
Use four horizontal sections: Input Layer, Memory Manager, Storage Layer, Output / Retrieval.
Include User, AI App / Agent, LLM, mem0 Client, Memory Manager, Vector Store, Graph DB, Key-Value Store, History Store, Context Builder, Ranked Results, Personalized Response.
Use semantic arrows for read, write, control, and data flow. Keep the layout clean and product-doc friendly.
```

### Style 2 — Dark Terminal
```text
Draw a tool call flow diagram in style 2 (Dark Terminal).
Show User query, Retrieve chunks, Generate answer, Knowledge base, Agent, Terminal, Source documents, and Grounded answer.
Use terminal chrome, neon accents, monospace typography, and semantic arrows for retrieval, synthesis, and embedding update.
```

### Style 3 — Blueprint
```text
Draw a microservices architecture diagram in style 3 (Blueprint).
Create numbered engineering sections like 01 // EDGE, 02 // APPLICATION SERVICES, 03 // DATA + EVENT INFRA, 04 // OBSERVABILITY.
Include Client Apps, API Gateway, Auth / Policy, three services, Event Router, Postgres, Redis Cache, Warehouse, and Metrics / Traces.
Use blueprint grid, cyan strokes, and a bottom-right title block.
```

### Style 4 — Notion Clean
```text
Draw an agent memory types diagram in style 4 (Notion Clean).
Compare Sensory Memory, Working Memory, Episodic Memory, Semantic Memory, and Procedural Memory around a central Agent core.
Use a minimal white layout, neutral borders, one accent color for arrows, and short storage tags for each memory type.
```

### Style 5 — Glassmorphism
```text
Draw a multi-agent collaboration diagram in style 5 (Glassmorphism).
Use three sections: Mission Control, Specialist Agents, and Synthesis.
Include User brief, Coordinator Agent, Research Agent, Coding Agent, Review Agent, Shared Memory, Synthesis Engine, and Final response.
Use frosted cards, soft glow, and semantic arrows for delegation, shared memory writes, and synthesis output.
```

### Style 6 — Claude Official
```text
Draw a system architecture diagram in style 6 (Claude Official).
Use left-side layer labels: Interface Layer, Core Layer, Foundation Layer.
Include Client Surface, Gateway, Task Planner, Model Runtime, Policy Guardrails, Memory Store, Tool Runtime, Observability, and Registry.
Use warm cream background, restrained brand-like palette, generous whitespace, and a bottom-right legend.
```

### Style 7 — OpenAI Official
```text
Draw an API integration flow diagram in style 7 (OpenAI Official).
Use three sections: Entry, Model + Tools, and Delivery.
Include Application, OpenAI SDK Layer, Prompt Builder, Model Runtime, Tool Calls, Response Formatter, Observability, and Release Control.
Keep the look minimal, white, precise, and modern with clean green-accented arrows.
```

### Style 8 — Dark Luxury *(AI-authored)*
> Style 8 is not a template-driven style. The AI reads `references/style-8-dark-luxury.md` and hand-crafts the SVG directly.

```text
Draw an Agent Runtime Architecture diagram in style 8 (Dark Luxury).
Use two sections: Control Plane and Execution and State.
Include Client, Gateway, Agent Runtime, Vector Memory, Tool Runtime, and Trace + Eval.
Use a deep black background (#0a0a0a), champagne gold (#d4a574) for titles and cluster labels,
and spread node colors across the full color wheel: emerald, violet, sky blue, rose, amber, cool-gray.
Apply Georgia serif only for the main title and section labels (≥11px); use sans-serif for all node text and arrow labels.
```

---

## Features

- **8 visual styles** — 7 template-driven (Flat Icon to OpenAI Official) + 1 AI-authored (Dark Luxury)
- **Executable style system** — style guides are encoded into the generator, not only documented in markdown
- **14 diagram types** — Full UML support (Class, Component, Deployment, Package, Composite Structure, Object, Use Case, Activity, State Machine, Sequence, Communication, Timing, Interaction Overview, ER Diagram) plus AI/Agent domain diagrams
- **AI/Agent domain patterns** — RAG, Agentic Search, Mem0, Multi-Agent, Tool Call, and more built-in
- **Semantic shape vocabulary** — LLM = double-border rect, Agent = hexagon, Vector Store = ringed cylinder
- **Semantic arrow system** — color + dash pattern encode meaning (write vs read vs async vs loop)
- **Structured SVG validation** — XML parsing, `marker-start/mid/end` integrity, and arrow-component collision checks for `M/L/H/V/Q/C/S/T` paths
- **Visual review gate** — exported PNGs are inspected for clipping, overlap, label placement, and routing regressions before delivery
- **Product icons** — 40+ products with brand colors: OpenAI, Anthropic, Pinecone, Weaviate, Kafka, PostgreSQL…
- **Swim lane grouping** — automatic layer labeling for complex architectures
- **SVG + PNG output** — SVG for editing, 1920px PNG for embedding
- **Renderer-friendly** — pure inline SVG, no external font fetching; renders cleanly in cairosvg, rsvg-convert, and headless Chrome

---

## Loop Engineering

The first render is treated as a candidate, not an automatic final result. `fireworks-tech-graph` uses an agent-driven, bounded validation feedback loop to move each diagram toward a verified deliverable:

```text
Prompt
  → Diagram Contract
  → Semantic IR
  → Style Spec
  → Route Planner
  → SVG Build
  → Structural Validation
  → PNG Visual Readback
  → Targeted Revision
  → Verified SVG + PNG
```

The loop follows five design principles:

1. **Evaluate, don't assert** — completion is backed by validator and render evidence, not by the model saying the diagram looks correct.
2. **Deterministic checks first** — XML structure, marker integrity, path geometry, arrow-component collisions, and renderability are checked before visual judgment.
3. **Perceptual validation second** — the exported PNG is read back to inspect clipping, label collisions, hierarchy, whitespace, and routing quality that syntax checks cannot see.
4. **Targeted correction** — each pass changes only the diagnosed labels, coordinates, corridors, or spacing, then reruns validation and rendering.
5. **Bounded convergence** — visual review allows at most two focused correction passes by default, preventing an unbounded self-editing loop.

The loop is observable in the final status:

```text
validation: passed
visual_review: passed
```

If the runtime cannot read images, the skill reports `visual_review: skipped (image reader unavailable)` explicitly. The workflow remains bounded and auditable; it does not claim visual verification without image evidence.

---

## Installation

> [!WARNING]
> Some versions of `npx skills add` only copy `SKILL.md` and omit bundled directories such as `references/`, `scripts/`, and `templates/`. **Use `git clone` for a complete installation.**

The commands below are for a fresh install. If the destination already exists but is not a Git checkout, move it aside first, then run the matching clone command:

```bash
mv ~/.agents/skills/fireworks-tech-graph ~/.agents/skills/fireworks-tech-graph.backup-$(date +%Y%m%d-%H%M%S)
# or
mv ~/.claude/skills/fireworks-tech-graph ~/.claude/skills/fireworks-tech-graph.backup-$(date +%Y%m%d-%H%M%S)
```

### Codex

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/yizhiyanhua-ai/fireworks-tech-graph.git ~/.agents/skills/fireworks-tech-graph
```

Codex discovers personal skills from `~/.agents/skills` and reads the optional `agents/openai.yaml` metadata included in this repository.

### Claude Code

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/yizhiyanhua-ai/fireworks-tech-graph.git ~/.claude/skills/fireworks-tech-graph
```

Claude Code discovers personal skills from `~/.claude/skills` and ignores the Codex-only UI metadata.

### Codex + Claude Code on the same machine

For a fresh install with Claude Code 2.1.203 or newer, keep one checkout and link both discovery paths to it. Move any existing destinations aside before creating the links.

```bash
mkdir -p ~/.local/share/agent-skills ~/.agents/skills ~/.claude/skills
git clone https://github.com/yizhiyanhua-ai/fireworks-tech-graph.git ~/.local/share/agent-skills/fireworks-tech-graph
ln -s ~/.local/share/agent-skills/fireworks-tech-graph ~/.agents/skills/fireworks-tech-graph
ln -s ~/.local/share/agent-skills/fireworks-tech-graph ~/.claude/skills/fireworks-tech-graph
```

This keeps `SKILL.md`, references, scripts, templates, and future updates identical in both agents. The npm package page remains available for package metadata and distribution:

```text
https://www.npmjs.com/package/@yizhiyanhua-ai/fireworks-tech-graph
```

## Update

Update whichever checkout you installed:

```bash
git -C ~/.agents/skills/fireworks-tech-graph pull
# or
git -C ~/.claude/skills/fireworks-tech-graph pull
# or, for the shared checkout
git -C ~/.local/share/agent-skills/fireworks-tech-graph pull
```

After the first install, restart Codex and Claude Code so both discover the skill. Later `SKILL.md` edits are detected automatically; restart the runtime after changing bundled scripts or references if the update is not visible.

The shell commands above target macOS, Linux, WSL, and Git Bash. On native Windows, use the equivalent `%USERPROFILE%\.agents\skills` and `%USERPROFILE%\.claude\skills` paths.

---

## Requirements

The bundled validation/export scripts require **cairosvg** (recommended) or `rsvg-convert`. Puppeteer is an advanced manual conversion path documented in `SKILL.md`, not a fallback used by the bundled shell scripts.

```bash
# Recommended: cairosvg (best CSS support)
python3 -m pip install cairosvg

# Fallback: rsvg-convert (system package; may drop CSS / <foreignObject>)
brew install librsvg                   # macOS
sudo apt install librsvg2-bin          # Ubuntu/Debian

# Verify either supported script renderer
python3 -c "import cairosvg; print(cairosvg.__version__)"
rsvg-convert --version
```

| Renderer | Quality | Install Cost | Use When |
|----------|---------|--------------|----------|
| **cairosvg** | ✅ Good | Single `python3 -m pip install` | Default — best balance |
| rsvg-convert | ⚠️ Fair | System package | No Python available, simple flat diagrams |
| puppeteer | ✅✅ Best | Node + Chromium | Manual browser-rendering path for D3, Mermaid, or pixel-perfect output |

---

## Why Not Mermaid or draw.io?

| | Mermaid | draw.io | **fireworks-tech-graph** |
|--|---------|---------|--------------------------|
| Natural language input | ✗ | ✗ | ✅ |
| AI/Agent domain patterns | ✗ | ✗ | ✅ |
| Multiple visual styles | ✗ | manual | ✅ 8 built-in |
| High-res PNG export | ✗ | manual | ✅ auto 1920px |
| Semantic arrow colors | ✗ | manual | ✅ auto |
| No online tool needed | ✅ | ✗ | ✅ |

Mermaid is great for quick inline diagrams in markdown. draw.io is great for manual polishing. `fireworks-tech-graph` is optimized for **describing a system and getting a polished diagram immediately**, without writing DSL syntax or clicking around a GUI.

---

## Usage

### Trigger phrases

The skill auto-triggers on:

```
generate diagram / draw diagram / create chart / visualize
architecture diagram / flowchart / sequence diagram / data flow
```

### Basic usage

```
Draw a RAG pipeline flowchart
```

```
Generate an Agentic Search architecture diagram
```

### Specify style

```
Draw a microservices architecture diagram, style 2 (dark terminal)
```

```
Draw a multi-agent collaboration diagram --style glassmorphism
```

### Specify output path

```
Generate a Mem0 architecture diagram, output to ~/Desktop/
```

```
Create a tool call flow diagram --output /tmp/diagrams/
```

---

## Example Prompts by Scenario

### AI/Agent Systems

```
Compare Agentic RAG vs standard RAG in a feature matrix, Notion clean style
```
→ Comparison matrix: RAG vs Agentic RAG, covering retrieval strategy, agent loop, tool use

```
Generate a Mem0 memory architecture diagram with vector store, graph DB, KV store, and memory manager
```
→ Memory Architecture with swim lanes: Input → Memory Manager → Storage tiers → Retrieval

```
Draw a Multi-Agent diagram: Orchestrator dispatches 3 SubAgents (search / compute / code execution), results aggregated
```
→ Agent Architecture with hexagons, tool layers, and result aggregation

```
Visualize the Tool Call execution flow: LLM → Tool Selector → Execution → Parser → back to LLM
```
→ Flowchart with decision loop showing tool invocation cycle

```
Draw the 5 agent memory types: Sensory, Working, Episodic, Semantic, Procedural
```
→ Mind map or layered architecture showing memory tiers from sensory to procedural

### Infrastructure & Cloud

```
Draw a microservices architecture: Client → API Gateway → [User Service / Order Service / Payment Service] → PostgreSQL + Redis
```
→ Architecture diagram with horizontal layers, swim lanes per service cluster

```
Generate a data pipeline diagram: Kafka → Spark processing → write to S3 → Athena query
```
→ Data flow diagram with labeled arrows (stream / batch / query)

```
Draw a Kubernetes deployment: Ingress → Service → [Pod × 3] → ConfigMap + PersistentVolume
```
→ Architecture with dashed containers per namespace, solid arrows for traffic flow

### API & Sequence Flows

```
Draw an OAuth2 authorization code flow sequence diagram: User → Client → Auth Server → Resource Server
```
→ Sequence diagram with vertical lifelines and activation boxes

```
Draw the ChatGPT Plugin call sequence diagram
```
→ Sequence: User → ChatGPT → Plugin Manifest → API → Response chain

### Decision & Process Flows

```
Draw a pre-launch QA flowchart for an AI app: Code Review → Security Scan → Performance Test → Manual Approval → Deploy
```
→ Flowchart with diamond decision nodes and parallel branches

```
Generate a feature comparison matrix: RAG vs Fine-tuning vs Prompt Engineering
```
→ Comparison matrix with checked/unchecked cells across cost, latency, accuracy, flexibility

### Concept Maps

```
Visualize the LLM application tech stack: from foundation model to SDK to app framework to deployment
```
→ Layered architecture or mind map from model layer to product layer

```
Draw an AI Agent capability map: Perception / Memory / Reasoning / Action / Learning
```
→ Mind map with central "AI Agent" node and 5 radial branches

---

## Styles

| # | Name | Background | Font | Best For |
|---|------|-----------|------|----------|
| 1 | **Flat Icon** *(default)* | `#ffffff` | Helvetica | Blogs, slides, docs |
| 2 | **Dark Terminal** | `#0f0f1a` | SF Mono / Fira Code | GitHub README, dev articles |
| 3 | **Blueprint** | `#0a1628` | Courier New | Architecture docs, engineering |
| 4 | **Notion Clean** | `#ffffff` | system-ui | Notion, Confluence, wikis |
| 5 | **Glassmorphism** | `#0d1117` gradient | Inter | Product sites, keynotes |
| 6 | **Claude Official** | `#f8f6f3` | system-ui | Anthropic-style diagrams, warm aesthetic |
| 7 | **OpenAI Official** | `#ffffff` | system-ui | OpenAI-style diagrams, clean modern look |
| 8 | **Dark Luxury** *(AI-authored)* | `#0a0a0a` | Georgia + system-ui | Premium docs, README heroes, conference slides |

Each style has a dedicated reference file in `references/` with exact color tokens and SVG patterns. Styles 1-7 are generator-backed; Style 8 uses AI-authored composition plus a static regression fixture.
For Styles 1-7, the generator consumes structure fields such as `containers`, semantic `nodes[].kind`, `arrows[].flow`, and explicit port anchors so sample-grade layouts can be reproduced consistently.

Useful high-leverage fields for style-specific polish:
- `style_overrides` to nudge title alignment or palette tokens without forking a full style
- `containers[].header_prefix` / `containers[].header_text` for blueprint-style numbered section headers such as `01 // EDGE`
- `containers[].side_label` for Claude-style left layer labels
- `window_controls`, `meta_left`, `meta_center`, `meta_right` for terminal / document chrome
- `blueprint_title_block` for engineering title boxes in style 3

### Style Selection Guide

**For UML Diagrams:**
- **Class/Component/Package**: Style 1 (Flat Icon) or Style 4 (Notion Clean) — clear structure, easy to read
- **Sequence/Timing**: Style 2 (Dark Terminal) — monospace fonts help with alignment
- **State Machine/Activity**: Style 3 (Blueprint) — engineering aesthetic fits process flows
- **Use Case/Interview**: Style 1 (Flat Icon) — colorful, accessible

**For AI/Agent Diagrams:**
- **RAG/Agentic Search**: Style 2 (Dark Terminal) or Style 5 (Glassmorphism) — tech-forward aesthetic
- **Memory Architecture**: Style 3 (Blueprint) — emphasizes layered storage tiers
- **Multi-Agent**: Style 5 (Glassmorphism) — frosted cards distinguish agent boundaries

**For Documentation:**
- **Internal docs**: Style 4 (Notion Clean) — minimal, wiki-friendly
- **Blog posts**: Style 1 (Flat Icon) — colorful, engaging
- **GitHub README**: Style 2 (Dark Terminal) — matches dark theme
- **Presentations**: Style 5 (Glassmorphism) or Style 6 (Claude Official) — polished

**Brand-Specific:**
- **Anthropic/Claude projects**: Style 6 (Claude Official) — warm cream background, brand colors
- **OpenAI projects**: Style 7 (OpenAI Official) — clean white, OpenAI palette
- **Premium editorial diagrams**: Style 8 (Dark Luxury) — deep black canvas, champagne-gold hierarchy, semantic color buckets

---

## Diagram Types

| Type | Description | Key Layout Rule |
|------|-------------|-----------------|
| **Architecture** | Services, components, cloud infra | Horizontal layers top→bottom |
| **Data Flow** | What data moves where | Label every arrow with data type |
| **Flowchart** | Decisions, process steps | Diamond = decision, top→bottom |
| **Agent Architecture** | LLM + tools + memory | 5-layer model: Input/Agent/Memory/Tool/Output |
| **Memory Architecture** | Mem0, MemGPT-style | Separate read/write paths, memory tiers |
| **Sequence** | API call chains, time-ordered | Vertical lifelines, horizontal messages |
| **Comparison** | Feature matrix, side-by-side | Column = system, row = attribute |
| **Mind Map** | Concept maps, radial | Central node, bezier branches |

### UML Diagram Support (14 Types)

| UML Type | Description | Best Style |
|----------|-------------|------------|
| **Class Diagram** | Classes, attributes, methods, relationships | Style 1, 4 |
| **Component Diagram** | Software components and dependencies | Style 1, 3 |
| **Deployment Diagram** | Hardware nodes and software deployment | Style 3 |
| **Package Diagram** | Package organization and dependencies | Style 1, 4 |
| **Composite Structure** | Internal structure of classes/components | Style 1, 3 |
| **Object Diagram** | Object instances and relationships | Style 1, 4 |
| **Use Case Diagram** | Actors, use cases, system boundaries | Style 1 |
| **Activity Diagram** | Workflows, parallel processes | Style 3 |
| **State Machine** | State transitions and events | Style 2, 3 |
| **Sequence Diagram** | Message exchanges over time | Style 2 |
| **Communication Diagram** | Object interactions and messages | Style 1, 2 |
| **Timing Diagram** | State changes over time | Style 2 |
| **Interaction Overview** | High-level interaction flow | Style 1, 2 |
| **ER Diagram** | Entity-relationship data models | Style 1, 3 |

---

## AI/Agent Domain Patterns

Built-in pattern knowledge:

```
RAG Pipeline         → Query → Embed → VectorSearch → Retrieve → LLM → Response
Agentic RAG          → adds Agent loop + Tool use
Agentic Search       → Query → Planner → [Search/Calc/Code] → Synthesizer
Mem0 Memory Layer    → Input → Memory Manager → [VectorDB + GraphDB] → Context
Agent Memory Types   → Sensory → Working → Episodic → Semantic → Procedural
Multi-Agent          → Orchestrator → [SubAgent×N] → Aggregator → Output
Tool Call Flow       → LLM → Tool Selector → Execution → Parser → LLM (loop)
```

---

## Shape Vocabulary

Shapes encode semantic meaning consistently across all styles:

| Concept | Shape |
|---------|-------|
| User / Human | Circle + body |
| LLM / Model | Rounded rect, double border, ⚡ |
| Agent / Orchestrator | Hexagon |
| Memory (short-term) | Dashed-border rounded rect |
| Memory (long-term) | Solid cylinder |
| Vector Store | Cylinder with inner rings |
| Graph DB | 3-circle cluster |
| Tool / Function | Rect with ⚙ |
| API / Gateway | Hexagon (single border) |
| Queue / Stream | Horizontal pipe/tube |
| Document / File | Folded-corner rect |
| Browser / UI | Rect with 3-dot titlebar |
| Decision | Diamond |
| External Service | Dashed-border rect |

---

## Arrow Semantics

| Flow Type | Stroke | Dash | Meaning |
|-----------|--------|------|---------|
| Primary data flow | 2px solid | — | Main request/response |
| Control / trigger | 1.5px solid | — | System A triggers B |
| Memory read | 1.5px solid | — | Retrieve from store |
| Memory write | 1.5px | `5,3` | Write/store operation |
| Async / event | 1.5px | `4,2` | Non-blocking |
| Feedback / loop | 1.5px curved | — | Iterative reasoning |

---

## File Structure

```
fireworks-tech-graph/
├── SKILL.md                      # Main skill — diagram types, layout rules, shape vocab
├── README.md                     # This file (English)
├── README.zh.md                  # Chinese version
├── references/
│   ├── style-1-flat-icon.md      # White background, colored accents
│   ├── style-2-dark-terminal.md  # Dark bg, neon accents, monospace
│   ├── style-3-blueprint.md      # Blueprint grid, cyan lines
│   ├── style-4-notion-clean.md   # Minimal, white, single arrow color
│   ├── style-5-glassmorphism.md  # Dark gradient, frosted glass cards
│   ├── style-6-claude-official.md # Warm cream background, Anthropic brand
│   ├── style-7-openai.md         # Clean white, OpenAI brand palette
│   ├── style-8-dark-luxury.md    # Deep black, champagne gold, AI-authored layout
│   ├── png-export.md             # Renderer selection and manual export paths
│   └── icons.md                  # 40+ product icons + semantic shapes
├── agents/
│   └── openai.yaml              # Optional Codex UI metadata
├── fixtures/
│   ├── mem0-style1.json         # Style 1 regression fixture
│   ├── tool-call-style2.json    # Style 2 regression fixture
│   ├── dark-luxury-style8.svg   # Static Style 8 regression fixture
│   └── ...                      # Additional sample-grade fixtures per style
├── scripts/
│   ├── generate-diagram.sh       # Validate SVG + export PNG
│   ├── generate-from-template.py # Create starter SVGs from templates
│   ├── svg2png.js                 # High-fidelity Puppeteer exporter
│   ├── validate-svg.sh           # Validation and render-check entrypoint
│   ├── validate_svg.py           # XML, marker, transform, and path collision checks
│   └── test-all-styles.sh        # Batch test all styles
├── tests/
│   └── test_validate_svg.py      # Validator regression tests
├── assets/
│   └── samples/                  # Showcase diagram PNGs
├── templates/
│   ├── architecture.svg         # Architecture starter template
│   ├── data-flow.svg            # Data-flow starter template
│   └── ...                      # Additional diagram templates
└── agentloop-core.svg           # Included sample SVG
```

---

## Product Icon Coverage

**AI/ML:** OpenAI, Anthropic/Claude, Google Gemini, Meta LLaMA, Mistral, Cohere, Groq, Hugging Face

**AI Frameworks:** Mem0, LangChain, LlamaIndex, LangGraph, CrewAI, AutoGen, DSPy, Haystack

**Vector DBs:** Pinecone, Weaviate, Qdrant, Chroma, Milvus, pgvector, Faiss

**Databases:** PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch, Neo4j, Cassandra

**Messaging:** Kafka, RabbitMQ, NATS, Pulsar

**Cloud:** AWS, GCP, Azure, Cloudflare, Vercel, Docker, Kubernetes

**Observability:** Grafana, Prometheus, Datadog, LangSmith, Langfuse, Arize

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| PNG is blank or all-black | `@import url()` in SVG — neither cairosvg nor rsvg-convert can fetch external fonts | Remove `@import`, use system font stack |
| PNG not generated | No renderer installed | `python3 -m pip install cairosvg` (recommended), or `brew install librsvg` / `apt install librsvg2-bin` |
| Borders or text missing in PNG | Using `rsvg-convert` on SVG with CSS / `<foreignObject>` | Switch to `cairosvg` (`python3 -m pip install cairosvg`) — much better CSS support |
| Diagram cut off at bottom | ViewBox height too short | Increase `height` in `viewBox="0 0 960 <height>"` |
| Text overflowing boxes | Labels too long | Add `text-anchor="middle"` + `<clipPath>` or shorten label |
| Icons not rendering | External CDN URL | Use inline SVG paths from `references/icons.md` |
| Browser-generated SVG renders incorrectly | cairosvg / rsvg can't replay all CSS/JS-injected styles | Use `scripts/svg2png.js` as described in `references/png-export.md` |

---

## License

MIT © 2025 fireworks-tech-graph contributors

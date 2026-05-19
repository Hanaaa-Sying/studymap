# StudyMap — AI-Native 复习思维导图工具

## 项目简介

帮助大学生应对论述题为主的期末考试（政治学、社会学等）。
核心思路：用 AI 把课程知识结构化，同时沉淀高频答题话术，考试时快速定位知识位置 + 调取合适表达。

**两种模式：**
- **填充模式（Fill Mode）**：学期初建框架，学期中持续填充
- **复习模式（Review Mode）**：考前定位知识点、推荐话术

## 目录结构

```
studymap/
├── cli.py              # 入口
├── fill_mode/
│   ├── parser.py       # PDF / 大纲解析
│   ├── framework.py    # AI 生成知识框架
│   └── mubu_export.py  # 导出幕布兼容格式
├── review_mode/
│   ├── retriever.py    # 问题 → 知识节点定位
│   └── rhetoric.py     # 话术推荐
├── ai/
│   └── client.py       # LLM 抽象层（多 provider）
├── store/
│   └── schema.py       # 数据结构定义
├── data/               # 本地 JSON 存储
├── prompt-used.md      # 核心 Prompt 模板库（每次迭代后自动更新）
├── log.md              # 产品更新日志（每次迭代后自动追加）
└── plan.md             # 产品规划存档（仅开发规划阶段维护）
```

## 技术栈

- **语言**：Python 3.11+
- **AI（多 provider，可配置）**：
  - 默认：DeepSeek API（国内可用，兼容 OpenAI 格式）
  - 备选：豆包（Doubao）/ Claude（开发调试用）
  - `ai/client.py` 中的 `LLMClient` 统一抽象，配置文件切换 provider
- **PDF 解析**：pdfplumber
- **幕布集成**：生成幕布支持的大纲 Markdown 格式，用户手动导入
- **本地存储**：JSON 文件（MVP 阶段）

## 关键数据结构

```python
# KnowledgeNode
{ "id": str, "title": str, "summary": str, "content": str,
  "checked": bool, "parent_id": str, "rhetoric_ids": [str] }

# RhetoricEntry
{ "id": str, "text": str, "context": str, "source": str, "courses": [str] }
```

## 配置

```bash
export STUDYMAP_LLM_PROVIDER=deepseek   # deepseek | doubao | claude
export DEEPSEEK_API_KEY=sk-...
export DOUBAO_API_KEY=...
export ANTHROPIC_API_KEY=sk-ant-...     # 仅开发用
export STUDYMAP_DATA_DIR=./data
```

## 运行 CLI

```bash
python cli.py fill --pdf syllabus.pdf --course "Political Science 101"
python cli.py fill --update --course "Political Science 101"
python cli.py export --course "Political Science 101" --format mubu
python cli.py review --question "分析全球化对民族国家的冲击"
```

## 知识框架粒度约束

生成框架时 AI 必须遵守（详见 prompt-used.md）：
- 最多 3-4 层层级
- 每个节点标题 ≤ 10 字，名词短语
- 优先保留：理论名、学者名、核心命题、对比关系
- 过滤掉：章节编号、引言/结论文字、举例内容
- 目标节点数：整门课 50-80 个

## 项目文档规范

每次对话结束前，必须更新以下两个文件：

**`prompt-used.md`** — Prompt 模板库
- 新增或修改了任何 AI prompt → 追加或更新对应条目
- 每条结构：用途、模板正文、约束说明、更新历史（日期 + 修改原因）

**`log.md`** — 产品更新日志
- 每次迭代结束追加一个条目，格式：
  ```
  ## YYYY-MM-DD · vX.Y — 本次标题
  **新增** / **修复** / **变更** 分类列出
  ```
- 只记录对用户可见的功能变化，不记录内部重构细节

**`plan.md`** — 产品规划存档（仅开发规划阶段维护，功能迭代期不强制更新）

## GitHub 同步规范

仓库：`https://github.com/hanaaa-sying/studymap`

每次功能迭代完成后，在对话结束前执行：
```bash
git add -p          # 逐块确认，避免提交 key 或临时文件
git commit -m "描述本次变更"
git push origin main
```

**永远不要提交的内容**（已写入 `.gitignore`）：
- `data/` — 用户课程数据（含个人 PDF 内容）
- `.env` / `.env.*` — API Key
- `*.pdf` — 上传的 PDF 文件

## 当前阶段

MVP CLI：验证 PDF 解析 + AI 框架生成 + 话术提取三个核心能力

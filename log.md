# StudyMap 产品日志

---

## 2026-05-21 · v0.8 — 填充模式智能分支

**新增**
- 填充模式自动检测文件是否有目录（扫描前5页关键词和页码格式）
- 有目录 → 取前25页精细提取（50-80节点，4层）
- 无目录（论文/笔记/文献）→ 读全文略读（20-35节点，3层，聚焦主线）

---

## 2026-05-21 · v0.7 — 稳定性修复

**修复**
- 改为 job + polling 模式，解决复习模式 Railway 代理超时问题
- 用 fetch blob 方式下载文件，避免浏览器误下载 JSON 响应
- prompt 加"保留原文语言"规则，英文材料不再被翻译成中文

---

## 2026-05-21 · v0.6 — docx 支持 + 文件校验

**新增**
- 支持上传 Word (.docx) 文件，与 PDF 使用相同的两种模式
- 前端加 20MB 文件大小校验，超出时给出明确提示
- 后端同步校验文件大小（413 错误）

**变更**
- `fill_mode/parser.py` 新增 `extract_text_from_docx`、`extract_first_paras_docx`
- `server.py` 重构文件解析逻辑，统一支持 pdf/docx

---

## 2026-05-19 · v0.5 — 填充/复习模式分离

**新增**
- 填充模式：只解析 PDF 前 25 页（目录/章节），约 30 秒完成
- 复习模式：全文分块处理（每块 6000 字，50% 重叠），逐块提取话术后合并去重
- 网页新增模式选择 UI，含时间预估提示

**变更**
- `fill_mode/parser.py` 新增 `extract_first_pages()` 和 `chunk_text()`
- `fill_mode/framework.py` 改用页面级别控制，不再按字符截断
- `review_mode/rhetoric.py` 新增 `extract_rhetoric_chunked()`
- `server.py` 新增 `mode` 参数（fill / review）

---

## 2026-05-19 · v0.4 — 导出序号格式

**变更**
- 导出大纲新增层级序号：一级用 `1`，二级用 `1.1`，三级用 `1.1.1`，四级用 `1）`

---

## 2026-05-19 · v0.3 — 部署上线

**新增**
- Procfile：Railway 部署配置
- 公开地址：https://web-production-1cf24.up.railway.app
- 代码托管：https://github.com/Hanaaa-Sying/studymap

---

## 2026-05-19 · v0.2 — Web 界面

**新增**
- `server.py`：FastAPI 后端，`POST /generate` 接收 PDF + 课程名，返回幕布 .md 文件下载
- `static/index.html`：单页前端，支持拖拽上传 PDF，生成完成后自动下载
- 依赖新增：fastapi、uvicorn、python-multipart

---

## 2026-05-19 · v0.1 — MVP CLI 初始版本

**新增**
- 项目基础结构搭建（`cli.py`, `ai/`, `fill_mode/`, `review_mode/`, `store/`）
- 填充模式：从 PDF 提取文本 → DeepSeek 生成知识框架 → 本地 JSON 存储
- 话术提取：从课程材料中识别高频答题表达
- 导出幕布格式：生成层级 Markdown，支持手动导入幕布
- 复习模式：论述题 → 相关知识节点定位 + 话术推荐
- 多 provider 支持：DeepSeek（默认）/ 豆包 / Claude

**修复**
- 修复 `cli.py` 中错误引用 `fill_mode.rhetoric` 的 import
- 修复幕布导出使用 Tab 缩进导致层级丢失，改为 2 空格缩进

**已知问题**
- 仅支持 CLI，尚无 Web 界面
- DeepSeek 生成的框架质量依赖 prompt，需持续调优

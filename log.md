# StudyMap 产品日志

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

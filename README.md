# TrustLens AI - 合同审核助手

> 规则驱动、证据可溯源、基于 RAG 的合同智能审查系统

## 项目简介

TrustLens 是一个 AI 合同审核助手，通过规则驱动和 RAG 技术实现智能合同审查。

### 核心特性

- **规则可配置**：Rule as Data，规则以结构化数据形式存储
- **证据可定位**：每一条审核结论包含原文证据（文本、页码、位置）
- **过程可追问**：支持多轮追问与解释
- **基于 RAG**：检索增强生成，提高审核准确性

## 项目结构

```
approve_assistant/
├── backend/           # 后端服务（FastAPI）
├── frontend/          # 前端应用（React + Vite）
├── prompts/           # Prompt 模板
├── shared/            # 共享资源
│   └── schemas/       # 数据契约定义
├── tests/             # 测试用例
├── plan.md            # 项目协同与开发计划
├── task.md            # 任务协同开发清单
├── summary.md         # 项目整体进展同步
└── CLAUDE.md          # Claude 助手协作指南
```

## 快速开始

### 后端启动

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端 | FastAPI |
| 前端 | React + Vite |
| 文档处理 | pdfplumber / PyMuPDF |
| Embedding | OpenAI Embedding API |
| 向量存储 | FAISS |
| 数据库 | SQLite / PostgreSQL |

## 开发规范

- 所有开发任务记录在 `task.md` 中
- 任务完成后更新 `summary.md`
- 模块之间通过 Schema + API 协作
- 每项任务必须包含自测用例

## 文档

- [技术架构文档](./trust_lens_ai_合同审核助手完整技术架构文档 (1).md)
- [开发计划](./plan.md)
- [任务清单](./task.md)
- [协作指南](./CLAUDE.md)

## 许可证

MIT License

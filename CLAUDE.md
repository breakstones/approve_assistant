# TrustLens AI - Claude 助手协作指南

> 项目代号：TrustLens
> 项目定位：规则驱动、证据可溯源、基于 RAG 的合同智能审查系统
> 文档版本：v1.0
> 创建日期：2026-02-09

---

## 项目概述

TrustLens 是一个 AI 合同审核助手，核心目标是构建一个：
- **规则可配置**（Rule as Data）
- **证据可定位**（Evidence-first）
- **过程可追问**（Explainable & Interactive）
- **基于 RAG 的审查执行引擎**

### 核心设计原则

1. **Rule as Data**：审核规则不是写死在 Prompt 中，规则以结构化数据形式存储、版本化管理
2. **Evidence First**：每一条审核结论必须有原文证据，Evidence 必须包含：文本、页码、位置信息（bbox）
3. **Rule-aware RAG**：检索阶段即引入规则语义，降低向量检索噪音

---

## 技术架构

### 架构分层

```
┌──────────────────────────────────────────┐
│              Web UI Layer                │
│    上传 / 进度 / 双屏预览 / 追问          │
└───────────────▲──────────────────────────┘
                │
┌───────────────┴──────────────────────────┐
│         API Gateway / Orchestrator       │
│    文档状态机 / 任务编排 / 会话管理       │
└───────▲───────────────▲──────────────────┘
        │               │
┌───────┴───────┐   ┌───┴──────────────────┐
│ Config Agent  │   │   Execution Agent     │
│  规则配置中心  │   │  RAG + 规则审查        │
└───────▲───────┘   └───▲──────────────────┘
        │               │
┌───────┴───────────────┴──────────────────┐
│  Document Intelligence & Vector Store     │
│ Chunk / Position / Embedding / Evidence   │
└───────────────▲──────────────────────────┘
                │
┌───────────────┴──────────────────────────┐
│              LLM Runtime                  │
│     审核 / 检索 / 解释 / 追问              │
└──────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端 | FastAPI |
| 前端 | React + Vite |
| 文档处理 | pdfplumber / PyMuPDF |
| Embedding | OpenAI Embedding API |
| 向量存储 | FAISS / pgvector |
| 数据库 | SQLite / PostgreSQL |

---

## 核心数据契约（Schema）

### Rule Schema（规则定义）

```json
{
  "rule_id": "payment_cycle_max_30",
  "name": "付款周期限制",
  "category": "Payment",
  "intent": "限制付款周期不超过 30 天",
  "type": "numeric_constraint",
  "params": {
    "max_days": 30
  },
  "risk_level": "HIGH",
  "retrieval_tags": ["payment", "cycle"],
  "prompt_template_id": "numeric_constraint_v1"
}
```

规则类型：
- `numeric_constraint`：数值约束
- `text_contains`：文本包含检查
- `prohibition`：禁止条款
- `requirement`：必须条款

### Chunk Schema（文档切分单元）

```json
{
  "chunk_id": "doc1_p3_c2",
  "doc_id": "doc1",
  "page": 3,
  "clause_hint": "付款条款",
  "text": "付款周期为收到发票后 45 日内完成。",
  "bbox": [x1, y1, x2, y2]
}
```

原则：一个 Chunk = 一个最小可高亮证据单元，推荐 150-300 tokens

### Review Result Schema（审核结果）

```json
{
  "rule_id": "payment_cycle_max_30",
  "status": "RISK",
  "reason": "合同约定付款周期为 45 天，超过 30 天限制",
  "evidence": [
    {
      "chunk_id": "doc1_p3_c2",
      "page": 3,
      "text": "付款周期为收到发票后 45 日内完成",
      "bbox": [...]
    }
  ]
}
```

状态值：
- `PASS`：通过
- `RISK`：风险
- `MISSING`：未找到相关条款

### Document State Schema（文档状态机）

状态流转：`UPLOADED` → `PROCESSING` → `READY` → `REVIEWING` → `REVIEWED`

---

## 七大核心模块

| 模块 | 职责 | 关键产出 | 推荐角色 |
|------|------|----------|----------|
| Configuration Agent | 规则配置、规则解析、规则存储 | Rule Schema、规则解析 Prompt | AI 工程师 |
| Document Intelligence | 文档解析、Chunk 切分、位置信息 | Chunk Schema、Embedding Pipeline | 后端 / NLP |
| Vector & Evidence Store | 向量存储、检索接口 | Vector API、Metadata 设计 | 后端 |
| Execution Agent | RAG 检索 + 审核执行 | 审核 Prompt、Result Schema | AI 工程师 |
| Explainability Agent | 追问、解释、Grounding | Explain Prompt | AI 工程师 |
| API / Orchestrator | 状态机、任务调度、接口编排 | REST API、状态流转 | 后端 |
| Web UI | 上传、进度、双屏、高亮 | React 页面 | 前端 |

---

## 用户旅程

```
用户上传合同文档
   ↓
文档预处理（拆分 + 位置信息记录 + Embedding）
   ↓
执行智能审查（RAG 检索 + LLM + 审核规则）
   ↓
输出结构化审核结果（含 Evidence）
   ↓
基于审核结果进行多轮追问与解释
```

---

## 项目文档结构

```
approve_assistant/
├── plan.md                    # 项目协同与开发计划（已确认）
├── task.md                    # 任务协同开发清单（46个任务）
├── summary.md                 # 项目整体进展同步
├── trust_lens_ai_合同审核助手完整技术架构文档 (1).md  # 技术架构文档
├── CLAUDE.md                  # 本文件：Claude 助手协作指南
├── CLAUDE.md.local            # 用户私有配置（如有）
└── (待创建的项目代码)
    ├── backend/
    ├── frontend/
    ├── prompts/
    └── shared/
```

---

## 协同开发规范

### 任务管理

- 所有开发任务记录在 `task.md` 中
- 任务状态：`TODO` → `IN_PROGRESS` → `REVIEW` → `DONE`
- 任务完成后更新 `summary.md` 进行项目进展同步

### 接口协作原则

1. 模块之间只通过 **Schema + API** 协作
2. Schema 冻结后不得随意变更
3. 每个模块必须提供 Mock 数据
4. Prompt 视为代码，需要版本化

### 代码质量要求

- 每项任务必须包含自测用例
- 每个模块可独立 Mock 测试
- 审核结果作为"事实源"，禁止 UI 推理

---

## MVP 验收清单

- [ ] 可上传 PDF/DOCX 合同文档
- [ ] 文档自动拆分并保留位置信息
- [ ] 基于规则执行智能审查
- [ ] 审核结果包含原文证据（页码、位置）
- [ ] 双屏 UI 展示结果与原文
- [ ] 点击结果可定位并高亮原文
- [ ] 支持多轮追问与解释

---

## 开发阶段

### Phase 0: 基础设施与契约定义（最先完成）
- 项目初始化与环境搭建
- Rule Schema 设计与冻结
- Chunk Schema 设计与冻结
- Review Result Schema 设计与冻结
- Document State Schema 设计

### Phase 1-7: 并行开发阶段
- Configuration Agent（规则配置中心）
- Document Intelligence（文档预处理）
- Execution Agent（RAG 审查执行）
- Explainability Agent（追问与解释）
- Web UI（前端）
- 集成与优化
- 测试与交付

---

## 常用命令与工具

### 后端开发
```bash
# 启动 FastAPI 服务
cd backend && uvicorn main:app --reload

# 运行测试
pytest tests/
```

### 前端开发
```bash
# 启动开发服务器
cd frontend && npm run dev

# 构建生产版本
npm run build
```

### 文档处理测试
```bash
# 测试 PDF 解析
python -m backend.document.pdf_parser test.pdf

# 测试 Embedding
python -m backend.document.embedding
```

---

## GitHub 仓库

- 仓库地址：https://github.com/breakstones/approve_assistant
- 技术讨论：项目 Issues
- 代码 Review：Pull Request

---

## AI 助手协作要点

当协助开发时，请遵循以下原则：

1. **Schema 优先**：任何开发前先确认相关 Schema 已定义
2. **Evidence First**：审核结果必须包含原文证据引用
3. **Prompt 工程**：所有 Prompt 需要强约束，避免幻觉
4. **模块自治**：各模块通过 API 协作，避免紧耦合
5. **测试覆盖**：每个任务完成后必须包含自测
5. **信息共享**：每项任务完成，必须更新 task.md 、plan.md 、summary.md 实时反馈进度。每项任务完成，需完整提交并推送一次代码。1.用于记录每次修改 2.也用于协作中的信息通讯。


### 处理任务时

1. 先查看 `task.md` 了解任务详情
2. 确认依赖任务已完成
3. 遵循 Schema 契约实现
4. 完成后更新任务状态和 `summary.md`

### 处理问题时

1. 先查阅技术架构文档了解设计意图
2. 查看相关 Schema 定义
3. 参考现有任务实现模式
4. 记录决策到 `summary.md` 决策记录部分

---

## 企业级演进方向

- 规则版本治理（Rule Lifecycle）
- 审核结果审计日志
- Human-in-the-loop 复核
- 多模型对照审核
- 风险统计与规则命中分析

---

**最后更新**：2026-02-09
**文档状态**：✅ 已确认

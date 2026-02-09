# TrustLens AI 合同审核助手

> 项目代号：**TrustLens**  
> 定位：**规则驱动、证据可溯源、基于 RAG 的合同智能审查系统**  
> 目标：在保证一天内可从 0 到 1 落地 MVP 的前提下，构建具备企业级演进能力的技术架构。

---

## 1. 项目背景与目标

### 1.1 背景
合同审核是典型的高风险、高专业度、强解释性的业务场景，传统人工审核成本高、效率低，而“纯大模型阅读合同”的方式在 **可解释性、可溯源性、合规性** 上存在天然缺陷。

TrustLens 旨在构建一个：
- **规则可配置**（Rule as Data）
- **证据可定位**（Evidence-first）
- **过程可追问**（Explainable & Interactive）
- **基于 RAG 的审查执行引擎**

的 AI 合同审核助手。

---

## 2. 用户旅程（User Journey）

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

## 3. 总体技术架构

### 3.1 架构总览

```
┌──────────────────────────────────────────┐
│                Web UI                    │
│ 上传 / 进度 / 双屏预览 / 追问             │
└───────────────▲──────────────────────────┘
                │
┌───────────────┴──────────────────────────┐
│        API Gateway / Orchestrator         │
│ 文档状态机 / 任务编排 / 会话管理           │
└───────▲───────────────▲──────────────────┘
        │               │
┌───────┴───────┐   ┌───┴──────────────────┐
│ Config Agent  │   │   Execution Agent     │
│ 规则配置中心  │   │  RAG + 规则审查        │
└───────▲───────┘   └───▲──────────────────┘
        │               │
┌───────┴───────────────┴──────────────────┐
│  Document Intelligence & Vector Store     │
│ Chunk / Position / Embedding / Evidence   │
└───────────────▲──────────────────────────┘
                │
┌───────────────┴──────────────────────────┐
│              LLM Runtime                  │
│ 审核 / 检索 / 解释 / 追问                  │
└──────────────────────────────────────────┘
```

---

## 4. 核心设计原则

### 4.1 Rule as Data
- 审核规则不是写死在 Prompt 中
- 规则以结构化数据形式存储、版本化管理
- Prompt = 模板 + 规则实例

### 4.2 Evidence First
- 每一条审核结论必须有原文证据
- Evidence 必须包含：文本、页码、位置信息（bbox）
- Evidence 是 UI 高亮与审计可信度的基础

### 4.3 Rule-aware RAG
- 检索阶段即引入规则语义
- 降低向量检索噪音，避免“全文聊天”

---

## 5. Configuration Agent（规则配置中心）

### 5.1 规则模型设计

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

### 5.2 自然语言规则解析

输入：
> “付款周期不得超过 30 天”

输出（结构化）：
```json
{
  "field": "payment_cycle",
  "operator": "<=",
  "value": 30,
  "unit": "days"
}
```

---

## 6. Document Intelligence（文档预处理与 Embedding）

### 6.1 文档处理 Pipeline

```
PDF / DOCX
 → 文本抽取（保留页码与坐标）
 → 语义切分（Chunk）
 → 元数据增强
 → Embedding
 → 向量库 + Evidence Store
```

### 6.2 Chunk 设计规范

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

原则：
- 一个 Chunk = 一个最小可高亮证据单元
- 推荐 150–300 tokens

### 6.3 Embedding 与向量存储

```json
{
  "vector": [...],
  "metadata": {
    "doc_id": "doc1",
    "chunk_id": "doc1_p3_c2",
    "page": 3,
    "tags": ["payment"]
  }
}
```

---

## 7. Execution Agent（RAG 驱动的审查执行）

### 7.1 执行流程

```
for rule in rules:
    query = build_rule_query(rule)
    chunks = vector_search(query, filter=rule.tags)
    result = llm_check(rule, chunks)
    store(result)
```

### 7.2 审核 Prompt 约束

- 仅基于候选原文
- 必须逐字引用 Evidence
- 找不到返回 MISSING

### 7.3 审核结果结构

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

---

## 8. 文档状态机（支撑用户旅程）

```
UPLOADED
 → PROCESSING
 → READY
 → REVIEWING
 → REVIEWED
```

用于：
- UI 进度展示
- 防止非法操作
- 支持失败重试

---

## 9. 交互 UI 与原文溯源

### 9.1 双屏设计
- 左侧：规则列表 + 审核状态
- 右侧：文档预览（PDF.js / HTML）

### 9.2 Evidence 定位逻辑

```ts
scrollToEvidence(chunkId) {
  const el = document.querySelector(`[data-chunk-id="${chunkId}"]`)
  el.scrollIntoView({ behavior: 'smooth' })
  el.classList.add('highlight')
}
```

---

## 10. 多轮追问与解释（Explainability）

### 10.1 追问上下文组成
- 原始规则
- 审核结论
- Evidence 原文
- 用户问题

### 10.2 Explain Prompt 示例

```
规则：付款周期不得超过 30 天
结论：不通过
依据原文：付款周期为收到发票后 45 日内完成
用户问题：为什么这条不通过？
```

---

## 11. MVP 技术选型建议

### 后端
- FastAPI
- 异步任务：BackgroundTask / Celery
- SQLite / PostgreSQL

### 文档处理
- PDF：pdfplumber / PyMuPDF
- Word：python-docx

### Embedding & Vector Store
- OpenAI Embedding API / 兼容模型
- FAISS / pgvector

### 前端
- React + Vite
- PDF.js + 高亮层

---

## 12. 企业级演进方向

- 规则版本治理（Rule Lifecycle）
- 审核结果审计日志
- Human-in-the-loop 复核
- 多模型对照审核
- 风险统计与规则命中分析

---

## 13. 多人协同研发与分工设计

TrustLens 作为一个 **AI + 文档智能 + Web 应用** 的系统，非常适合采用并行协同研发。以下从 **功能模块、前后端、技术栈/角色** 三个维度给出可落地的协同分工方案，支持 1 天 Hackathon 或 2–4 周工程化迭代。

---

### 13.1 按功能模块的协同分工（最推荐）

> 适用于：AI / 后端 / 前端成员混合，强调“模块自治 + 接口协作”

#### 模块拆分总览

| 模块 | 主要职责 | 关键产出 | 推荐角色 |
|----|----|----|----|
| Configuration Agent | 规则配置、规则解析、规则存储 | Rule Schema、规则解析 Prompt | AI 工程师 |
| Document Intelligence | 文档解析、Chunk 切分、位置信息 | Chunk Schema、Embedding Pipeline | 后端 / NLP |
| Vector & Evidence Store | 向量存储、检索接口 | Vector API、Metadata 设计 | 后端 |
| Execution Agent | RAG 检索 + 审核执行 | 审核 Prompt、Result Schema | AI 工程师 |
| Explainability Agent | 追问、解释、Grounding | Explain Prompt | AI 工程师 |
| API / Orchestrator | 状态机、任务调度、接口编排 | REST API、状态流转 | 后端 |
| Web UI | 上传、进度、双屏、高亮 | React 页面 | 前端 |

**协作原则**：
- 模块之间只通过 **Schema + API** 协作
- 每个模块可独立 Mock / Stub 开发

---

### 13.2 按前端 / 后端 / AI 能力分工（最易管理）

> 适用于：中小团队（3–6 人），强调职责清晰

#### 前端组（1–2 人）
- 文件上传与进度轮询
- 双屏布局（结果 / 文档）
- Evidence 高亮与滚动定位
- 追问交互 UI

**依赖接口**：
- 文档状态 API
- 审核结果 API
- Evidence 定位数据

---

#### 后端组（1–2 人）
- 文档状态机（UPLOADED → REVIEWED）
- 文档解析与 Chunk 管道
- 向量库接入（FAISS / pgvector）
- 审核任务编排

**交付重点**：
- 稳定的数据结构
- 可复用的 Pipeline

---

#### AI / Prompt 组（1–2 人）
- 规则解析 Prompt
- Rule-aware Retrieval Query 设计
- 审核 Prompt（强 Evidence 约束）
- 解释 / 追问 Prompt

**注意事项**：
- Prompt 必须严格依赖输入上下文
- 输出结构必须 100% 可解析

---

### 13.3 按技术栈 / 角色分工（适合工程化）

| 角色 | 关注点 | 主要交付 |
|----|----|----|
| AI Architect | Agent 边界、RAG 策略 | Prompt 体系、流程设计 |
| Backend Engineer | Pipeline、性能、存储 | API、任务系统 |
| Frontend Engineer | 可用性、可解释性 | UI、交互体验 |
| Tech Lead | 架构一致性 | Schema、接口规范 |

---

### 13.4 并行开发的接口契约（关键）

为避免阻塞，推荐 **先定义 Schema，再写实现**。

#### 核心契约示例

- Rule Schema（Config Agent ↔ Execution Agent）
- Chunk Schema（Document ↔ Vector ↔ UI）
- Review Result Schema（Execution ↔ UI）

> Schema 一旦冻结，各模块即可完全并行开发。

---

### 13.5 1 天 Hackathon 推荐分工示例（4 人）

| 成员 | 当日任务 |
|----|----|
| A | 文档解析 + Chunk + Embedding |
| B | 审核规则模型 + Execution Prompt |
| C | API 编排 + 状态机 |
| D | 前端双屏 + 高亮 |

---

### 13.6 工程化阶段的协作建议

- 使用 Monorepo（frontend / backend / prompts）
- Prompt 视为代码（版本化、Review）
- 每个模块必须提供 Mock 数据
- 审核结果作为“事实源”，禁止 UI 推理

---

## 14. 总结

TrustLens 的协同研发核心在于：

> **模块自治 + 数据契约 + Evidence 驱动 + Prompt 工程规范化**

只要 Schema 与 Agent 边界清晰，TrustLens 可以在多人并行下快速从 MVP 演进为企业级 AI 合同审查平台。


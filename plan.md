# TrustLens AI 合同审核助手 - 项目协同与开发计划

> 项目代号：**TrustLens**
> 计划周期：1天 MVP Hackathon → 2-4周 工程化迭代
> 文档版本：v1.0
> 创建日期：2026-02-09

---

## 1. 项目概览

### 1.1 项目定位
规则驱动、证据可溯源、基于 RAG 的合同智能审查系统

### 1.2 核心目标
- [ ] 一天内完成 MVP 从 0 到 1 落地
- [ ] 构建具备企业级演进能力的技术架构
- [ ] 实现规则可配置、证据可定位、过程可追问

### 1.3 技术栈选型

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 后端 | FastAPI | 高性能异步 Web 框架 |
| 前端 | React + Vite | 现代化前端构建工具 |
| 文档处理 | pdfplumber / PyMuPDF | PDF 解析，保留页码与坐标 |
| Embedding | OpenAI Embedding API | 向量化服务 |
| 向量存储 | FAISS / pgvector | 高效向量检索 |
| 数据库 | SQLite / PostgreSQL | 持久化存储 |

---

## 2. 核心架构分层

### 2.1 功能模块划分

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

### 2.2 七大核心模块

| 模块 | 负责人 | 优先级 | 依赖 |
|------|--------|--------|------|
| Configuration Agent | _TBD_ | P0 | 无 |
| Document Intelligence | _TBD_ | P0 | 无 |
| Vector & Evidence Store | _TBD_ | P0 | Document Intelligence |
| Execution Agent | _TBD_ | P0 | Config Agent, Vector Store |
| Explainability Agent | _TBD_ | P1 | Execution Agent |
| API / Orchestrator | _TBD_ | P0 | 所有 Agent |
| Web UI | _TBD_ | P0 | API / Orchestrator |

---

## 3. 开发阶段规划

### 3.1 第一阶段：Schema 契约定义（必须最先完成）

**目标**：冻结所有核心数据结构，使各模块可并行开发

**交付物**：
- [ ] Rule Schema（规则定义）
- [ ] Chunk Schema（文档切分单元）
- [ ] Review Result Schema（审核结果）
- [ ] Document State Schema（文档状态机）
- [ ] Evidence Schema（证据定位）

**时间**：Day 1 上午（2小时）

### 3.2 第二阶段：MVP 并行开发（Day 1 全天）

**并行开发任务**：
1. Configuration Agent：规则模型 + 解析 Prompt
2. Document Intelligence：解析 Pipeline + Embedding
3. Execution Agent：RAG 检索 + 审核 Prompt
4. API / Orchestrator：状态机 + REST API
5. Web UI：上传 + 双屏 + 高亮

### 3.3 第三阶段：工程化迭代（Week 2-4）

- [ ] 规则版本治理
- [ ] 审核结果审计日志
- [ ] Human-in-the-loop 复核
- [ ] 多模型对照审核
- [ ] 风险统计与规则命中分析

---

## 4. 协同工作机制

### 4.1 任务管理规范
- 所有开发任务记录在 `task.md` 中
- 每项任务包含：任务ID、描述、负责人、状态、验收标准、自测要求
- 任务状态：`TODO` → `IN_PROGRESS` → `REVIEW` → `DONE`

### 4.2 进度同步机制
- 任务完成后更新 `summary.md`
- 每日站会前更新个人任务状态
- 阻塞问题立即标注并通知相关人员

### 4.3 代码质量要求
- 每个模块必须提供 Mock 数据
- 每项任务必须包含自测用例
- Prompt 视为代码，需要版本化

### 4.4 接口协作原则
- 模块之间只通过 **Schema + API** 协作
- Schema 冻结后不得随意变更
- 变更必须通过 Tech Lead 审批

---

## 5. 验收标准

### 5.1 MVP 验收清单
- [ ] 可上传 PDF/DOCX 合同文档
- [ ] 文档自动拆分并保留位置信息
- [ ] 基于规则执行智能审查
- [ ] 审核结果包含原文证据（页码、位置）
- [ ] 双屏 UI 展示结果与原文
- [ ] 点击结果可定位并高亮原文
- [ ] 支持多轮追问与解释

### 5.2 技术质量标准
- [ ] 所有核心 Schema 冻结并文档化
- [ ] 每个 Agent 可独立 Mock 测试
- [ ] API 响应时间 < 3秒
- [ ] 前端交互流畅，无明显卡顿
- [ ] 至少覆盖 3 种常见合同类型

---

## 6. 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| Schema 定义不完善 | 模块阻塞 | Day 1 上午集中评审冻结 |
| Prompt 效果不理想 | 审核质量差 | 预留调试时间，准备 fallback |
| 文档解析失败率高 | 核心功能不可用 | 多方案备选（pdfplumber/PyMuPDF） |
| 前后端联调问题 | 进度延误 | 提前定义 Mock 数据并行开发 |
| 向量检索效果差 | 审核结果不准 | Rule-aware 检索，人工验证 |

---

## 7. 角色与分工建议

### 7.1 4人团队推荐分工（Hackathon）

| 成员 | 角色 | 核心职责 |
|------|------|----------|
| A | Backend + Doc Intelligence | 文档解析、Chunk、Embedding |
| B | AI Engineer | 规则模型、Execution Prompt |
| C | Backend + Orchestrator | API、状态机、任务编排 |
| D | Frontend | 双屏 UI、高亮、交互 |

### 7.2 6人团队推荐分工（工程化）

| 成员 | 角色 | 核心职责 |
|------|------|----------|
| A | Tech Lead + AI Architect | 架构设计、Prompt 体系 |
| B | Backend Engineer | Document Intelligence |
| C | Backend Engineer | Vector Store + API |
| D | AI Engineer | Execution + Explainability |
| E | Frontend Engineer | Web UI 开发 |
| F | QA + DevOps | 测试、部署、CI/CD |

---

## 8. 交付物清单

### 8.1 代码交付
- [ ] Configuration Agent 模块
- [ ] Document Intelligence Pipeline
- [ ] Vector Store 接入
- [ ] Execution Agent 实现
- [ ] Explainability Agent 实现
- [ ] API Gateway / Orchestrator
- [ ] Web UI 完整实现

### 8.2 文档交付
- [ ] API 接口文档
- [ ] Schema 定义文档
- [ ] Prompt 说明书
- [ ] 部署文档
- [ ] 使用手册

### 8.3 测试交付
- [ ] 单元测试覆盖率 > 60%
- [ ] 集成测试用例
- [ ] 端到端测试场景
- [ ] Prompt 效果评估报告

---

## 9. 附录

### 9.1 相关文档
- `task.md` - 任务协同开发清单
- `summary.md` - 项目整体进展同步
- `trust_lens_ai_合同审核助手完整技术架构文档 (1).md` - 技术架构文档

### 9.2 沟通渠道
- 技术讨论：项目 Issues
- 紧急问题：即时通讯群
- 代码 Review：Pull Request

---

**文档状态**：✅ 已确认
**最后更新**：2026-02-09

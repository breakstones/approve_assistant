# TrustLens AI - 常见问题 FAQ

> 版本: v1.0
> 更新日期: 2026-02-09

---

## 目录

1. [安装与部署](#安装与部署)
2. [使用指南](#使用指南)
3. [功能问题](#功能问题)
4. [错误排查](#错误排查)
5. [性能优化](#性能优化)
6. [其他问题](#其他问题)

---

## 安装与部署

### Q1: 系统有什么要求？

**A**: 最低要求：
- Python 3.8+
- Node.js 16+
- 4GB 内存
- 10GB 磁盘空间

推荐配置：
- 8GB+ 内存
- SSD 磁盘
- 4 核心 CPU

---

### Q2: 如何安装依赖？

**A**:
```bash
# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
```

---

### Q3: 可以使用 Docker 部署吗？

**A**: 可以。项目提供了 Dockerfile 和 docker-compose.yml：

```bash
docker-compose up -d
```

详见 [部署文档](./deployment.md#docker-部署)

---

### Q4: Windows 环境有什么特殊注意事项？

**A**:
1. 使用 PowerShell 或 Git Bash
2. 激活虚拟环境: `venv\Scripts\activate`
3. 可能需要安装 Visual C++ Build Tools

---

## 使用指南

### Q5: 如何上传合同文档？

**A**:
1. 访问前端页面（默认 http://localhost:5173）
2. 点击"上传文档"或直接拖拽文件
3. 支持的格式: PDF、DOCX
4. 文件大小限制: 50MB

---

### Q6: 如何创建审核规则？

**A**: 有两种方式：

1. **自然语言创建**：
   ```
   输入: "付款周期不得超过 30 天"
   系统自动解析为结构化规则
   ```

2. **结构化创建**：
   - 填写规则 ID、名称、类型、参数
   - 选择风险等级
   - 添加检索标签

---

### Q7: 支持哪些规则类型？

**A**: 支持 4 种规则类型：

| 类型 | 说明 | 示例 |
|------|------|------|
| numeric_constraint | 数值约束 | 付款周期 ≤ 30 天 |
| text_contains | 文本包含 | 必须包含"管辖法律" |
| prohibition | 禁止条款 | 禁止自动续约 |
| requirement | 必须条款 | 必须包含保密条款 |

---

### Q8: 如何查看审核结果？

**A**:
1. 审核完成后，结果列表自动展示
2. 每条结果显示：状态、原因、证据
3. 点击证据可定位到原文位置
4. 可按状态过滤（通过/风险/缺失）

---

### Q9: 如何进行追问？

**A**:
1. 在审核结果下方找到追问输入框
2. 输入问题，如"为什么判定为有风险？"
3. 系统基于证据进行解释
4. 支持多轮对话

---

## 功能问题

### Q10: 文档上传后一直处于处理中？

**A**: 可能原因：
1. 文档格式不支持
2. 文档损坏或加密
3. 系统资源不足

解决方法：
- 检查文档格式是否正确
- 尝试重新上传
- 查看后端日志

---

### Q11: 为什么有些规则返回 MISSING 状态？

**A**: MISSING 表示：
- 在文档中未找到相关条款
- 可能文档确实缺少该条款
- 也可能是检索关键词不够准确

建议：
- 检查文档是否真的缺少该条款
- 调整规则的检索标签

---

### Q12: Evidence 定位不准确怎么办？

**A**:
1. PDF 解析的 bbox 坐标可能有误差
2. 尝试使用不同版本的 PDF
3. 或使用文档预览手动查找

---

### Q13: 支持批量审核吗？

**A**: 当前版本支持：
- 一次选择多条规则
- 后台异步执行
- 可查看进度和状态

---

### Q14: 可以导出审核报告吗？

**A**: 当前版本暂不支持，计划在后续版本添加：
- PDF 报告导出
- Excel 数据导出
- API 接口导出

---

## 错误排查

### Q15: 启动时报 "ModuleNotFoundError"

**A**: 依赖未正确安装：

```bash
# 重新安装依赖
pip install -r requirements.txt

# 或指定镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

### Q16: 端口 8000 被占用怎么办？

**A**: 修改启动端口：

```bash
# 使用其他端口
uvicorn main:app --port 8001
```

或查找并关闭占用进程：

```bash
# Linux/macOS
lsof -i :8000
kill -9 <PID>

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

### Q17: 数据库连接失败？

**A**: 检查：
1. SQLite 文件路径是否正确
2. 文件权限是否正确
3. 数据库文件是否损坏

重建数据库：
```bash
rm backend/data/trustlens.db
# 重启服务自动创建
```

---

### Q18: PDF 解析失败？

**A**:
1. 确认 PDF 未加密
2. 尝试使用其他工具转换 PDF
3. 安装系统依赖：

```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

---

### Q19: 前端无法连接后端？

**A**: 检查：
1. 后端服务是否启动
2. API 地址配置是否正确
3. 防火墙是否允许连接

配置 API 地址：
```typescript
// frontend/src/config.ts
export const API_BASE_URL = 'http://your-backend:8000';
```

---

## 性能优化

### Q20: 文档处理太慢怎么办？

**A**: 优化方法：
1. 使用更快的 CPU
2. 减少 chunk 数量
3. 使用向量缓存
4. 考虑使用 GPU 加速

---

### Q21: 内存占用过高？

**A**:
1. 减少并发处理数量
2. 清理历史文档数据
3. 使用 FAISS 替代内存向量存储

---

### Q22: 如何提高审核准确率？

**A**:
1. 优化规则描述
2. 调整检索标签
3. 提供更多示例文档
4. 使用更强的 LLM 模型

---

## 其他问题

### Q23: 数据存储在哪里？

**A**:
- 数据库: `backend/data/trustlens.db`
- 上传文件: `backend/data/uploads/`
- 日志: `backend/logs/trustlens.log`

---

### Q24: 支持多用户吗？

**A**: 当前版本为单用户版本，多用户功能计划中：
- 用户认证
- 权限管理
- 数据隔离

---

### Q25: 可以离线使用吗？

**A**: 可以：
- Mock LLM 模式完全离线
- 真实 LLM 需要网络连接
- 向量检索可以本地运行

---

### Q26: 如何配置 LLM？

**A**: 编辑 `backend/.env`：

```bash
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4
```

或使用兼容 OpenAI 的其他服务。

---

### Q27: 支持哪些语言的合同？

**A**:
- 主要支持中文合同
- 英文合同部分支持
- 其他语言需要额外配置

---

### Q28: 如何获取技术支持？

**A**:
1. 查看 [部署文档](./deployment.md)
2. 搜索 GitHub Issues
3. 提交新的 Issue
4. 联系开发团队

---

### Q29: 是否开源？

**A**: 是的，项目在 GitHub 上开源：
https://github.com/breakstones/approve_assistant

欢迎贡献代码和建议！

---

### Q30: 后续计划有哪些功能？

**A**:
- [ ] 多用户支持
- [ ] 报告导出
- [ ] 更多文档格式
- [ ] AI 规则推荐
- [ ] 移动端支持
- [ ] API 限流
- [ ] 审批流程集成

---

**文档维护**: TrustLens AI Team
**最后更新**: 2026-02-09

更多问题请访问: https://github.com/breakstones/approve_assistant/issues

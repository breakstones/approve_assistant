# TrustLens AI - 部署文档

> 版本: v1.0
> 更新日期: 2026-02-09
> 部署环境: 本地开发 / 云服务器

---

## 目录

1. [系统要求](#系统要求)
2. [环境依赖](#环境依赖)
3. [快速开始](#快速开始)
4. [详细部署步骤](#详细部署步骤)
5. [配置说明](#配置说明)
6. [生产环境部署](#生产环境部署)
7. [故障排查](#故障排查)

---

## 系统要求

### 最低配置

| 组件 | 要求 |
|------|------|
| 操作系统 | Linux / macOS / Windows |
| Python | 3.8+ |
| Node.js | 16+ |
| 内存 | 4GB+ |
| 磁盘 | 10GB+ |

### 推荐配置

| 组件 | 要求 |
|------|------|
| CPU | 4 核心以上 |
| 内存 | 8GB+ |
| 磁盘 | SSD 20GB+ |

---

## 环境依赖

### 后端依赖

```bash
# Python 依赖
pip install -r requirements.txt
```

主要依赖包：
- `fastapi` - Web 框架
- `uvicorn` - ASGI 服务器
- `sqlalchemy` - ORM
- `pydantic` - 数据验证
- `python-multipart` - 文件上传支持
- `pdfplumber` / `PyMuPDF` - PDF 解析
- `python-docx` - DOCX 解析
- `openai` - LLM 客户端（可选）
- `sentence-transformers` - Embedding（可选）

### 前端依赖

```bash
cd frontend
npm install
```

主要依赖包：
- `react` - UI 框架
- `react-router-dom` - 路由
- `axios` - HTTP 客户端
- `pdfjs-dist` - PDF 渲染
- `tailwindcss` - 样式框架

### 可选依赖

```bash
# 向量存储（可选）
pip install faiss-cpu  # CPU 版本
# 或
pip install faiss-gpu  # GPU 版本

# LLM 客户端（可选）
pip install openai
```

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/breakstones/approve_assistant.git
cd approve_assistant
```

### 2. 后端启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
cd backend
uvicorn main:app --reload --port 8000
```

### 3. 前端启动

```bash
# 安装依赖
cd frontend
npm install

# 启动开发服务器
npm run dev
```

### 4. 访问应用

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

---

## 详细部署步骤

### 步骤 1: 环境准备

```bash
# 创建项目目录
mkdir -p /opt/trustlens
cd /opt/trustlens

# 克隆代码
git clone https://github.com/breakstones/approve_assistant.git .
```

### 步骤 2: Python 环境配置

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 步骤 3: 数据库初始化

```bash
# SQLite 数据库会自动创建
# 数据文件位置: backend/data/trustlens.db
```

### 步骤 4: 后端服务配置

创建 `backend/.env` 文件：

```bash
# LLM 配置（可选）
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4

# Embedding 配置（可选）
EMBEDDING_MODEL=text-embedding-ada-002
VECTOR_STORE_TYPE=memory  # 或 faiss

# 服务配置
HOST=0.0.0.0
PORT=8000
WORKERS=4
LOG_LEVEL=INFO
```

### 步骤 5: 前端构建

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

### 步骤 6: 使用 systemd 管理服务（Linux）

创建 `/etc/systemd/system/trustlens.service`：

```ini
[Unit]
Description=TrustLens AI Backend
After=network.target

[Service]
Type=notify
User=trustlens
WorkingDirectory=/opt/trustlens/backend
Environment="PATH=/opt/trustlens/venv/bin"
ExecStart=/opt/trustlens/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable trustlens
sudo systemctl start trustlens
sudo systemctl status trustlens
```

### 步骤 7: Nginx 反向代理配置

创建 `/etc/nginx/sites-available/trustlens`：

```nginx
# 后端 API
server {
    listen 80;
    server_name api.trustlens.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# 前端
server {
    listen 80;
    server_name trustlens.com;

    root /opt/trustlens/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 配置说明

### 后端配置

配置文件位置: `backend/config/settings.py`

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| DATABASE_URL | 数据库连接 | sqlite:///data/trustlens.db |
| UPLOAD_DIR | 文件上传目录 | data/uploads |
| MAX_FILE_SIZE | 最大文件大小 | 50MB |
| ALLOWED_EXTENSIONS | 允许的文件类型 | .pdf, .docx |
| LLM_API_KEY | LLM API 密钥 | - |
| VECTOR_STORE_TYPE | 向量存储类型 | memory |

### 前端配置

配置文件位置: `frontend/src/config.ts`

```typescript
export const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';
export const PDF_JS_VERSION = '3.11.174';
```

---

## 生产环境部署

### Docker 部署（推荐）

创建 `Dockerfile`：

```dockerfile
# 后端 Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=sqlite:///data/trustlens.db
    restart: always

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always
```

启动：

```bash
docker-compose up -d
```

---

## 故障排查

### 常见问题

#### 1. 端口被占用

```bash
# 查找占用端口的进程
lsof -i :8000

# 或使用 netstat
netstat -tuln | grep 8000
```

#### 2. 数据库锁定

```bash
# 删除锁文件
rm backend/data/trustlens.db-wal
rm backend/data/trustlens.db-shm
```

#### 3. PDF 解析失败

```bash
# 安装 PDF 解析依赖
pip install pdfplumber PyMuPDF

# 安装系统依赖（Ubuntu）
sudo apt-get install poppler-utils
```

#### 4. 前端构建失败

```bash
# 清理缓存并重新安装
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## 日志查看

### 后端日志

```bash
# 开发环境
# 日志输出到控制台

# 生产环境
tail -f backend/logs/trustlens.log
```

### 系统服务日志

```bash
sudo journalctl -u trustlens -f
```

---

## 健康检查

```bash
# 检查后端服务
curl http://localhost:8000/health

# 检查数据库
curl http://localhost:8000/api/database/status

# 检查 API 文档
curl http://localhost:8000/docs
```

---

## 备份与恢复

### 数据库备份

```bash
# 备份
cp backend/data/trustlens.db backup/trustlens_$(date +%Y%m%d).db

# 恢复
cp backup/trustlens_20260209.db backend/data/trustlens.db
```

### 完整备份

```bash
# 备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR=/backup/trustlens_$DATE

mkdir -p $BACKUP_DIR
cp -r backend/data $BACKUP_DIR/
cp -r backend/uploads $BACKUP_DIR/
tar czf trustlens_backup_$DATE.tar.gz $BACKUP_DIR
```

---

## 更新与升级

### 代码更新

```bash
# 拉取最新代码
git pull origin master

# 更新依赖
pip install -r requirements.txt --upgrade

# 重启服务
sudo systemctl restart trustlens
```

### 数据库迁移

```bash
# 如果有数据库结构变更
cd backend
python migrations/migrate.py
```

---

## 安全建议

1. **API 密钥保护**: 不要将 API 密钥提交到代码仓库
2. **HTTPS 配置**: 生产环境必须使用 HTTPS
3. **访问控制**: 配置防火墙规则
4. **定期备份**: 每日自动备份数据
5. **日志监控**: 设置日志监控和告警

---

**文档维护**: TrustLens AI Team
**最后更新**: 2026-02-09

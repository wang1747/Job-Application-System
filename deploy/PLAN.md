# OfferFlow 上线 + 建库 + 语料积累方案

> 目标：把项目部署到公网，切 Postgres，建立可持续增长、喂给 AI 的简历/JD 语料库。
> 基于对项目源码的实际审查，所有方案都对应到真实代码。

---

## 一、现状速览（代码审查结论）

| 层面 | 现状 | 上线影响 |
|------|------|----------|
| 前端 | React 19 + Vite 8 + nginx 反代 `/api` → backend | ✅ 生产就绪 |
| 后端 | FastAPI + SQLAlchemy 2.0 (同步) + LangGraph agents | ✅ 生产就绪 |
| 数据库 | SQLite 单文件，`DATABASE_URL` 可切 Postgres | ⚠️ 需切 Postgres |
| Postgres 驱动 | `psycopg==3.3.4` + `psycopg-binary` 已在 requirements | ✅ 已就绪 |
| 迁移 | Alembic 已配置（有 versions 目录） | ✅ 已就绪 |
| 向量库 | ChromaDB PersistentClient | ✅ 可用 |
| **Embedding** | **MD5 哈希 384 维（`match/services.py::_get_embedding`）** | ❌ **假语义，是最大技术债** |
| 语料库 | 无共享语料表，数据全 per-user | ❌ 需新建 |
| 安全 | JWT/Encryption 有长度校验；生产环境禁止默认密钥 | ⚠️ 需生成密钥 |
| compose | postgres profile 已预留但未启用；n8n 默认启动 | ⚠️ 需生产版 compose |

**一句话**：架构扎实，切 Postgres 和安全加固是"改配置"级别的工作；真正需要写代码的是 **embedding 升级** 和 **语料库表 + RAG 管线**。

---

## 二、部署架构（方案 A：轻量云主机 + docker-compose）

```
                        Internet
                           |
                    [域名 + HTTPS]
                           |
              +-----------------------+
              |   offerflow-frontend  |   nginx:443/80
              |   (React 静态 + 反代)  |
              +-----------------------+
                           | /api →
              +-----------------------+
              |   offerflow-backend   |   uvicorn:8001
              |   FastAPI + LangGraph |
              +-----------------------+
                    |              |
          +---------+--+     +----+---------+
          |  postgres  |     |   chroma     |
          |  :5432     |     |  (文件卷)    |
          +------------+     +--------------+
```

**为什么不需要 GPU**：项目是 BYOK 架构，调外部 DeepSeek API 做推理，后端只做编排和数据存储。2 核 2G 的普通 CPU 机器完全够用。

---

## 三、已备好的部署包（5 个文件）

| 文件 | 说明 |
|------|------|
| `docker-compose.prod.yml` | 生产编排：Postgres + 后端 + 前端 + 自动备份 |
| `.env.prod.example` | 环境变量模板，所有 `???` 必须替换 |
| `deploy/nginx.prod.conf` | HTTPS + 安全头 + gzip + 静态缓存 |
| `deploy/deploy.sh` | 一键部署脚本（生成密钥→构建→启动→健康检查） |
| `deploy/PLAN.md` | 本文档 |

### 上线步骤（你买完服务器后照做）

```bash
# 1. SSH 登录服务器
# 2. 装 Docker（如果没装）
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker

# 3. 拉代码
git clone <你的仓库地址> /opt/offferflow
cd /opt/offferflow

# 4. 一键部署
bash deploy/deploy.sh
#    脚本会：自动生成密钥 → 提示你填 API Key 和域名 → 构建 → 启动

# 5.（可选）配域名 DNS A 记录 → 服务器 IP
# 6.（可选）替换自签证书为 Let's Encrypt 免费证书
#    https://certbot.eff.org/
```

---

## 四、服务器选购建议

| 云商 | 规格 | 价格 | 备注 |
|------|------|------|------|
| 腾讯云轻量 | 2核2G 3M | ~¥40/月 或年付~¥270 | **推荐**，国内速度快 |
| 阿里云 ECS | 2核2G 3M | ~¥40/月 | 同等 |
| 雨云/狗云 | 1核1G | ~¥20/月 | 预算极限可选 |

**购买要点**：
- 选**轻量应用服务器**（比 ECS 便宜，自带面板）
- 系统** Ubuntu 22.04 / Debian 12**（装 Docker 最省心）
- 带宽 3M 起步（前端是静态文件，首屏后无大流量）
- 磁盘 40G SSD 足够（Postgres + Chroma + 备份）
- **不需要 GPU**

**域名（可选但建议）**：
- 买个 `.com` / `.cn`（¥30-60/年），或用免费的 `.top`
- DNS 解析到服务器 IP
- Let's Encrypt 免费证书（certbot 一键申请）

---

## 五、Postgres 切换（已就绪，无需改代码）

代码层面**零改动**：

1. `database.py` 第 9 行已做兼容：`connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}`
2. `psycopg` (v3) 已在 requirements
3. `docker-compose.prod.yml` 中 backend 环境变量已设：`DATABASE_URL=postgresql+psycopg://...`
4. `config.py` 的 `Settings.database_url` 直接读环境变量

**切换后要做的事**：
```bash
# 首次启动时后端会自动 Base.metadata.create_all() 建表
# 如有 Alembic 迁移，也可手动执行：
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

**数据迁移**（如果 SQLite 已有数据想搬过来）：
```bash
# 1. 导出 SQLite
sqlite3 offerflow.db ".dump" > dump.sql
# 2. 清洗 SQLite 语法差异（AUTOINCREMENT / 方言）
# 3. 导入 Postgres
docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U offerflow -d offerflow < dump.sql
# 或用 pgloader 工具（推荐，自动处理方言差异）
```

---

## 六、语料库设计（核心：让数据库越来越丰富）

你选了"两者都要"：正常使用自然累积 + 专门建可检索语料库喂 AI。下面分两部分。

### 6.1 自然累积（已有，无需改动）

用户日常使用时数据自动入库：

| 数据 | 表 | 增长方式 |
|------|------|---------|
| 简历 | `resumes` | 每次上传/粘贴简历 |
| JD | `job_descriptions` | 每次解析 JD |
| 面经 | `interview_articles` | 每次导入面经 |
| 投递记录 | `applications` | 每次投递 |
| 匹配结果 | `match_results` | 每次匹配 |

这些表已经有 `user_id` 关联，随使用自然增长。

### 6.2 语料库建设（需新增代码）

这是"让 AI 越用越准"的关键。当前项目缺少两层能力：

#### 问题 1：Embedding 是假的

`match/services.py::_get_embedding` 用 MD5 哈希塞进 384 维——这本质是"哈希词袋"，**完全不是语义向量**。两个意思相同但用词不同的句子会得到完全不重叠的向量。ChromaDB 虽然在跑，但检索质量约等于关键词匹配。

**升级方案（三选一，按推荐度排序）**：

| 方案 | 模型 | 是否需 GPU | 中文质量 | 成本 |
|------|------|-----------|---------|------|
| **A. BGE-M3（推荐）** | 1024 维 | 否（CPU 可跑） | 优秀 | 免费 |
| B. Ollama embeddings | nomic-embed / bge-m3 | 否 | 良好 | 免费 |
| C. DeepSeek/硅基流动 API | 远程 embedding | 否 | 优秀 | 极低 |

**方案 A 落地（本地 BGE-M3）**：

```python
# backend/app/core/embeddings.py（新增）
from FlagEmbedding import BGEM3FlagModel

_model = None

def get_embedder():
    global _model
    if _model is None:
        _model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
    return _model

def embed(text: str) -> list[float]:
    return get_embedder().encode([text])["dense_vecs"][0].tolist()
```

requirements 追加：`FlagEmbedding==1.3.5`（首次运行自动从 HuggingFace 下载模型，约 2.3GB，CPU 推理 50ms/条）。

> ⚠️ 服务器磁盘和内存：BGE-M3 需 ~2.5GB 磁盘 + ~1.5GB 内存。2核2G 机器会比较吃紧，建议升到 **2核4G**（约 ¥60/月）。或用方案 C 远程 API 省 1.5G 内存。

#### 问题 2：没有共享语料表

所有数据都是 per-user，AI 无法跨用户参考"别人怎么写的"。

**新增语料表**：

```python
# backend/app/models/corpus.py（新增）
class CorpusItem(Base):
    __tablename__ = "corpus_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_type = Column(String, nullable=False)  # resume | jd | interview | snippet
    raw_text = Column(Text, nullable=False)
    structured = Column(JSON, nullable=True)     # 解析后的结构化字段
    tags = Column(JSON, nullable=True)          # 行业/岗位/技能标签
    source = Column(String, nullable=True)      # user_upload | crawl | import
    user_id = Column(String, nullable=True)     # 贡献者（可空=匿名语料）
    is_public = Column(Boolean, default=False)  # 是否允许跨用户检索
    embedding_id = Column(String, nullable=True)  # ChromaDB 中的 ID
    created_at = Column(DateTime, server_default=func.now())
```

#### RAG 检索管线（在简历优化 / JD 分析 / 面试准备时调用）

```python
# backend/app/modules/corpus/services.py（新增）
def retrieve_similar(query_text: str, top_k: int = 5, item_type: str = None) -> list:
    """检索语料库中最相似的 N 条，喂给 LLM 做参考"""
    query_vec = embed(query_text)
    client = get_vector_store()
    collection = get_or_create_collection(client, "corpus_embeddings")
    where_filter = {"item_type": item_type} if item_type else None
    results = collection.query(
        query_embeddings=[query_vec],
        n_results=top_k,
        where=where_filter,
    )
    return results  # → 作为 LLM context 注入 prompt
```

#### 语料入库流程

```
用户上传简历/JD
     │
     ├─→ 存 resumes / job_descriptions 表（原有逻辑，per-user）
     │
     └─→ [新增] 检查用户是否同意"贡献语料"
              │
              ├─ 同意 → 写入 corpus_items 表 + 生成 embedding 存 Chroma
              └─ 不同意 → 仅存个人数据，不进语料库
```

### 6.3 语料增长策略

| 来源 | 方式 | 预估量 |
|------|------|--------|
| 自身使用 | 每次上传简历/JD/面经时入库 | 百级 |
| 公开数据集 | 导入开源简历数据集（如 Kaggle） | 千级 |
| 爬虫（合规） | 公开招聘网站 JD（遵守 robots.txt） | 万级 |
| 用户导入 | 批量导入功能（上传 .zip 含多个简历文件） | 按需 |

**批量导入接口**（建议新增）：
```
POST /api/v1/corpus/batch-import
  - 上传 zip 文件（含 .pdf / .docx / .txt）
  - 后端解析 → 结构化 → 生成 embedding → 存 corpus_items + Chroma
```

---

## 七、安全加固清单

| 项 | 开发态 | 生产态 | 文件 |
|----|--------|--------|------|
| JWT_SECRET_KEY | 默认值（会 warn） | 32 位随机 | `.env.prod` |
| ENCRYPTION_KEY | 无 | 32 位随机 | `.env.prod` |
| 默认用户 | demo/demo1234 | 随机密码 | `.env.prod` |
| HTTPS | 无 | nginx 443 + Let's Encrypt | `nginx.prod.conf` |
| Postgres 端口 | 5432 公开 | 仅容器内 | compose |
| n8n | 默认启动 | 生产去掉 | compose |
| 安全头 | 无 | HSTS / X-Frame 等 | `nginx.prod.conf` |
| 日志 | 无限制 | 10m×3 轮转 | compose |
| 备份 | 无 | 每日 pg_dump，保留 7 天 4 周 | compose |

---

## 八、执行路线（按优先级）

### Phase 1：上线（1-2 天）
1. ✅ 部署包已备好（compose + nginx + 脚本 + env 模板）
2. [ ] 买服务器 + 域名
3. [ ] 服务器装 Docker，跑 `deploy.sh`
4. [ ] 配域名 DNS + Let's Encrypt 证书
5. [ ] 验证：能注册/登录/上传简历/解析 JD

### Phase 2：建库（3-5 天）
6. [ ] 新增 `corpus_items` 模型 + Alembic 迁移
7. [ ] 新增 `corpus` 模块（CRUD + 批量导入接口）
8. [ ] 在简历/JD 入库流程中加"贡献语料"分支
9. [ ] 导入种子语料（公开数据集 / 历史数据）

### Phase 3：RAG 升级（3-5 天）
10. [ ] 新增 `embeddings.py`，用 BGE-M3 替换 MD5 哈希
11. [ ] 改造 `match/services.py` 的 `_get_embedding` → 调真 embedding
12. [ ] 新增 `retrieve_similar`，在简历优化 / JD 分析时检索语料
13. [ ] 在 LangGraph agent 的 prompt 中注入检索到的上下文

### Phase 4：持续增长（持续）
14. [ ] 批量导入功能（上传 zip）
15. [ ] 前端加"语料管理"页面（查看/搜索/删除语料）
16. [ ] 定期重算 embedding（模型升级时）

---

## 九、面试角度

这个项目可以讲的故事线：
- "从 Vite 脚手架到全栈部署"：技术选型、Docker 编排、nginx 反代、Postgres 切换
- "BYOK 架构"：为什么让用户自带 Key（成本、隐私、合规）
- "RAG 从假到真"：发现 MD5 哈希 embedding 的问题 → 升级 BGE-M3 → 语料库建设 → 检索增强
- "数据飞轮"：使用越多 → 语料越丰富 → AI 建议越准 → 体验越好 → 使用更多

---

## 十、文件清单

```
求职系统/
├── docker-compose.prod.yml   ← 生产编排（新）
├── .env.prod.example         ← 环境变量模板（新）
├── deploy/
│   ├── nginx.prod.conf       ← HTTPS nginx 配置（新）
│   ├── deploy.sh             ← 一键部署脚本（新）
│   └── PLAN.md               ← 本文档（新）
├── docker-compose.yml        ← 开发版（原有）
├── .env.example              ← 开发环境（原有）
├── backend/
│   └── app/
│       ├── core/
│       │   ├── database.py   ← 已兼容 Postgres
│       │   ├── vector_store.py
│       │   └── embeddings.py ← Phase 3 新增
│       ├── models/
│       │   └── corpus.py     ← Phase 2 新增
│       └── modules/
│           ├── corpus/       ← Phase 2 新增
│           └── match/
│               └── services.py  ← Phase 3 改造 embedding
└── frontend/
    └── ...
```

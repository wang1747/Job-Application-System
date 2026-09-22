# OfferFlow 求职全流程智能 Agent 系统

> 一个把简历生成、职位要求分析、简历优化、岗位匹配、面试准备、薪资谈判、投递追踪串成完整闭环的求职助手。
> 基于 FastAPI + LangGraph + ChromaDB + React 构建，支持用户自带 API Key（BYOK），可 Docker 一键部署。界面面向零基础应届生设计，全中文、无术语门槛。

## 项目简介

OfferFlow 面向秋招、社招和日常求职场景，帮助用户从“看到职位”到“拿到 Offer”：

1. 没有简历？填写学校和经历，AI 自动生成一份一页内、匹配岗位的中文简历（覆盖 15 个求职方向、19 个行业范文参考）。
2. 粘贴职位要求或上传截图，AI 自动解析公司和岗位要求。
3. 选择简历和岗位，系统给出匹配度、技能差距和投递建议。
4. 针对目标岗位优化简历（事实保真校验、绝不编造），支持导出中文 PDF / Word。
5. 导入面试经验，生成面试题（带参考答案），进行模拟面试（可提前结束）。
6. 先测测你的市场薪资（参考 2026 届应届生起薪行情），再和 AI 扮演的 HR 实战演练薪资谈判，每轮有教练点评。
7. 使用看板追踪每份投递，自动提醒逾期未跟进和即将面试。

## 核心功能

- 注册、登录、JWT 鉴权、用户数据隔离。
- 管理员用户管理：角色分配、启用/禁用账号。
- 模型设置：支持 DeepSeek、OpenAI、Moonshot 等模型，用户可配置自己的 API Key。
- 简历生成：结构化卡片式输入，AI 生成一页内、字数达标（约 800 字）的中文简历，按 15 个求职方向提供示例/推荐技能，参考 19 个行业的真实范文，逐段重生成给多候选，事实保真校验（不编造）。
- 职位要求分析：提取公司、职位、硬性要求、技术栈、隐藏信号；支持截图 OCR。
- 岗位匹配：本地技能词典 + 真实 JD 词频 + ChromaDB 语义检索混合评分，支持批量匹配。
- 简历优化：针对目标岗位做差距分析 + 整份重写，一页约束（三刀裁剪：删废话/并同类/强重点），事实保真硬校验（关键信息绝不丢失），输出优化前后评分和逐行 diff。
- 简历导出：中文 PDF / Word 一键下载（PDF 用文泉驿 TrueType 字体，Docker 容器内无乱码）。
- 面试准备：面试经验库（文本/文件/截图 OCR 导入）、面试题生成（带参考答案）、多轮模拟面试（可提前结束）、个人题库导入。
- 薪资：先根据简历估市场价（学历 × 岗位方向 × 城市，参考 2026 届应届生起薪行情，数字由规则计算不靠 AI 编造），再 AI 扮演 HR 实战压价，4 个场景，每轮实时教练点评，5 轮后出总结。市场基准数据落库版本化，支持定期自动刷新与手动刷新（旧版本保留可回滚）。
- 投递追踪：看板状态流转、事件时间线、统计图表、主动提醒（Webhook / n8n）。
- 数据管理：一键导出全部数据（JSON）、单条/全部删除（级联清理，不留孤儿数据）。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python 3.13 / FastAPI / SQLAlchemy / Alembic |
| Agent | LangChain / LangGraph / ChromaDB |
| LLM | OpenAI 兼容 API，支持 DeepSeek、OpenAI、Moonshot 等 |
| 前端 | React 19 / TypeScript / Vite / TailwindCSS / Recharts / Zustand |
| 部署 | Docker / docker-compose / Nginx |
| 自动化 | GitHub Actions / n8n |
| 数据 | SQLite（默认，可切换 PostgreSQL） |

## 系统架构

```mermaid
graph TB
    UI[React 前端] --> Nginx[Nginx]
    Nginx --> API[FastAPI]
    API --> JD[JD 解析服务]
    API --> MATCH[匹配分析服务]
    API --> RESUME[简历优化服务]
    API --> INTERVIEW[面试准备服务]
    API --> TRACK[投递追踪服务]
    API --> MODEL[模型配置服务]
    JD --> LLM[用户动态 LLM]
    RESUME --> LLM
    INTERVIEW --> LLM
    MATCH --> CHROMA[ChromaDB]
    TRACK --> DB[(SQLite)]
    TRACK --> WEBHOOK[Webhook / n8n]
```

后端已开始按模块化架构组织：

```text
backend/app/modules/
├── auth/                  # 登录注册
├── jd/                    # 职位要求解析与 OCR
├── resume/                # 简历优化与导出
├── resume_generation/     # 简历生成（结构化 + 范文 + 字数约束）
├── match/                 # 岗位匹配
├── interview/             # 面试准备（面经/题目/模拟面试）
├── salary_negotiation/    # 薪资谈判演练
├── application/           # 投递追踪
├── model_config/          # BYOK 模型设置
├── permissions/           # 角色与资源权限
├── database/              # 数据库统一入口
└── vector_store/          # 向量库统一入口
```

## 快速开始（本地开发）

### 1. 配置环境变量

```bash
cp .env.example .env
```

至少需要配置：

```env
ENCRYPTION_KEY=please-change-this-encryption-key-32chars
JWT_SECRET_KEY=offerflow-secret-key-change-in-production
```

`DEEPSEEK_API_KEY` 不是必须的。首次使用需要用户在“模型设置”页面配置自己的 API Key。

### 2. 启动

```bash
uv sync
uv run python run.py
```

另开终端：

```bash
cd frontend
npm install
npm run dev
```

也可以直接运行：

```bash
start.bat
```

访问：

```text
前端：http://127.0.0.1:5173
后端：http://127.0.0.1:8001
API 文档：http://127.0.0.1:8001/docs
```

## Docker 部署

```bash
cp .env.example .env
docker compose up --build -d
```

访问：

```text
前端：http://localhost
n8n：http://localhost:5678
```

如需启用 PostgreSQL：

```bash
docker compose --profile postgres up -d
```

并将后端 `DATABASE_URL` 改为：

```env
DATABASE_URL=postgresql+psycopg://offerflow:offerflow@postgres:5432/offerflow
```

生产环境建议修改：

- `JWT_SECRET_KEY`
- `ENCRYPTION_KEY`
- `REMINDER_WEBHOOK_URL`
- `DEFAULT_USER_PASSWORD`

## 演示账号

默认演示账号：

```text
用户名：demo
密码：demo1234
```

可在 `.env` 中通过 `DEFAULT_USER_NAME` 和 `DEFAULT_USER_PASSWORD` 修改。

## 模型设置（BYOK）

首次上线不配置默认 API Key，用户必须先完成模型设置：

1. 登录后进入 `/settings`。
2. 选择模型预设，例如 DeepSeek、OpenAI、Moonshot。
3. 填写 API Key。
4. 点击“测试连接”。
5. 测试成功后保存。

安全规则：

- API Key 使用 `ENCRYPTION_KEY` 加密存储。
- API Key 不写日志、不返回给前端。
- 前端只显示掩码，例如 `sk-****1234`。
- 每个用户只能读写自己的模型配置。

## 提醒与 n8n

后端会定时检查待跟进投递和即将面试，并推送 Webhook。

配置：

```env
REMINDER_WEBHOOK_URL=https://example.com/webhook
REMINDER_CHECK_INTERVAL_MINUTES=60
```

n8n 已加入 `docker-compose.yml`：

```text
http://localhost:5678
```

可以在 n8n 中创建定时工作流，调用 OfferFlow API 或接收 Webhook，再发送到企业微信、钉钉、邮件等渠道。

仓库提供了基础工作流模板：

```text
n8n/workflows/offerflow-reminders.json
```

可在 n8n 工作流页面导入该文件，并替换其中的 `REMINDER_SERVICE_TOKEN`。

## CI

GitHub Actions 已配置：

- 后端 `pytest`
- 前端 `npm run lint`
- 前端 `npm run build`
- Docker 镜像构建

配置文件：`.github/workflows/ci.yml`

## 测试

```bash
uv run python -m pytest backend/tests -q

cd frontend
npm run lint
npm run build
```

数据库备份：

```bash
python scripts/backup_db.py
```

## API 概览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/v1/auth/register` | 注册 |
| `POST` | `/api/v1/auth/login` | 登录 |
| `GET` | `/api/v1/auth/me` | 当前用户 |
| `POST` | `/api/v1/user/model-config` | 保存模型配置 |
| `GET` | `/api/v1/user/model-config` | 获取模型配置 |
| `POST` | `/api/v1/jd/parse` | 解析 JD |
| `POST` | `/api/v1/jd/ocr` | OCR 识别并导入 JD |
| `POST` | `/api/v1/interview/articles/ocr` | OCR 识别并导入面经 |
| `POST` | `/api/v1/match` | 计算匹配度 |
| `POST` | `/api/v1/match/batch` | 批量匹配 JD |
| `POST` | `/api/v1/resume-generation/generate` | 生成简历 |
| `POST` | `/api/v1/resume-generation/regenerate-section-variants` | 逐段重生成（多候选） |
| `POST` | `/api/v1/resume/optimize` | 优化简历 |
| `GET` | `/api/v1/resume/{id}/export` | 导出简历 |
| `POST` | `/api/v1/interview/simulate/start` | 开始模拟面试 |
| `POST` | `/api/v1/interview/simulate/{id}/finish` | 提前结束模拟面试 |
| `POST` | `/api/v1/salary-negotiation/start` | 开始薪资谈判 |
| `POST` | `/api/v1/salary-negotiation/reference` | 薪资参考（根据简历估市场价） |
| `POST` | `/api/v1/salary-negotiation/{id}/answer` | 提交谈判回应 |
| `GET` | `/api/v1/applications/reminders` | 获取提醒 |
| `GET` | `/api/v1/applications/reminders/export` | n8n 提醒导出接口 |

完整接口见后端 `/docs`。

## 简历亮点

- 基于 FastAPI + LangGraph + React 构建求职全流程 Agent，覆盖简历生成、职位要求分析、语义匹配、简历优化、面试准备、薪资谈判、投递看板。
- 核心差异化：简历生成/优化/面试题参考答案均有「事实保真」硬校验（关键信息绝不丢失、不编造）；一页约束用「三刀裁剪」做内容取舍而非压缩字号；薪资谈判用「实时教练点评」指出用户接受了对方的框架。
- 结构化简历生成：15 个求职方向模板 + 19 个行业真实范文 few-shot + 字数约束（800±100）+ 逐段重生成给多候选。
- 面试题生成带「能脱稿讲」的参考答案，并按真实 JD 词频增强 ATS 技能识别。
- 实现注册登录、用户数据隔离、BYOK 模型设置、CI 和一键 Docker 部署，界面全中文、面向零基础应届生。

## 已知限制

- OCR 依赖 Docker 镜像中的 Tesseract 中文语言包，构建镜像时已安装。
- n8n 容器已加入部署，但工作流需要在 n8n UI 中按实际渠道配置。
- 项目截图和线上访问地址需要在部署后补充。

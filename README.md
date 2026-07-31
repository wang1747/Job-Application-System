# OfferFlow 求职全流程智能 Agent 系统

OfferFlow 是一个面向求职全流程的 Web 应用，覆盖 JD 智能解析、简历优化、面试准备和投递追踪四个核心模块。后端使用 FastAPI + LangGraph 编排 Agent 工作流，前端使用 React + TypeScript + TailwindCSS，开箱即可运行。

## 功能

- **JD 解析**：粘贴职位描述，自动提取公司、职位、硬性要求、技术栈和隐藏信号，支持历史记录管理
- **匹配分析**：选择 JD 与简历，计算技能匹配度并输出差距分析
- **简历优化**：上传 PDF / Markdown / TXT 简历，针对目标 JD 输出优化稿、改动项和 ATS 评分对比，支持多版本管理
- **面试准备**：导入面经文本或文件，自动去重、提取题目；基于简历 + JD + 面经生成面试题；多轮模拟面试并生成总结
- **投递追踪**：看板管理投递状态流转，支持统计、跟进提醒和面试前公司面经推送

## 技术栈

| 层 | 技术 |
| --- | --- |
| 后端 | Python 3.13 / FastAPI / SQLAlchemy |
| Agent | LangChain / LangGraph / ChromaDB |
| LLM | OpenAI 兼容 API（默认 DeepSeek） |
| 前端 | React 19 / TypeScript / Vite / TailwindCSS |
| 部署 | Docker / docker-compose |

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，至少填写 `DEEPSEEK_API_KEY`：

```env
DEEPSEEK_API_KEY=你的API密钥
```

### 2. 启动后端

```bash
uv sync
uv run python run.py
```

后端默认运行在 `http://127.0.0.1:8001`，首次启动会自动建表并写入演示数据。

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://127.0.0.1:5173`。也可以直接运行 `start.bat` 一键启动前后端。

### 4. 运行测试

```bash
uv run python -m pytest backend/tests -q
```

### 5. 前端构建与检查

```bash
cd frontend
npm run build
npm run lint
```

## Docker 部署

```bash
docker compose up --build
```

后端服务运行在 `http://127.0.0.1:8001`。`docker-compose.yml` 中的 `DEEPSEEK_API_KEY` 等变量会从项目根目录的 `.env` 读取。

## 演示数据

后端启动时会自动填充演示数据。如需重置，删除根目录 `offerflow.db` 后重新启动后端即可。

## API 概览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `POST` | `/api/v1/jd/parse` | 解析 JD |
| `GET` | `/api/v1/jd/list` | JD 列表 |
| `POST` | `/api/v1/resume/optimize` | 针对 JD 优化简历 |
| `POST` | `/api/v1/match` | 计算匹配度 |
| `GET` | `/api/v1/match/rankings` | 匹配排名 |
| `POST` | `/api/v1/interview/articles` | 导入面经 |
| `POST` | `/api/v1/interview/generate` | 生成面试题 |
| `POST` | `/api/v1/interview/simulate/start` | 开始模拟面试 |
| `GET` | `/api/v1/applications` | 投递列表 |
| `GET` | `/api/v1/applications/reminders` | 跟进提醒 |

完整接口文档见后端启动后的 `http://127.0.0.1:8001/docs`。

## 项目结构

```text
OfferFlow/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph 工作流与 Agent 节点
│   │   ├── api/routes/      # 业务路由
│   │   ├── core/            # 数据库、LLM、向量库
│   │   ├── models/          # SQLAlchemy 模型
│   │   ├── schemas/         # Pydantic 模型
│   │   └── services/        # 业务逻辑
│   └── tests/               # 后端测试
├── frontend/
│   └── src/
│       ├── api/             # API 客户端
│       ├── components/      # 通用组件
│       ├── pages/           # 页面
│       └── types/           # TypeScript 类型
├── docker-compose.yml
├── Dockerfile
├── run.py
└── start.bat
```

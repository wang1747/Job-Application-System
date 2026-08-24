# OfferFlow 前端

OfferFlow 是一个求职全流程智能 Agent 系统的前端，配合 FastAPI 后端使用，提供 JD 解析、匹配分析、简历优化、模拟面试、投递追踪和模型设置等界面。

## 技术栈

- React 19 + TypeScript + Vite
- TailwindCSS
- React Router 7
- Zustand（状态管理）
- Recharts（图表）

## 环境变量

复制 `.env.example` 为 `.env`，按需配置后端地址：

```bash
VITE_API_URL=http://127.0.0.1:8001
```

- 开发环境：后端默认监听 `http://127.0.0.1:8001`。
- 生产环境：由 Nginx 提供同源 `/api` 转发，此时 `VITE_API_URL` 可留空。

## 本地启动

```bash
npm install
npm run dev
```

启动后访问 `http://localhost:5173`。

## 构建

```bash
npm run build
```

构建产物输出到 `dist/`，由 Nginx 静态托管。

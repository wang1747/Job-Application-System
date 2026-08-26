import type { ComponentType, ReactNode } from "react";
import Dashboard from "./pages/Dashboard";
import JDAnalysis from "./pages/JDAnalysis";
import MatchAnalysis from "./pages/MatchAnalysis";
import ResumeOptimize from "./pages/ResumeOptimize";
import InterviewPrep from "./pages/InterviewPrep";
import ApplicationTracker from "./pages/ApplicationTracker";
import CostDashboard from "./pages/CostDashboard";
import ModelSettings from "./pages/ModelSettings";
import UserManagement from "./pages/admin/UserManagement";
import { Icons } from "./components/ui";

/**
 * 模块注册表：侧边栏导航 + 路由的单一数据源。
 *
 * 新增一个模块只需在这里加一条定义，侧边栏和路由会自动生成，
 * 无需改动 Sidebar.tsx / App.tsx，实现模块间互不干扰、方便扩展。
 */
export interface AppModule {
  /** 唯一标识 */
  key: string;
  /** 路由路径 */
  path: string;
  /** 侧边栏显示名 */
  label: string;
  /** 图标 */
  icon: ReactNode;
  /** 页面组件 */
  component: ComponentType;
  /** 分组：工作区 / 系统 / 管理员 */
  section: "workspace" | "system" | "admin";
  /** 是否需要先完成模型配置（走 ModelConfigGate） */
  requireModel?: boolean;
  /** 是否精确匹配路由（如首页 "/"） */
  end?: boolean;
}

export const MODULES: AppModule[] = [
  {
    key: "dashboard",
    path: "/",
    label: "总览",
    icon: Icons.dashboard,
    component: Dashboard,
    section: "workspace",
    end: true,
  },
  {
    key: "jd",
    path: "/jd",
    label: "JD 解析",
    icon: Icons.sparkle,
    component: JDAnalysis,
    section: "workspace",
    requireModel: true,
  },
  {
    key: "resume",
    path: "/resume",
    label: "简历优化",
    icon: Icons.resume,
    component: ResumeOptimize,
    section: "workspace",
    requireModel: true,
  },
  {
    key: "match",
    path: "/match",
    label: "匹配分析",
    icon: Icons.match,
    component: MatchAnalysis,
    section: "workspace",
  },
  {
    key: "interview",
    path: "/interview",
    label: "面试准备",
    icon: Icons.interview,
    component: InterviewPrep,
    section: "workspace",
    requireModel: true,
  },
  {
    key: "applications",
    path: "/applications",
    label: "投递追踪",
    icon: Icons.track,
    component: ApplicationTracker,
    section: "workspace",
  },
  {
    key: "cost",
    path: "/cost",
    label: "成本看板",
    icon: Icons.chart,
    component: CostDashboard,
    section: "workspace",
  },
  {
    key: "settings",
    path: "/settings",
    label: "模型设置",
    icon: Icons.settings,
    component: ModelSettings,
    section: "system",
  },
  {
    key: "admin_users",
    path: "/admin/users",
    label: "用户管理",
    icon: Icons.admin,
    component: UserManagement,
    section: "admin",
  },
];

export const WORKSPACE_MODULES = MODULES.filter((m) => m.section === "workspace");
export const SYSTEM_MODULES = MODULES.filter((m) => m.section === "system");
export const ADMIN_MODULES = MODULES.filter((m) => m.section === "admin");

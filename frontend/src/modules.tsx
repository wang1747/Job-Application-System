import type { ComponentType, ReactNode } from "react";
import Dashboard from "./pages/Dashboard";
import JobMatch from "./pages/JobMatch";
import ResumeOptimize from "./pages/ResumeOptimize";
import ResumeGenerate from "./pages/ResumeGenerate";
import InterviewPrep from "./pages/InterviewPrep";
import SalaryNegotiation from "./pages/SalaryNegotiation";
import ApplicationTracker from "./pages/ApplicationTracker";
import CostDashboard from "./pages/CostDashboard";
import Settings from "./pages/Settings";
import Community from "./pages/Community";
import AdminConsole from "./pages/admin/AdminConsole";
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
  /** 侧边栏副标题（小字，帮助区分相近模块） */
  subtitle?: string;
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
    subtitle: "求职进展一览",
    icon: Icons.dashboard,
    component: Dashboard,
    section: "workspace",
    end: true,
  },
  {
    key: "resume_generate",
    path: "/resume/generate",
    label: "简历生成",
    subtitle: "没有简历，从零做一份",
    icon: Icons.rocket,
    component: ResumeGenerate,
    section: "workspace",
    requireModel: true,
    end: true,
  },
  {
    key: "job",
    path: "/job",
    label: "岗位分析",
    subtitle: "拆解岗位 + 算匹配度",
    icon: Icons.sparkle,
    component: JobMatch,
    section: "workspace",
    requireModel: true,
  },
  {
    key: "resume",
    path: "/resume",
    label: "简历优化",
    subtitle: "已有简历，针对岗位改",
    icon: Icons.resume,
    component: ResumeOptimize,
    section: "workspace",
    requireModel: true,
    end: true,
  },
  {
    key: "interview",
    path: "/interview",
    label: "面试准备",
    subtitle: "面经库 + 模拟面试",
    icon: Icons.interview,
    component: InterviewPrep,
    section: "workspace",
    requireModel: true,
  },
  {
    key: "salary_negotiation",
    path: "/salary-negotiation",
    label: "薪资",
    subtitle: "先估市场价，再演练谈薪",
    icon: Icons.money,
    component: SalaryNegotiation,
    section: "workspace",
    requireModel: true,
  },
  {
    key: "applications",
    path: "/applications",
    label: "投递追踪",
    subtitle: "投递进度看板",
    icon: Icons.track,
    component: ApplicationTracker,
    section: "workspace",
  },
  {
    key: "community",
    path: "/community",
    label: "交流中心",
    subtitle: "分享与建议",
    icon: Icons.interview,
    component: Community,
    section: "workspace",
  },
  {
    key: "preferences",
    path: "/preferences",
    label: "设置",
    subtitle: "资料、安全与偏好",
    icon: Icons.settings,
    component: Settings,
    section: "system",
  },
  {
    key: "cost",
    path: "/cost",
    label: "AI 用量与成本",
    subtitle: "查看消耗明细",
    icon: Icons.chart,
    component: CostDashboard,
    section: "system",
  },
  {
    key: "admin",
    path: "/admin",
    label: "管理后台",
    subtitle: "用户与内容治理",
    icon: Icons.admin,
    component: AdminConsole,
    section: "admin",
  },
];

export const WORKSPACE_MODULES = MODULES.filter((m) => m.section === "workspace");
export const SYSTEM_MODULES = MODULES.filter((m) => m.section === "system");
export const ADMIN_MODULES = MODULES.filter((m) => m.section === "admin");

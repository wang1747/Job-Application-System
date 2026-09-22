import { useState, type ReactNode } from "react";
import { PageHeader, Tabs, Icons } from "../../components/ui";
import UserManagement from "./UserManagement";
import FeedbackManage from "./FeedbackManage";
import CommunityManage from "./CommunityManage";
import AccountSecurity from "./AccountSecurity";

type AdminTab = "users" | "feedback" | "community" | "security";

const TABS: { key: AdminTab; label: string; icon: ReactNode }[] = [
  { key: "users", label: "用户管理", icon: Icons.admin },
  { key: "feedback", label: "建议反馈", icon: Icons.alert },
  { key: "community", label: "社区内容", icon: Icons.interview },
  { key: "security", label: "账号安全", icon: Icons.settings },
];

export default function AdminConsole() {
  const [tab, setTab] = useState<AdminTab>("users");

  return (
    <div>
      <PageHeader
        title="管理后台"
        subtitle="用户、内容与系统治理"
        icon={Icons.admin}
      />

      <Tabs
        tabs={TABS}
        active={tab}
        onChange={(k) => setTab(k as AdminTab)}
      />

      {tab === "users" && <UserManagement />}
      {tab === "feedback" && <FeedbackManage />}
      {tab === "community" && <CommunityManage />}
      {tab === "security" && <AccountSecurity />}
    </div>
  );
}

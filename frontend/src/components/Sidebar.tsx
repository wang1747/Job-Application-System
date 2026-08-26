import { NavLink, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import { Icons } from "./ui";
import {
  WORKSPACE_MODULES,
  SYSTEM_MODULES,
  ADMIN_MODULES,
  type AppModule,
} from "../modules";

function NavItem({ module }: { module: AppModule }) {
  return (
    <NavLink
      to={module.path}
      end={module.end}
      className={({ isActive }) =>
        `group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
          isActive
            ? "bg-brand-600 text-white shadow-lg shadow-brand-600/20"
            : "text-slate-400 hover:bg-white/5 hover:text-white"
        }`
      }
    >
      <span className="flex h-5 w-5 items-center justify-center">{module.icon}</span>
      {module.label}
    </NavLink>
  );
}

export default function Sidebar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isAdmin = user?.role === "admin";

  return (
    <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col bg-gradient-to-b from-slate-900 via-slate-900 to-brand-950">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 text-sm font-black text-white shadow-lg shadow-brand-600/30">
          OF
        </div>
        <div>
          <p className="text-sm font-bold text-white">OfferFlow</p>
          <p className="text-[10px] font-medium text-slate-400">求职智能助手</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-2">
        <p className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
          工作区
        </p>
        {WORKSPACE_MODULES.map((mod) => (
          <NavItem key={mod.key} module={mod} />
        ))}

        <p className="px-3 pt-5 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
          系统
        </p>
        {SYSTEM_MODULES.map((mod) => (
          <NavItem key={mod.key} module={mod} />
        ))}

        {isAdmin &&
          ADMIN_MODULES.map((mod) => <NavItem key={mod.key} module={mod} />)}
      </nav>

      {/* User */}
      <div className="border-t border-white/5 px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-slate-600 to-slate-700 text-xs font-bold text-white">
            {user?.name?.charAt(0).toUpperCase() || "U"}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-white">{user?.name}</p>
            <p className="text-[10px] text-slate-400">{isAdmin ? "管理员" : "成员"}</p>
          </div>
          <button
            onClick={handleLogout}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition hover:bg-white/5 hover:text-rose-400"
            title="退出登录"
          >
            {Icons.logout}
          </button>
        </div>
      </div>
    </aside>
  );
}

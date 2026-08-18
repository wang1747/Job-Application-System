import { type FC } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

interface SidebarProps {
  active: string;
  onNavigate: (page: string) => void;
}

const navItems = [
  { key: "dashboard", label: "总览", icon: "总", path: "/" },
  { key: "jd", label: "JD 解析", icon: "JD", path: "/jd" },
  { key: "match", label: "匹配分析", icon: "匹", path: "/match" },
  { key: "resume", label: "简历优化", icon: "简", path: "/resume" },
  { key: "interview", label: "面试准备", icon: "面", path: "/interview" },
  { key: "applications", label: "投递追踪", icon: "投", path: "/applications" },
  { key: "settings", label: "模型设置", icon: "设", path: "/settings" },
];

const Sidebar: FC<SidebarProps> = ({ active, onNavigate }) => {
  const navigate = useNavigate();
  const { logout } = useAuthStore();

  const handleNavigate = (key: string, path: string) => {
    onNavigate(key);
    navigate(path);
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <aside className="sticky top-0 flex h-screen w-64 flex-col bg-slate-950 text-slate-200 shadow-2xl">
      <div className="flex h-20 items-center border-b border-white/10 px-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-500 text-sm font-black text-white shadow-lg shadow-indigo-500/25">
          OF
        </div>
        <div className="ml-3">
          <div className="text-lg font-bold tracking-tight text-white">OfferFlow</div>
          <div className="text-xs text-slate-400">求职智能助手</div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5">
        {navItems.map((item) => {
          const isActive = active === item.key;
          return (
            <button
              key={item.key}
              onClick={() => handleNavigate(item.key, item.path)}
              className={`group flex h-11 w-full items-center gap-3 rounded-xl px-3 text-left transition ${
                isActive
                  ? "bg-white/10 text-white shadow-inner"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-100"
              }`}
            >
              <span
                className={`flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold transition ${
                  isActive
                    ? "bg-indigo-500 text-white shadow-md shadow-indigo-500/20"
                    : "bg-white/5 text-slate-400 group-hover:text-white"
                }`}
              >
                {item.icon}
              </span>
              <span className="text-sm font-medium">{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="border-t border-white/10 p-3">
        <button
          onClick={handleLogout}
          className="flex h-11 w-full items-center justify-center gap-2 rounded-xl border border-white/10 text-sm font-medium text-rose-300 transition hover:border-rose-400/30 hover:bg-rose-500/10"
        >
          退出登录
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;

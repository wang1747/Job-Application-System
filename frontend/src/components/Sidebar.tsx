import { type FC } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

interface SidebarProps {
  active: string;
  onNavigate: (page: string) => void;
}

const navItems = [
  { key: "match", label: "匹配分析", path: "/match" },
  { key: "dashboard", label: "📊 总览", path: "/" },
  { key: "jd", label: "📄 JD 解析", path: "/jd" },
  { key: "resume", label: "📝 简历优化", path: "/resume" },
  { key: "interview", label: "🎯 面试准备", path: "/interview" },
  { key: "applications", label: "📋 投递追踪", path: "/applications" },
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
    <aside
      style={{
        width: 220,
        background: "#1a1a2e",
        color: "#eee",
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        position: "sticky",
        top: 0,
        padding: "16px 0",
      }}
    >
      <div
        style={{
          padding: "16px 20px",
          fontSize: 20,
          fontWeight: "bold",
          color: "#e94560",
          borderBottom: "1px solid #2a2a4e",
          marginBottom: 12,
        }}
      >
        OfferFlow
      </div>

      <nav style={{ flex: 1 }}>
        {navItems.map((item) => (
          <div
            key={item.key}
            onClick={() => handleNavigate(item.key, item.path)}
            style={{
              padding: "12px 20px",
              cursor: "pointer",
              background: active === item.key ? "#16213e" : "transparent",
              borderLeft:
                active === item.key ? "3px solid #e94560" : "3px solid transparent",
              color: active === item.key ? "#fff" : "#aaa",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              if (active !== item.key) {
                e.currentTarget.style.background = "#1e2a4a";
              }
            }}
            onMouseLeave={(e) => {
              if (active !== item.key) {
                e.currentTarget.style.background = "transparent";
              }
            }}
          >
            {item.label}
          </div>
        ))}
      </nav>

      <div
        style={{
          padding: "12px 20px",
          borderTop: "1px solid #2a2a4e",
          marginTop: 12,
        }}
      >
        <div
          onClick={handleLogout}
          style={{
            padding: "10px 12px",
            cursor: "pointer",
            color: "#e94560",
            borderRadius: 6,
            transition: "all 0.2s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "#2a1a2e";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
          }}
        >
          🚪 退出登录
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;

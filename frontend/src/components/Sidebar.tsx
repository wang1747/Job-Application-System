import { type FC } from "react";

interface SidebarProps {
  active: string;
  onNavigate: (page: string) => void;
}

const navItems = [
  { key: "dashboard", label: "总览" },
  { key: "jd", label: "JD 解析" },
  { key: "match", label: "匹配分析" },
  { key: "resume", label: "简历优化" },
  { key: "interview", label: "面试准备" },
  { key: "applications", label: "投递追踪" },
];

const Sidebar: FC<SidebarProps> = ({ active, onNavigate }) => {
  return (
    <aside style={{
      width: 200,
      background: "#1a1a2e",
      color: "#eee",
      display: "flex",
      flexDirection: "column",
      padding: "16px 0",
    }}>
      <div style={{ padding: "16px 20px", fontSize: 20, fontWeight: "bold", color: "#e94560" }}>
        OfferFlow
      </div>
      <nav style={{ flex: 1 }}>
        {navItems.map((item) => (
          <div
            key={item.key}
            onClick={() => onNavigate(item.key)}
            style={{
              padding: "12px 20px",
              cursor: "pointer",
              background: active === item.key ? "#16213e" : "transparent",
              borderLeft: active === item.key ? "3px solid #e94560" : "3px solid transparent",
              color: active === item.key ? "#fff" : "#aaa",
            }}
          >
            {item.label}
          </div>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;

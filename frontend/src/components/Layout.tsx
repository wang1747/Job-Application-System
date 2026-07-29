import { type FC, type ReactNode, useState } from "react";
import Sidebar from "./Sidebar";

const pages: Record<string, ReactNode> = {
  dashboard: null,
  jd: null,
  resume: null,
  interview: null,
  applications: null,
};

interface LayoutProps {
  children: (page: string) => ReactNode;
}

const Layout: FC<LayoutProps> = ({ children }) => {
  const [active, setActive] = useState("dashboard");

  return (
    <div style={{ display: "flex", height: "100vh", background: "#f0f2f5" }}>
      <Sidebar active={active} onNavigate={setActive} />
      <main style={{ flex: 1, overflow: "auto", padding: 24 }}>
        {children(active)}
      </main>
    </div>
  );
};

export default Layout;

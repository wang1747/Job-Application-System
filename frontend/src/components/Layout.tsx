import { type FC, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";

interface LayoutProps {
  children: ReactNode;
}

const Layout: FC<LayoutProps> = ({ children }) => {
  const location = useLocation();

  const active =
    location.pathname === "/"
      ? "dashboard"
      : location.pathname.startsWith("/jd")
        ? "jd"
        : location.pathname.startsWith("/match")
          ? "match"
          : location.pathname.startsWith("/resume")
            ? "resume"
            : location.pathname.startsWith("/interview")
              ? "interview"
              : location.pathname.startsWith("/applications")
                ? "applications"
                : "dashboard";

  return (
    <div style={{ display: "flex", height: "100vh", background: "#f0f2f5" }}>
      <Sidebar active={active} onNavigate={() => {}} />
      <main style={{ flex: 1, overflow: "auto", padding: 24 }}>
        {children}
      </main>
    </div>
  );
};

export default Layout;

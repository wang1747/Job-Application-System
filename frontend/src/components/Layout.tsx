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
                : location.pathname.startsWith("/settings")
                  ? "settings"
                  : "dashboard";

  return (
    <div className="flex min-h-screen bg-[#f4f6fb] text-slate-900">
      <Sidebar active={active} onNavigate={() => {}} />
      <main className="min-w-0 flex-1 overflow-auto px-4 py-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
};

export default Layout;

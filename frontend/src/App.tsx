import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import Layout from "./components/Layout";
import ModelConfigGate from "./components/ModelConfigGate";
import { MODULES, type AppModule } from "./modules";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, initialized } = useAuthStore();
  if (!initialized) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user, initialized } = useAuthStore();
  if (!initialized) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user?.role !== "admin") return <Navigate to="/" replace />;
  return <>{children}</>;
}

/** 根据模块定义渲染页面 + 守卫 + 模型配置门禁。 */
function renderModule(mod: AppModule) {
  const Component = mod.component;
  const inner = (
    <Layout>
      {mod.requireModel ? (
        <ModelConfigGate>
          <Component />
        </ModelConfigGate>
      ) : (
        <Component />
      )}
    </Layout>
  );
  return mod.section === "admin" ? <AdminRoute>{inner}</AdminRoute> : <PrivateRoute>{inner}</PrivateRoute>;
}

function App() {
  const { initialize } = useAuthStore();

  useEffect(() => {
    initialize();
  }, [initialize]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        {MODULES.map((mod) => (
          <Route key={mod.key} path={mod.path} element={renderModule(mod)} />
        ))}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

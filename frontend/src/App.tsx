import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "./store/authStore";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import JDAnalysis from "./pages/JDAnalysis";
import MatchAnalysis from "./pages/MatchAnalysis";
import ResumeOptimize from "./pages/ResumeOptimize";
import InterviewPrep from "./pages/InterviewPrep";
import ApplicationTracker from "./pages/ApplicationTracker";
import ModelSettings from "./pages/ModelSettings";
import ModelConfigGate from "./components/ModelConfigGate";
import UserManagement from "./pages/admin/UserManagement";
import CostDashboard from "./pages/CostDashboard";

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
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/jd"
          element={
            <PrivateRoute>
              <Layout>
                <ModelConfigGate>
                  <JDAnalysis />
                </ModelConfigGate>
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/match"
          element={
            <PrivateRoute>
              <Layout>
                <MatchAnalysis />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/resume"
          element={
            <PrivateRoute>
              <Layout>
                <ModelConfigGate>
                  <ResumeOptimize />
                </ModelConfigGate>
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/interview"
          element={
            <PrivateRoute>
              <Layout>
                <ModelConfigGate>
                  <InterviewPrep />
                </ModelConfigGate>
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/applications"
          element={
            <PrivateRoute>
              <Layout>
                <ApplicationTracker />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/cost"
          element={
            <PrivateRoute>
              <Layout>
                <CostDashboard />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <PrivateRoute>
              <Layout>
                <ModelSettings />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/admin/users"
          element={
            <AdminRoute>
              <Layout>
                <UserManagement />
              </Layout>
            </AdminRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

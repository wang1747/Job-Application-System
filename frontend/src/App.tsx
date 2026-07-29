import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import JDAnalysis from "./pages/JDAnalysis";
import ResumeOptimize from "./pages/ResumeOptimize";
import InterviewPrep from "./pages/InterviewPrep";
import ApplicationTracker from "./pages/ApplicationTracker";

const pageMap: Record<string, React.ReactNode> = {
  dashboard: <Dashboard />,
  jd: <JDAnalysis />,
  resume: <ResumeOptimize />,
  interview: <InterviewPrep />,
  applications: <ApplicationTracker />,
};

function App() {
  return (
    <Layout>
      {(active) => pageMap[active] || <Dashboard />}
    </Layout>
  );
}

export default App;

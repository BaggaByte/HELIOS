import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Sidebar } from './components/layout/Sidebar';
import { TopBar } from './components/layout/TopBar';
import { ChatPanel } from './features/chat/ChatPanel';
import { ReconDashboard } from './features/recon/ReconDashboard';
import { WebSecurityDashboard } from './features/web/WebSecurityDashboard';
import { SourceCodeDashboard } from './features/code/SourceCodeDashboard';
import { LogDashboard } from './features/logs/LogDashboard';
import { MalwareDashboard } from './features/malware/MalwareDashboard';
import { GraphDashboard } from './features/knowledge-graph/GraphDashboard';
import { EvidenceDashboard } from './features/evidence/EvidenceDashboard';
import { ReportsDashboard } from './features/reports/ReportsDashboard';
import { JsIntelDashboard } from './features/js-intel/JsIntelDashboard';
import { MainDashboard } from './features/dashboard/MainDashboard';
import { SettingsDashboard } from './features/settings/SettingsDashboard';

// Professional 404 Component
const NotFound = () => (
  <div className="flex flex-col items-center justify-center h-full text-center p-6">
    <h1 className="text-6xl font-bold text-border-active mb-4">404</h1>
    <h2 className="text-2xl font-semibold text-gray-200 mb-2">Page Not Found</h2>
    <p className="text-gray-400 mb-8 max-w-md">
      The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
    </p>
    <Link 
      to="/" 
      className="px-6 py-2.5 bg-border-active text-white font-medium rounded-lg hover:bg-opacity-90 transition-all shadow-lg hover:shadow-md"
    >
      Back to Dashboard
    </Link>
  </div>
);

import { useAuthStore } from './stores/authStore';
import { Login } from './features/auth/Login';

function App() {
  const token = useAuthStore(state => state.token);

  if (!token) {
    return <Login />;
  }

  return (
      <Router>
        {/* Skip to main content link for accessibility (screen readers / keyboard users) */}
        <a 
          href="#main-content" 
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-border-active focus:text-white focus:rounded-md"
        >
          Skip to main content
        </a>

        <div className="flex h-screen overflow-hidden bg-surface-primary bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-surface-tertiary/20 via-surface-primary to-surface-primary text-gray-200">
          <Sidebar />
          
          <div className="flex flex-col flex-1 overflow-hidden relative">
            {/* Background ambient glow */}
            <div className="absolute top-[-10%] right-[-5%] w-[40%] h-[40%] bg-border-active/10 blur-[120px] rounded-full pointer-events-none" />
            
            <TopBar />
            
            {/* id="main-content" links to the skip-nav above. tabIndex={-1} allows it to receive programmatic focus */}
            <main id="main-content" className="flex-1 overflow-y-auto" tabIndex={-1}>
              <Routes>
                <Route path="/" element={<MainDashboard />} />
                <Route path="/chat" element={<ChatPanel />} />
                <Route path="/recon" element={<ReconDashboard />} />
                <Route path="/web" element={<WebSecurityDashboard />} />
                <Route path="/code" element={<SourceCodeDashboard />} />
                <Route path="/logs" element={<LogDashboard />} />
                <Route path="/malware" element={<MalwareDashboard />} />
                <Route path="/graph" element={<GraphDashboard />} />
                <Route path="/evidence" element={<EvidenceDashboard />} />
                <Route path="/reports" element={<ReportsDashboard />} />
                <Route path="/js-intel" element={<JsIntelDashboard />} />
                <Route path="/settings" element={<SettingsDashboard />} />
                
                {/* Catch-all route for 404 */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </main>
          </div>
        </div>
      </Router>
  );
}

export default App;

import {
  Activity,
  Target,
  ShieldAlert,
  Bug,
  Network,
  ShieldCheck,
  Zap,
  Globe,
  Code2,
  FileBox,
  Terminal,
  ExternalLink,
  ChevronRight,
  Lock,
  Flame,
  Loader2
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

import { useRecon } from '../../hooks/useRecon';
import { useWebSecurity } from '../../hooks/useWebSecurity';
import { useLogs } from '../../hooks/useLogs';
import { useEvidence } from '../../hooks/useEvidence';
import { useProjectStore } from '../../stores/projectStore';

export function MainDashboard() {
  const navigate = useNavigate();
  const { hosts, isLoading: reconLoading, error: reconError, refetch: refetchRecon } = useRecon();
  const { findings, isLoading: webLoading, error: webError, refetch: refetchWeb } = useWebSecurity();
  const { events, isLoading: logsLoading, error: logsError, refetch: refetchLogs } = useLogs();
  const { evidenceList, isLoading: evidenceLoading, error: evidenceError, refetch: refetchEvidence } = useEvidence();
  const activeProjectId = useProjectStore(state => state.activeProjectId);

  const displayHosts = hosts ?? [];
  const discoveredServicesCount = displayHosts.reduce((acc, host) => acc + (host.services?.length || 0), 0);
  const criticalFindings = findings?.filter(f => f.severity.toUpperCase() === 'CRITICAL').length ?? 0;
  const highFindings = findings?.filter(f => f.severity.toUpperCase() === 'HIGH').length ?? 0;

  return (
    <div className="flex flex-col h-full bg-surface-primary overflow-y-auto custom-scrollbar p-6 space-y-6 animate-in fade-in duration-300">
      
      {/* Top Banner / Mission Status */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-5 rounded-2xl bg-surface-secondary border border-border-default shadow-sm">
        <div className="flex items-start gap-4">
          <div className="p-3.5 rounded-xl bg-border-active/15 border border-border-active/30 text-border-active shadow-inner shrink-0">
            <Zap size={28} />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-100 tracking-tight">HELIOS Mission Control</h1>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border flex items-center gap-1.5 ${activeProjectId ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40' : 'bg-amber-500/20 text-amber-300 border-amber-500/40'}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${activeProjectId ? 'bg-emerald-400' : 'bg-amber-300'}`} />
                {activeProjectId ? 'PROJECT SELECTED' : 'NO PROJECT'}
              </span>
            </div>
            <p className="text-sm text-gray-400 mt-1 max-w-2xl">
              Offensive cyber copilot & centralized intelligence platform for security data aggregation, vulnerability triage, and evidence management.
            </p>
          </div>
        </div>

        {/* Engine Telemetry Pillbox */}
        <div className="flex flex-wrap items-center gap-2 self-start lg:self-center">

          <div className="px-3 py-1.5 rounded-lg bg-surface-primary/80 border border-border-default text-xs flex items-center gap-2">
            <Lock size={14} className="text-emerald-400" />
            <span className="text-gray-400">Vault:</span>
            <span className="text-gray-200 font-semibold">Evidence integrity checks</span>
          </div>
        </div>
      </div>

      {/* Primary Key Metrics & Threat Score Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        
        {/* Threat Posture Meter */}
        <div className="p-5 rounded-2xl bg-surface-secondary border border-border-default shadow-sm relative overflow-hidden flex flex-col justify-between">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Vulnerability Summary</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-3xl font-black text-gray-100">{findings?.length ?? 0}</span>
                <span className="text-xs text-gray-500">Web Vulnerabilities</span>
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-severity-critical/15 text-severity-critical border border-severity-critical/30">
              <Flame size={20} />
            </div>
          </div>

          <div className="mt-4 flex flex-col gap-1.5">
            {webLoading ? (
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Loader2 size={14} className="animate-spin" />
                <span>Loading vulnerability data...</span>
              </div>
            ) : webError ? (
              <div className="flex items-center gap-2 text-xs text-red-400 group cursor-pointer" onClick={(e) => { e.preventDefault(); refetchWeb(); }}>
                <ShieldAlert size={14} />
                <span className="group-hover:underline">Failed to load. Click to retry.</span>
              </div>
            ) : (
              <>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-severity-critical font-bold">{criticalFindings} Critical</span>
                  <div className="flex-1 h-1 bg-surface-tertiary mx-2 rounded-full overflow-hidden">
                    <div className="h-full bg-severity-critical" style={{ width: findings?.length ? `${(criticalFindings / findings.length) * 100}%` : '0%' }} />
                  </div>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-severity-high font-bold">{highFindings} High</span>
                  <div className="flex-1 h-1 bg-surface-tertiary mx-2 rounded-full overflow-hidden">
                    <div className="h-full bg-severity-high" style={{ width: findings?.length ? `${(highFindings / findings.length) * 100}%` : '0%' }} />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Active Recon Targets */}
        <Link 
          to="/recon"
          className="p-5 rounded-2xl bg-surface-secondary border border-border-default hover:border-border-active/60 transition-all shadow-sm group flex flex-col justify-between"
        >
          <div className="flex items-start justify-between">
            <div>
              <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Discovered Hosts</span>
              <div className="text-3xl font-black text-gray-100 mt-1">
                {reconLoading ? (
                  <div className="flex items-center gap-2 mt-2">
                    <Loader2 size={18} className="animate-spin text-blue-500/50" />
                    <span className="text-sm font-normal text-gray-400">Loading hosts...</span>
                  </div>
                ) : reconError ? (
                  <div className="flex items-center gap-2 mt-2 group cursor-pointer" onClick={(e) => { e.preventDefault(); refetchRecon(); }}>
                    <ShieldAlert size={18} className="text-red-500/70" />
                    <span className="text-sm font-normal text-red-400/80 group-hover:underline">Retry connection</span>
                  </div>
                ) : (
                  `${displayHosts.length} Hosts`
                )}
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-blue-500/15 text-blue-400 border border-blue-500/30 group-hover:scale-105 transition-transform">
              <Target size={20} />
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
            <span className="text-gray-300">{discoveredServicesCount} discovered services</span>
            <ChevronRight size={14} className="text-border-active group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>

        {/* Web Vulnerabilities & Exploits */}
        <Link 
          to="/web"
          className="p-5 rounded-2xl bg-surface-secondary border border-border-default hover:border-border-active/60 transition-all shadow-sm group flex flex-col justify-between"
        >
          <div className="flex items-start justify-between">
            <div>
              <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Web Security</span>
              <div className="text-3xl font-black text-amber-400 mt-1">
                {webLoading ? (
                  <div className="flex items-center gap-2 mt-2">
                    <Loader2 size={18} className="animate-spin text-amber-500/50" />
                    <span className="text-sm font-normal text-gray-400">Loading findings...</span>
                  </div>
                ) : webError ? (
                  <div className="flex items-center gap-2 mt-2 group cursor-pointer" onClick={(e) => { e.preventDefault(); refetchWeb(); }}>
                    <ShieldAlert size={18} className="text-red-500/70" />
                    <span className="text-sm font-normal text-red-400/80 group-hover:underline">Retry connection</span>
                  </div>
                ) : (
                  `${findings?.length ?? 0} Findings`
                )}
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-amber-500/15 text-amber-400 border border-amber-500/30 group-hover:scale-105 transition-transform">
              <Globe size={20} />
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
            <span className="text-gray-300">ZAP XML Import</span>
            <ChevronRight size={14} className="text-border-active group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>

        {/* Cryptographic Evidence Locker */}
        <Link 
          to="/evidence"
          className="p-5 rounded-2xl bg-surface-secondary border border-border-default hover:border-border-active/60 transition-all shadow-sm group flex flex-col justify-between"
        >
          <div className="flex items-start justify-between">
            <div>
              <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Evidence Locker</span>
              <div className="text-3xl font-black text-emerald-400 mt-1">
                {evidenceLoading ? (
                  <div className="flex items-center gap-2 mt-2">
                    <Loader2 size={18} className="animate-spin text-emerald-500/50" />
                    <span className="text-sm font-normal text-gray-400">Loading evidence...</span>
                  </div>
                ) : evidenceError ? (
                  <div className="flex items-center gap-2 mt-2 group cursor-pointer" onClick={(e) => { e.preventDefault(); refetchEvidence(); }}>
                    <ShieldAlert size={18} className="text-red-500/70" />
                    <span className="text-sm font-normal text-red-400/80 group-hover:underline">Retry connection</span>
                  </div>
                ) : (
                  `${evidenceList?.length ?? 0} Vault Items`
                )}
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 group-hover:scale-105 transition-transform">
              <ShieldCheck size={20} />
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
            <span className="text-emerald-400">Stored Evidence</span>
            <ChevronRight size={14} className="text-border-active group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>

      </div>

      {/* Tactical Quick-Launch Operations Ribbon */}
      <div className="p-4 rounded-2xl bg-surface-secondary border border-border-default">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Terminal size={16} className="text-border-active" />
            <h3 className="text-xs font-bold text-gray-300 uppercase tracking-wider">Tactical Quick Launch</h3>
          </div>
          <span className="text-xs text-gray-500">Project Tools</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
          <button
            onClick={() => navigate('/recon')}
            className="flex flex-col items-center justify-center p-3 rounded-xl bg-surface-tertiary/70 hover:bg-surface-tertiary border border-border-default hover:border-border-active/60 transition-all text-center group"
          >
            <Target size={20} className="text-blue-400 mb-1.5 group-hover:scale-110 transition-transform" />
            <span className="text-xs font-semibold text-gray-200">SYN Recon</span>
            <span className="text-xs text-gray-500">Nmap Ingestion</span>
          </button>

          <button
            onClick={() => navigate('/web')}
            className="flex flex-col items-center justify-center p-3 rounded-xl bg-surface-tertiary/70 hover:bg-surface-tertiary border border-border-default hover:border-border-active/60 transition-all text-center group"
          >
            <Globe size={20} className="text-amber-400 mb-1.5 group-hover:scale-110 transition-transform" />
            <span className="text-xs font-semibold text-gray-200">Web Security</span>
            <span className="text-xs text-gray-500">ZAP Import</span>
          </button>

          <button
            onClick={() => navigate('/code')}
            className="flex flex-col items-center justify-center p-3 rounded-xl bg-surface-tertiary/70 hover:bg-surface-tertiary border border-border-default hover:border-border-active/60 transition-all text-center group"
          >
            <Code2 size={20} className="text-purple-400 mb-1.5 group-hover:scale-110 transition-transform" />
            <span className="text-xs font-semibold text-gray-200">AST Code Audit</span>
            <span className="text-xs text-gray-500">Secret Detector</span>
          </button>

          <button
            onClick={() => navigate('/malware')}
            className="flex flex-col items-center justify-center p-3 rounded-xl bg-surface-tertiary/70 hover:bg-surface-tertiary border border-border-default hover:border-border-active/60 transition-all text-center group"
          >
            <Bug size={20} className="text-rose-400 mb-1.5 group-hover:scale-110 transition-transform" />
            <span className="text-xs font-semibold text-gray-200">Malware Triage</span>
            <span className="text-xs text-gray-500">YARA & Entropy</span>
          </button>

          <button
            onClick={() => navigate('/graph')}
            className="flex flex-col items-center justify-center p-3 rounded-xl bg-surface-tertiary/70 hover:bg-surface-tertiary border border-border-default hover:border-border-active/60 transition-all text-center group"
          >
            <Network size={20} className="text-emerald-400 mb-1.5 group-hover:scale-110 transition-transform" />
            <span className="text-xs font-semibold text-gray-200">Attack Graph</span>
            <span className="text-xs text-gray-500">Path Finding</span>
          </button>

          <button
            onClick={() => navigate('/reports')}
            className="flex flex-col items-center justify-center p-3 rounded-xl bg-surface-tertiary/70 hover:bg-surface-tertiary border border-border-default hover:border-border-active/60 transition-all text-center group"
          >
            <FileBox size={20} className="text-cyan-400 mb-1.5 group-hover:scale-110 transition-transform" />
            <span className="text-xs font-semibold text-gray-200">Report Studio</span>
            <span className="text-xs text-gray-500">Markdown Report</span>
          </button>
        </div>
      </div>

      {/* Main Split: Targets Matrix & MITRE ATT&CK Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Target Infrastructure & Discovered Vulnerabilities */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Target Host Explorer Card */}
          <div className="p-5 rounded-2xl bg-surface-secondary border border-border-default shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Target size={18} className="text-border-active" />
                <h2 className="text-base font-bold text-gray-100">Discovered Target Hosts</h2>
              </div>
              <Link to="/recon" className="text-xs text-border-active hover:underline flex items-center gap-1 font-medium">
                <span>View Full Matrix</span>
                <ExternalLink size={12} />
              </Link>
            </div>

            <div className="space-y-3">
              {reconLoading ? (
                <div className="flex items-center justify-center gap-2 text-sm text-gray-500 py-6 bg-surface-tertiary/20 rounded-xl border border-border-default/50">
                  <Loader2 size={16} className="animate-spin" />
                  <span>Loading target hosts...</span>
                </div>
              ) : reconError ? (
                <button 
                  onClick={() => refetchRecon()}
                  className="w-full flex flex-col items-center justify-center gap-2 text-sm text-red-400 py-6 bg-surface-tertiary/40 rounded-xl border border-red-500/20 hover:bg-surface-tertiary transition-colors"
                >
                  <ShieldAlert size={20} />
                  <span>Failed to load hosts. Click to retry.</span>
                </button>
              ) : displayHosts.length === 0 ? (
                <p className="text-sm text-gray-400">No hosts recorded for this project yet.</p>
              ) : displayHosts.map(host => (
                <div 
                  key={host.id}
                  className="p-3.5 rounded-xl bg-surface-tertiary/60 border border-border-default hover:border-border-active/50 transition-all flex flex-col md:flex-row md:items-center justify-between gap-3"
                >
                  <div className="flex items-start md:items-center gap-3">
                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399] shrink-0 mt-1 md:mt-0" />
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono font-bold text-sm text-gray-100">{host.ip}</span>
                        {host.hostname && (
                          <span className="text-xs text-border-active font-mono bg-border-active/10 px-2 py-0.5 rounded border border-border-active/20">
                            {host.hostname}
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-gray-400 mt-0.5">{host.os || 'Operating system not identified'}</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap">
                    {host.services.map((svc: any, sIdx: number) => (
                      <span 
                        key={svc.id || sIdx}
                        className={`text-xs font-mono px-2 py-0.5 rounded border ${
                          svc.port === 80 || svc.port === 6379 
                            ? 'bg-severity-critical/15 text-severity-critical border-severity-critical/30' 
                            : 'bg-surface-primary text-gray-300 border-border-default'
                        }`}
                        title={svc.version}
                      >
                        {svc.port}/{svc.name || svc.service_name || svc.protocol}
                      </span>
                    ))}
                    <button
                      onClick={() => navigate('/recon')}
                      className="text-xs text-gray-400 hover:text-gray-200 px-2 py-1 rounded bg-surface-primary hover:bg-surface-hover border border-border-default transition-colors"
                    >
                      Open in Recon
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right 1 Col: Live Security Event Timeline & Copilot Widget */}
        <div className="space-y-6">
          
          {/* AI Security Copilot Quick Prompter */}
          <div className="p-5 rounded-2xl bg-surface-secondary border border-border-default shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Zap size={18} className="text-border-active animate-pulse" />
                <h3 className="font-bold text-gray-100 text-sm">HELIOS Copilot AI</h3>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">
                Chat uses the configured local model when available. Its runtime status is shown in Settings.
              </p>
            </div>

            <div className="mt-4 space-y-2">
              <button
                onClick={() => navigate('/chat', { state: { initialPrompt: 'What are the first steps to triage high-severity web vulnerabilities?' } })}
                className="w-full text-left p-2.5 rounded-lg bg-surface-primary/80 hover:bg-border-active/15 border border-border-default hover:border-border-active/40 text-xs text-gray-300 hover:text-gray-100 transition-all"
              >
                &ldquo;How to triage web vulnerabilities?&rdquo;
              </button>
              <button
                onClick={() => navigate('/chat', { state: { initialPrompt: 'What are best practices for securing commonly exposed ports?' } })}
                className="w-full text-left p-2.5 rounded-lg bg-surface-primary/80 hover:bg-border-active/15 border border-border-default hover:border-border-active/40 text-xs text-gray-300 hover:text-gray-100 transition-all"
              >
                &ldquo;Best practices for exposed ports&rdquo;
              </button>
              <Link
                to="/chat"
                className="block text-center w-full py-2 rounded-lg bg-border-active text-white font-semibold text-xs hover:bg-opacity-90 transition-colors shadow-sm"
              >
                Open Copilot Console
              </Link>
            </div>
          </div>

          {/* Live SIEM Log Feed */}
          <div className="p-5 rounded-2xl bg-surface-secondary border border-border-default shadow-sm flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Activity size={16} className="text-border-active" />
                <h3 className="text-sm font-bold text-gray-100">Stored Log Events</h3>
              </div>
              <Link to="/logs" className="text-xs text-border-active hover:underline">Full Feed</Link>
            </div>

            <div className="space-y-2.5 max-h-[320px] overflow-y-auto custom-scrollbar pr-1">
              {logsLoading ? (
                <div className="flex justify-center items-center gap-2 p-4 text-sm text-gray-500">
                  <Loader2 size={16} className="animate-spin" />
                  <span>Loading events...</span>
                </div>
              ) : logsError ? (
                <button 
                  onClick={() => refetchLogs()}
                  className="w-full flex flex-col items-center justify-center gap-2 text-sm text-red-400 p-6 bg-surface-tertiary/40 rounded-xl border border-red-500/20 hover:bg-surface-tertiary transition-colors"
                >
                  <ShieldAlert size={20} />
                  <span>Failed to load events. Click to retry.</span>
                </button>
              ) : (events ?? []).map(evt => (
                <div 
                  key={evt.id}
                  className="p-2.5 rounded-lg bg-surface-tertiary/70 border border-border-default text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className={`px-1.5 py-0.2 rounded text-xs font-bold uppercase border ${
                      evt.severity.toLowerCase() === 'critical' ? 'bg-severity-critical/20 text-severity-critical border-severity-critical/40' :
                      evt.severity.toLowerCase() === 'high' ? 'bg-severity-high/20 text-severity-high border-severity-high/40' :
                      'bg-severity-info/20 text-severity-info border-severity-info/40'
                    }`}>
                      {evt.severity}
                    </span>
                    <span className="text-xs text-gray-500">{evt.source}</span>
                  </div>
                  <p className="text-gray-300 line-clamp-2">{evt.message}</p>
                </div>
              ))}
              {!logsLoading && !logsError && (!events || events.length === 0) && <p className="text-xs text-gray-400 p-2">No events recorded for this project yet.</p>}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}

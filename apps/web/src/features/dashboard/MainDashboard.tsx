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
  Cpu,
  Lock,
  Flame
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

import { useRecon } from '../../hooks/useRecon';
import { useWebSecurity } from '../../hooks/useWebSecurity';
import { useLogs } from '../../hooks/useLogs';
import { useEvidence } from '../../hooks/useEvidence';

const DEFAULT_SIEM_EVENTS = [
  {
    id: 'e-1',
    severity: 'critical',
    source: 'suricata',
    timestamp: '2026-08-24T00:00:00.000Z',
    message: 'ET EXPLOIT Apache Path Traversal (CVE-2021-41773) from 198.51.100.45'
  },
  {
    id: 'e-2',
    severity: 'high',
    source: 'linux_auth',
    timestamp: '2026-08-23T23:55:00.000Z',
    message: 'SSH invalid user admin brute force from 203.0.113.88'
  },
  {
    id: 'e-3',
    severity: 'medium',
    source: 'nginx',
    timestamp: '2026-08-23T23:45:00.000Z',
    message: 'HTTP 403 probe on /api/v1/dump_config from 198.51.100.72'
  }
];

export function MainDashboard() {
  const navigate = useNavigate();
  const { hosts } = useRecon();
  const { findings } = useWebSecurity();
  const { events } = useLogs();
  const { evidenceList } = useEvidence();

  const openPorts = hosts?.reduce((acc, host) => acc + (host.services?.length || 0), 0) || 14;
  const criticalFindings = findings?.filter(f => f.severity.toUpperCase() === 'CRITICAL').length || 2;
  const highFindings = findings?.filter(f => f.severity.toUpperCase() === 'HIGH').length || 4;

  // Demo targets if recon store not loaded yet
  const displayHosts = hosts && hosts.length > 0 ? hosts : [
    {
      id: 'h-1',
      ip: '192.168.1.15',
      hostname: 'api.internal.helios.corp',
      os: 'Linux (Ubuntu 22.04 LTS / Kernel 5.15)',
      status: 'up',
      services: [
        { id: 's-1', port: 22, protocol: 'tcp', service_name: 'ssh', name: 'ssh', version: 'OpenSSH 8.9p1' },
        { id: 's-2', port: 80, protocol: 'tcp', service_name: 'http', name: 'http', version: 'Apache 2.4.49 (Vulnerable)' },
        { id: 's-3', port: 443, protocol: 'tcp', service_name: 'https', name: 'https', version: 'OpenSSL 3.0.2' },
        { id: 's-4', port: 8080, protocol: 'tcp', service_name: 'http-proxy', name: 'http-proxy', version: 'Node.js Express API' }
      ]
    },
    {
      id: 'h-2',
      ip: '192.168.1.10',
      hostname: 'auth.helios.corp',
      os: 'Linux (Debian 12)',
      status: 'up',
      services: [
        { id: 's-5', port: 22, protocol: 'tcp', service_name: 'ssh', name: 'ssh', version: 'OpenSSH 9.2' },
        { id: 's-6', port: 5432, protocol: 'tcp', service_name: 'postgresql', name: 'postgresql', version: 'PostgreSQL 16.1' },
        { id: 's-7', port: 6379, protocol: 'tcp', service_name: 'redis', name: 'redis', version: 'Redis 7.2 (Unauthenticated)' }
      ]
    },
    {
      id: 'h-3',
      ip: '192.168.1.50',
      hostname: 'k8s-master.helios.cloud',
      os: 'Linux (Container Linux)',
      status: 'up',
      services: [
        { id: 's-8', port: 6443, protocol: 'tcp', service_name: 'kube-apiserver', name: 'kube-apiserver', version: 'Kubernetes v1.28' },
        { id: 's-9', port: 2379, protocol: 'tcp', service_name: 'etcd', name: 'etcd', version: 'etcd 3.5.9' }
      ]
    }
  ];

  const mitreTactics = [
    { name: 'Reconnaissance', id: 'TA0043', count: 6, status: 'Completed', color: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' },
    { name: 'Initial Access', id: 'TA0001', count: 3, status: 'Exploited', color: 'text-red-400 border-red-500/30 bg-red-500/10' },
    { name: 'Execution', id: 'TA0002', count: 2, status: 'PoC Ready', color: 'text-amber-400 border-amber-500/30 bg-amber-500/10' },
    { name: 'Persistence', id: 'TA0003', count: 1, status: 'Identified', color: 'text-purple-400 border-purple-500/30 bg-purple-500/10' },
    { name: 'Privilege Escalation', id: 'TA0004', count: 2, status: 'Vulnerable', color: 'text-rose-400 border-rose-500/30 bg-rose-500/10' },
    { name: 'Defense Evasion', id: 'TA0005', count: 4, status: 'Bypassed', color: 'text-orange-400 border-orange-500/30 bg-orange-500/10' },
    { name: 'Credential Access', id: 'TA0006', count: 3, status: 'Extracted', color: 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10' },
    { name: 'Lateral Movement', id: 'TA0008', count: 2, status: 'Path Mapped', color: 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10' },
  ];

  return (
    <div className="flex flex-col h-full bg-surface-primary overflow-y-auto custom-scrollbar p-6 space-y-6 animate-in fade-in duration-300">
      
      {/* Top Banner / Mission Status */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-surface-secondary via-surface-secondary to-surface-tertiary/60 border border-border-default shadow-xl">
        <div className="flex items-start gap-4">
          <div className="p-3.5 rounded-xl bg-border-active/15 border border-border-active/30 text-border-active shadow-inner shrink-0">
            <Zap size={28} />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-100 tracking-tight">HELIOS Mission Control</h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                ENGAGEMENT LIVE
              </span>
            </div>
            <p className="text-sm text-gray-400 mt-1 max-w-2xl">
              Offensive cyber copilot & centralized intelligence platform with real-time attack graph reasoning, automated vulnerability triage, and tamper-proof evidence preservation.
            </p>
          </div>
        </div>

        {/* Engine Telemetry Pillbox */}
        <div className="flex flex-wrap items-center gap-2 self-start lg:self-center">
          <div className="px-3 py-1.5 rounded-lg bg-surface-primary/80 border border-border-default text-xs flex items-center gap-2">
            <Cpu size={14} className="text-border-active" />
            <span className="text-gray-400">OpenVINO:</span>
            <span className="text-gray-200 font-mono font-semibold">Qwen-2.5-Coder (NPU)</span>
          </div>
          <div className="px-3 py-1.5 rounded-lg bg-surface-primary/80 border border-border-default text-xs flex items-center gap-2">
            <Lock size={14} className="text-emerald-400" />
            <span className="text-gray-400">Vault:</span>
            <span className="text-gray-200 font-mono font-semibold">AES-256-GCM Locked</span>
          </div>
        </div>
      </div>

      {/* Primary Key Metrics & Threat Score Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        
        {/* Threat Posture Meter */}
        <div className="p-5 rounded-2xl bg-surface-secondary border border-border-default shadow-sm relative overflow-hidden flex flex-col justify-between">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Attack Surface Risk</span>
              <div className="flex items-baseline gap-2 mt-1">
                <span className="text-3xl font-black text-severity-critical">84</span>
                <span className="text-xs text-gray-500 font-mono">/ 100 HIGH</span>
              </div>
            </div>
            <div className="p-2.5 rounded-xl bg-severity-critical/15 text-severity-critical border border-severity-critical/30">
              <Flame size={20} />
            </div>
          </div>

          <div className="mt-4 space-y-1.5">
            <div className="w-full bg-surface-primary rounded-full h-2 overflow-hidden flex">
              <div className="bg-severity-critical h-full" style={{ width: '60%' }} />
              <div className="bg-severity-high h-full" style={{ width: '25%' }} />
              <div className="bg-severity-medium h-full" style={{ width: '15%' }} />
            </div>
            <div className="flex justify-between text-[10px] text-gray-400 font-mono">
              <span>{criticalFindings} Critical Exploitable</span>
              <span>{highFindings} High Risk</span>
            </div>
          </div>
        </div>

        {/* Active Recon Targets */}
        <Link 
          to="/recon"
          className="p-5 rounded-2xl bg-surface-secondary border border-border-default hover:border-border-active/60 transition-all shadow-sm group flex flex-col justify-between"
        >
          <div className="flex items-start justify-between">
            <div>
              <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Live Targets</span>
              <div className="text-3xl font-black text-gray-100 mt-1">{displayHosts.length} Hosts</div>
            </div>
            <div className="p-2.5 rounded-xl bg-blue-500/15 text-blue-400 border border-blue-500/30 group-hover:scale-105 transition-transform">
              <Target size={20} />
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
            <span className="font-mono text-gray-300">{openPorts} open service ports</span>
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
              <div className="text-3xl font-black text-amber-400 mt-1">{findings?.length || 6} Findings</div>
            </div>
            <div className="p-2.5 rounded-xl bg-amber-500/15 text-amber-400 border border-amber-500/30 group-hover:scale-105 transition-transform">
              <Globe size={20} />
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
            <span className="font-mono text-gray-300">HTTP Repeater & DAST Ready</span>
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
              <div className="text-3xl font-black text-emerald-400 mt-1">{evidenceList?.length || 4} Vault Items</div>
            </div>
            <div className="p-2.5 rounded-xl bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 group-hover:scale-105 transition-transform">
              <ShieldCheck size={20} />
            </div>
          </div>
          <div className="mt-4 flex items-center justify-between text-xs text-gray-400">
            <span className="font-mono text-emerald-400">100% SHA-256 Verified</span>
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
          <span className="text-[11px] text-gray-500 font-mono">1-Click Offensive Automation</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
          <button
            onClick={() => navigate('/recon')}
            className="flex flex-col items-center justify-center p-3 rounded-xl bg-surface-tertiary/70 hover:bg-surface-tertiary border border-border-default hover:border-border-active/60 transition-all text-center group"
          >
            <Target size={20} className="text-blue-400 mb-1.5 group-hover:scale-110 transition-transform" />
            <span className="text-xs font-semibold text-gray-200">SYN Recon</span>
            <span className="text-[10px] text-gray-500 font-mono">Nmap Ingestion</span>
          </button>

          <button
            onClick={() => navigate('/web')}
            className="flex flex-col items-center justify-center p-3 rounded-xl bg-surface-tertiary/70 hover:bg-surface-tertiary border border-border-default hover:border-border-active/60 transition-all text-center group"
          >
            <Globe size={20} className="text-amber-400 mb-1.5 group-hover:scale-110 transition-transform" />
            <span className="text-xs font-semibold text-gray-200">HTTP Repeater</span>
            <span className="text-[10px] text-gray-500 font-mono">Proxy & Fuzz</span>
          </button>

          <button
            onClick={() => navigate('/code')}
            className="flex flex-col items-center justify-center p-3 rounded-xl bg-surface-tertiary/70 hover:bg-surface-tertiary border border-border-default hover:border-border-active/60 transition-all text-center group"
          >
            <Code2 size={20} className="text-purple-400 mb-1.5 group-hover:scale-110 transition-transform" />
            <span className="text-xs font-semibold text-gray-200">AST Code Audit</span>
            <span className="text-[10px] text-gray-500 font-mono">Secret Detector</span>
          </button>

          <button
            onClick={() => navigate('/malware')}
            className="flex flex-col items-center justify-center p-3 rounded-xl bg-surface-tertiary/70 hover:bg-surface-tertiary border border-border-default hover:border-border-active/60 transition-all text-center group"
          >
            <Bug size={20} className="text-rose-400 mb-1.5 group-hover:scale-110 transition-transform" />
            <span className="text-xs font-semibold text-gray-200">Malware Triage</span>
            <span className="text-[10px] text-gray-500 font-mono">YARA & Entropy</span>
          </button>

          <button
            onClick={() => navigate('/graph')}
            className="flex flex-col items-center justify-center p-3 rounded-xl bg-surface-tertiary/70 hover:bg-surface-tertiary border border-border-default hover:border-border-active/60 transition-all text-center group"
          >
            <Network size={20} className="text-emerald-400 mb-1.5 group-hover:scale-110 transition-transform" />
            <span className="text-xs font-semibold text-gray-200">Attack Graph</span>
            <span className="text-[10px] text-gray-500 font-mono">Path Finding</span>
          </button>

          <button
            onClick={() => navigate('/reports')}
            className="flex flex-col items-center justify-center p-3 rounded-xl bg-surface-tertiary/70 hover:bg-surface-tertiary border border-border-default hover:border-border-active/60 transition-all text-center group"
          >
            <FileBox size={20} className="text-cyan-400 mb-1.5 group-hover:scale-110 transition-transform" />
            <span className="text-xs font-semibold text-gray-200">Report Studio</span>
            <span className="text-[10px] text-gray-500 font-mono">Export PDF/MD</span>
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
              {displayHosts.map(host => (
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
                      <div className="text-xs text-gray-400 mt-0.5">{host.os}</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap">
                    {host.services.map((svc: any, sIdx: number) => (
                      <span 
                        key={svc.id || sIdx}
                        className={`text-[11px] font-mono px-2 py-0.5 rounded border ${
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
                      Audit
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* MITRE ATT&CK Matrix Grid */}
          <div className="p-5 rounded-2xl bg-surface-secondary border border-border-default shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <ShieldAlert size={18} className="text-border-active" />
                <h2 className="text-base font-bold text-gray-100">MITRE ATT&CK Enterprise Matrix Coverage</h2>
              </div>
              <span className="text-xs text-gray-500 font-mono">v14.1 Alignment</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {mitreTactics.map(tactic => (
                <div 
                  key={tactic.id}
                  className={`p-3 rounded-xl border text-xs flex flex-col justify-between ${tactic.color}`}
                >
                  <div>
                    <span className="font-mono text-[10px] opacity-75">{tactic.id}</span>
                    <h4 className="font-bold text-gray-100 text-xs mt-0.5 leading-tight">{tactic.name}</h4>
                  </div>
                  <div className="flex items-center justify-between mt-3 pt-2 border-t border-white/10 font-mono text-[10px]">
                    <span>{tactic.count} Techniques</span>
                    <span className="font-bold">{tactic.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Right 1 Col: Live Security Event Timeline & Copilot Widget */}
        <div className="space-y-6">
          
          {/* AI Security Copilot Quick Prompter */}
          <div className="p-5 rounded-2xl bg-gradient-to-b from-surface-secondary to-surface-tertiary/80 border border-border-default shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Zap size={18} className="text-border-active animate-pulse" />
                <h3 className="font-bold text-gray-100 text-sm">HELIOS Copilot AI</h3>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">
                Local offline LLM with full context of your target scope, open ports, and decompiled source code.
              </p>
            </div>

            <div className="mt-4 space-y-2">
              <button
                onClick={() => navigate('/chat', { state: { initialPrompt: 'Analyze CVE-2021-41773 on host 192.168.1.15 and suggest non-destructive PoC verification steps.' } })}
                className="w-full text-left p-2.5 rounded-lg bg-surface-primary/80 hover:bg-border-active/15 border border-border-default hover:border-border-active/40 text-xs text-gray-300 hover:text-gray-100 transition-all font-mono"
              >
                &ldquo;Explain Apache 2.4.49 path traversal PoC&rdquo;
              </button>
              <button
                onClick={() => navigate('/chat', { state: { initialPrompt: 'Generate a lateral movement plan from host 192.168.1.15 to database host 192.168.1.10.' } })}
                className="w-full text-left p-2.5 rounded-lg bg-surface-primary/80 hover:bg-border-active/15 border border-border-default hover:border-border-active/40 text-xs text-gray-300 hover:text-gray-100 transition-all font-mono"
              >
                &ldquo;Draft lateral movement attack path&rdquo;
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
                <h3 className="text-sm font-bold text-gray-100">Live SIEM Feed</h3>
              </div>
              <Link to="/logs" className="text-xs text-border-active hover:underline">Full Feed</Link>
            </div>

            <div className="space-y-2.5 max-h-[320px] overflow-y-auto custom-scrollbar pr-1">
              {(events && events.length > 0 ? events : DEFAULT_SIEM_EVENTS).map(evt => (
                <div 
                  key={evt.id}
                  className="p-2.5 rounded-lg bg-surface-tertiary/70 border border-border-default text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold uppercase border ${
                      evt.severity.toLowerCase() === 'critical' ? 'bg-severity-critical/20 text-severity-critical border-severity-critical/40' :
                      evt.severity.toLowerCase() === 'high' ? 'bg-severity-high/20 text-severity-high border-severity-high/40' :
                      'bg-severity-info/20 text-severity-info border-severity-info/40'
                    }`}>
                      {evt.severity}
                    </span>
                    <span className="text-[10px] text-gray-500 font-mono">{evt.source}</span>
                  </div>
                  <p className="text-gray-300 line-clamp-2">{evt.message}</p>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}

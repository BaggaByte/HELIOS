import { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Search,
  Activity,
  Globe,
  ChevronRight,
  AlertTriangle,
  Bug,
  Send,
  Terminal,
  Key,
  Copy,
  Check,
  Shield,
  Sparkles,
  RefreshCw
} from 'lucide-react';
import { useWebSecurityStore } from '../../stores/webSecurityStore';
import { cn } from '../../lib/utils';
import { useNavigate } from 'react-router-dom';

export function WebSecurityDashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'vulnerabilities' | 'repeater' | 'jwt'>('vulnerabilities');
  const [scanTarget, setScanTarget] = useState('');
  const { findings, selectedFindingId, isLoading, isScanning, fetchFindings, triggerScan, selectFinding } = useWebSecurityStore();

  // HTTP Repeater state
  const [repeaterMethod, setRepeaterMethod] = useState<'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'>('GET');
  const [repeaterUrl, setRepeaterUrl] = useState('https://api.internal.helios.corp/cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd');
  const [repeaterHeaders, setRepeaterHeaders] = useState(
    'Host: api.internal.helios.corp\nUser-Agent: Mozilla/5.0 (HELIOS Security Scanner v1.4)\nAccept: */*\nContent-Type: application/json'
  );
  const [repeaterBody, setRepeaterBody] = useState('{\n  "action": "verify_token",\n  "debug": true\n}');
  const [isSendingRequest, setIsSendingRequest] = useState(false);
  const [responseViewMode, setResponseViewMode] = useState<'preview' | 'raw' | 'hex'>('preview');
  const [repeaterResponse, setRepeaterResponse] = useState<{
    status: number;
    statusText: string;
    timeMs: number;
    sizeBytes: number;
    headers: Record<string, string>;
    body: string;
  } | null>({
    status: 200,
    statusText: 'OK',
    timeMs: 42,
    sizeBytes: 1340,
    headers: {
      'content-type': 'text/plain; charset=utf-8',
      'server': 'Apache/2.4.49 (Unix)',
      'x-frame-options': 'DENY',
      'connection': 'close'
    },
    body: 'root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\nbin:x:2:2:bin:/bin:/usr/sbin/nologin\nsys:x:3:3:sys:/dev:/usr/sbin/nologin\nwww-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\nbackup:x:34:34:backup:/var/backups:/usr/sbin/nologin\nhelios_app:x:1000:1000:HELIOS Service Account:/home/helios_app:/bin/bash'
  });

  // JWT Lab state
  const [jwtInput, setJwtInput] = useState(
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDAwIiwibmFtZSI6IkFkbWluIFVzZXIiLCJyb2xlIjoiYWRtaW4iLCJpc3MiOiJoZWxpb3MtYXV0aCIsImV4cCI6MTgwMDAwMDAwMH0.3e4334a1795c6bd17ddcaef12204c326d9c661fffaebff36d4df927b5e43c52e'
  );
  const [jwtSecret, setJwtSecret] = useState('secret123');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchFindings('default-project-id');
  }, [fetchFindings]);

  const handleScanSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (scanTarget.trim() && !isScanning) {
      triggerScan(scanTarget.trim());
      setScanTarget('');
    }
  };

  const executeRepeaterRequest = () => {
    setIsSendingRequest(true);
    setTimeout(() => {
      setIsSendingRequest(false);
      // Realistic simulated response based on request
      if (repeaterUrl.includes('passwd')) {
        setRepeaterResponse({
          status: 200,
          statusText: 'OK',
          timeMs: Math.floor(Math.random() * 35) + 25,
          sizeBytes: 1340,
          headers: {
            'content-type': 'text/plain; charset=utf-8',
            'server': 'Apache/2.4.49 (Unix)',
            'x-powered-by': 'CGI/1.1',
            'connection': 'close'
          },
          body: 'root:x:0:0:root:/root:/bin/bash\nhelios_app:x:1000:1000:HELIOS Service Account:/home/helios_app:/bin/bash\npostgres:x:105:111:PostgreSQL server:/var/lib/postgresql:/bin/bash\nnginx:x:106:112:nginx user:/var/log/nginx:/bin/false'
        });
      } else if (repeaterMethod === 'POST') {
        setRepeaterResponse({
          status: 201,
          statusText: 'Created',
          timeMs: Math.floor(Math.random() * 45) + 30,
          sizeBytes: 420,
          headers: {
            'content-type': 'application/json',
            'server': 'nginx/1.24.0',
            'set-cookie': 'helios_session=s%3A98a2f1b.87bc9; Path=/; HttpOnly; SameSite=Lax'
          },
          body: JSON.stringify({
            status: 'success',
            authenticated: true,
            user_id: 'usr_981a',
            role: 'superadmin',
            issued_at: new Date().toISOString()
          }, null, 2)
        });
      } else {
        setRepeaterResponse({
          status: 200,
          statusText: 'OK',
          timeMs: 38,
          sizeBytes: 812,
          headers: {
            'content-type': 'application/json',
            'server': 'Node.js Express'
          },
          body: JSON.stringify({
            api_version: 'v1.4.0',
            status: 'healthy',
            database_cluster: 'connected',
            cache_nodes: 3
          }, null, 2)
        });
      }
    }, 450);
  };

  // JWT Decode calculation
  const parsedJwt = (() => {
    try {
      const parts = jwtInput.trim().split('.');
      if (parts.length !== 3) return null;
      const header = JSON.parse(atob(parts[0]));
      const payload = JSON.parse(atob(parts[1]));
      return { header, payload, signature: parts[2], valid: true };
    } catch {
      return null;
    }
  })();

  const generateAlgNoneJwt = () => {
    if (!parsedJwt) return;
    const header = btoa(JSON.stringify({ alg: 'none', typ: 'JWT' })).replace(/=/g, '');
    const payload = btoa(JSON.stringify(parsedJwt.payload)).replace(/=/g, '');
    setJwtInput(`${header}.${payload}.`);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getSeverityStyle = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL': return 'text-severity-critical bg-severity-critical/10 border-severity-critical/30';
      case 'HIGH': return 'text-orange-400 bg-orange-400/10 border-orange-400/30';
      case 'MEDIUM': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30';
      case 'LOW': return 'text-severity-low bg-severity-low/10 border-severity-low/30';
      default: return 'text-severity-info bg-severity-info/10 border-severity-info/30';
    }
  };

  const selectedFinding = findings.find(f => f.id === selectedFindingId) || findings[0];

  return (
    <div className="flex flex-col h-full bg-surface-primary overflow-hidden">
      
      {/* Top Header & Mode Tabs */}
      <div className="p-4 border-b border-border-default bg-surface-secondary flex flex-col sm:flex-row sm:items-center justify-between gap-4 flex-shrink-0">
        <div>
          <h1 className="text-xl font-bold text-gray-100 flex items-center gap-2.5">
            <Globe className="text-border-active" size={22} />
            Web Security & DAST Hub
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">Dynamic web app security audit, HTTP request repeater, and JWT analysis workbench.</p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center rounded-xl bg-surface-tertiary p-1 border border-border-default text-xs font-semibold self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('vulnerabilities')}
            className={cn(
              "px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5",
              activeTab === 'vulnerabilities' ? "bg-border-active text-white shadow-xs" : "text-gray-400 hover:text-gray-200"
            )}
          >
            <ShieldAlert size={14} />
            <span>Vulnerability Triage</span>
          </button>
          <button
            onClick={() => setActiveTab('repeater')}
            className={cn(
              "px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5",
              activeTab === 'repeater' ? "bg-border-active text-white shadow-xs" : "text-gray-400 hover:text-gray-200"
            )}
          >
            <Terminal size={14} />
            <span>HTTP Repeater</span>
          </button>
          <button
            onClick={() => setActiveTab('jwt')}
            className={cn(
              "px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5",
              activeTab === 'jwt' ? "bg-border-active text-white shadow-xs" : "text-gray-400 hover:text-gray-200"
            )}
          >
            <Key size={14} />
            <span>JWT Lab</span>
          </button>
        </div>
      </div>

      {/* Tab Content 1: Vulnerabilities */}
      {activeTab === 'vulnerabilities' && (
        <div className="flex-1 flex flex-col overflow-hidden">
          
          {/* Target Scan Control Bar */}
          <div className="p-4 border-b border-border-default bg-surface-secondary/40 flex flex-col md:flex-row gap-3 items-center justify-between flex-shrink-0">
            <form onSubmit={handleScanSubmit} className="flex-1 w-full max-w-2xl relative">
              <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              <input
                type="url"
                value={scanTarget}
                onChange={(e) => setScanTarget(e.target.value)}
                placeholder="Enter URL to audit (e.g., https://api.internal.helios.corp)..."
                className="w-full bg-surface-tertiary border border-border-default rounded-xl py-2 pl-10 pr-32 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-border-active"
                disabled={isScanning}
              />
              <button
                type="submit"
                disabled={!scanTarget.trim() || isScanning}
                className="absolute right-1.5 top-1.5 bottom-1.5 px-3 rounded-lg bg-border-active text-white font-semibold text-xs flex items-center gap-1.5 hover:bg-opacity-90 disabled:opacity-50 transition-all"
              >
                {isScanning ? <Activity size={14} className="animate-spin" /> : <Bug size={14} />}
                <span>{isScanning ? 'Auditing...' : 'Run DAST Scan'}</span>
              </button>
            </form>

            <div className="flex items-center gap-2 text-xs text-gray-400 font-mono self-end md:self-auto">
              <span>ACTIVE FINDINGS:</span>
              <span className="px-2 py-0.5 rounded bg-severity-critical/20 text-severity-critical font-bold">{findings.length || 3}</span>
            </div>
          </div>

          {/* Master-Detail Layout */}
          <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
            
            {/* Left Pane: Finding List */}
            <div className="w-full lg:w-96 border-b lg:border-b-0 lg:border-r border-border-default bg-surface-secondary/20 overflow-y-auto p-3 space-y-2 custom-scrollbar flex-shrink-0">
              {isLoading ? (
                <div className="flex items-center justify-center py-16 text-border-active">
                  <Activity size={28} className="animate-spin" />
                </div>
              ) : findings.length === 0 ? (
                <div className="text-center text-gray-500 py-12 p-4">
                  <ShieldAlert size={36} className="mx-auto mb-2 opacity-40" />
                  <p className="text-xs">No web vulnerabilities detected yet.</p>
                </div>
              ) : (
                findings.map((finding) => (
                  <div
                    key={finding.id}
                    onClick={() => selectFinding(finding.id)}
                    className={cn(
                      "p-3.5 rounded-xl border transition-all cursor-pointer text-xs",
                      (selectedFindingId === finding.id || (!selectedFindingId && selectedFinding?.id === finding.id))
                        ? "bg-surface-tertiary border-border-active shadow-md"
                        : "bg-surface-secondary/70 border-border-default hover:border-gray-500"
                    )}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded uppercase border", getSeverityStyle(finding.severity))}>
                        {finding.severity}
                      </span>
                      <span className="font-mono text-gray-400 text-[11px] font-semibold">{finding.method}</span>
                    </div>
                    <h3 className="font-bold text-gray-100 truncate mb-1">{finding.vulnerability_type}</h3>
                    <p className="text-gray-400 font-mono text-[11px] truncate">{finding.url}</p>
                  </div>
                ))
              )}
            </div>

            {/* Right Pane: Finding Details */}
            <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-surface-primary">
              {selectedFinding ? (
                <div className="max-w-4xl space-y-6">
                  
                  {/* Title & Actions */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-border-default">
                    <div className="flex items-start gap-3">
                      <div className={cn("p-3 rounded-xl border shrink-0", getSeverityStyle(selectedFinding.severity))}>
                        <AlertTriangle size={24} />
                      </div>
                      <div>
                        <h2 className="text-xl font-bold text-gray-100">{selectedFinding.vulnerability_type}</h2>
                        <div className="flex items-center gap-3 mt-1 text-xs text-gray-400 flex-wrap">
                          <span className={cn("font-bold", getSeverityStyle(selectedFinding.severity).split(' ')[0])}>
                            {selectedFinding.severity} SEVERITY
                          </span>
                          <span>•</span>
                          <span className="font-mono">CWE-22 / OWASP A01:2021</span>
                          <span>•</span>
                          <span>Discovered {new Date(selectedFinding.discovered_at).toLocaleString()}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-start sm:self-center">
                      <button
                        onClick={() => {
                          setRepeaterUrl(selectedFinding.url);
                          setRepeaterMethod((selectedFinding.method as any) || 'GET');
                          if (selectedFinding.request_headers) setRepeaterHeaders(selectedFinding.request_headers);
                          if (selectedFinding.request_body) setRepeaterBody(selectedFinding.request_body);
                          setActiveTab('repeater');
                        }}
                        className="px-3 py-1.5 rounded-lg bg-surface-tertiary hover:bg-surface-hover border border-border-default text-xs font-semibold text-gray-200 transition-colors flex items-center gap-1.5"
                      >
                        <Terminal size={14} className="text-border-active" />
                        <span>Send to Repeater</span>
                      </button>
                      <button
                        onClick={() => navigate('/chat', { state: { initialPrompt: `Analyze vulnerability ${selectedFinding.vulnerability_type} on ${selectedFinding.url} and generate an automated fix & exploit PoC.` } })}
                        className="px-3 py-1.5 rounded-lg bg-border-active text-white text-xs font-semibold hover:bg-opacity-90 transition-all flex items-center gap-1.5 shadow-sm"
                      >
                        <Sparkles size={14} />
                        <span>AI Fix & PoC</span>
                      </button>
                    </div>
                  </div>

                  {/* Endpoint & Description */}
                  <div className="space-y-4 text-xs">
                    <div>
                      <h4 className="font-bold text-gray-400 uppercase tracking-wider mb-1.5">Target Endpoint</h4>
                      <div className="p-2.5 rounded-xl bg-surface-secondary border border-border-default font-mono text-gray-200 flex items-center gap-2">
                        <span className="text-border-active font-bold">{selectedFinding.method}</span>
                        <span className="break-all">{selectedFinding.url}</span>
                      </div>
                    </div>

                    <div>
                      <h4 className="font-bold text-gray-400 uppercase tracking-wider mb-1.5">Vulnerability Description</h4>
                      <p className="p-3.5 rounded-xl bg-surface-secondary border border-border-default text-gray-300 leading-relaxed text-sm">
                        {selectedFinding.description}
                      </p>
                    </div>
                  </div>

                  {/* HTTP Proof of Concept Request / Response */}
                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                        <ChevronRight size={14} className="text-severity-info" />
                        <span>PoC Request</span>
                      </h4>
                      <div className="bg-[#0b0e14] rounded-xl border border-border-default p-3 font-mono text-[11px] text-gray-300 overflow-x-auto max-h-64">
                        <pre className="whitespace-pre-wrap">{selectedFinding.request_headers || `${selectedFinding.method} ${selectedFinding.url} HTTP/1.1\nHost: api.internal.helios.corp\nUser-Agent: HELIOS-DAST/1.4`}</pre>
                        {selectedFinding.request_body && (
                          <pre className="mt-2 pt-2 border-t border-border-default/50 text-border-active whitespace-pre-wrap">{selectedFinding.request_body}</pre>
                        )}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                        <ChevronRight size={14} className="text-severity-critical" />
                        <span>PoC Response Trace</span>
                      </h4>
                      <div className="bg-[#0b0e14] rounded-xl border border-border-default p-3 font-mono text-[11px] text-emerald-400 overflow-x-auto max-h-64">
                        <pre className="whitespace-pre-wrap text-gray-400">{selectedFinding.response_headers || 'HTTP/1.1 200 OK\nServer: Apache/2.4.49 (Unix)\nContent-Type: text/plain'}</pre>
                        <pre className="mt-2 pt-2 border-t border-border-default/50 text-emerald-400 whitespace-pre-wrap">{selectedFinding.response_body || 'root:x:0:0:root:/root:/bin/bash\nhelios_app:x:1000:1000:HELIOS Service:/home/helios_app:/bin/bash'}</pre>
                      </div>
                    </div>
                  </div>

                  {/* Remediation Guidance */}
                  <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 space-y-2 text-xs">
                    <div className="flex items-center gap-2 text-emerald-400 font-bold">
                      <Shield size={16} />
                      <span>Recommended Remediation</span>
                    </div>
                    <p className="text-gray-300 leading-relaxed">
                      Upgrade Apache HTTP Server to version 2.4.51 or later immediately. Ensure directory traversal protection directives (<code className="font-mono text-emerald-300">Require all denied</code>) are enforced globally across the server configuration.
                    </p>
                  </div>

                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <Globe size={48} className="opacity-30 mb-2" />
                  <p className="text-sm">Select a finding to inspect HTTP payloads and remediation guidelines.</p>
                </div>
              )}
            </div>

          </div>
        </div>
      )}

      {/* Tab Content 2: HTTP Repeater */}
      {activeTab === 'repeater' && (
        <div className="flex-1 flex flex-col overflow-hidden p-4 gap-4 bg-surface-primary">
          
          {/* Request URL & Method Bar */}
          <div className="flex items-center gap-2 p-2 rounded-xl bg-surface-secondary border border-border-default">
            <select
              value={repeaterMethod}
              onChange={(e) => setRepeaterMethod(e.target.value as any)}
              className="bg-surface-tertiary text-gray-100 font-mono font-bold text-xs px-3 py-2 rounded-lg border border-border-default focus:border-border-active outline-none"
            >
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="DELETE">DELETE</option>
              <option value="PATCH">PATCH</option>
            </select>

            <input
              type="text"
              value={repeaterUrl}
              onChange={(e) => setRepeaterUrl(e.target.value)}
              placeholder="https://target.com/endpoint..."
              className="flex-1 bg-surface-tertiary border border-border-default rounded-lg px-3 py-2 text-xs font-mono text-gray-200 placeholder-gray-500 focus:outline-none focus:border-border-active"
            />

            <button
              onClick={executeRepeaterRequest}
              disabled={isSendingRequest}
              className="px-4 py-2 rounded-lg bg-border-active text-white text-xs font-bold hover:bg-opacity-90 disabled:opacity-50 transition-all flex items-center gap-1.5 shadow-sm shrink-0"
            >
              {isSendingRequest ? <RefreshCw size={14} className="animate-spin" /> : <Send size={14} />}
              <span>{isSendingRequest ? 'Sending...' : 'Send Request'}</span>
            </button>
          </div>

          {/* Dual Workbench: Request vs Response */}
          <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 overflow-hidden">
            
            {/* Request Pane */}
            <div className="flex flex-col bg-surface-secondary rounded-xl border border-border-default overflow-hidden">
              <div className="p-3 border-b border-border-default flex items-center justify-between bg-surface-tertiary/40">
                <span className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-2">
                  <Terminal size={14} className="text-border-active" />
                  Request Inspector
                </span>
                
                {/* Payload Quick Injectors */}
                <div className="flex items-center gap-1 text-[11px]">
                  <span className="text-gray-500 mr-1">Inject:</span>
                  <button
                    onClick={() => setRepeaterUrl('https://api.internal.helios.corp/cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd')}
                    className="px-1.5 py-0.5 rounded bg-surface-primary hover:bg-surface-hover text-gray-300 border border-border-default font-mono"
                  >
                    Path Traversal
                  </button>
                  <button
                    onClick={() => setRepeaterUrl("https://api.internal.helios.corp/api/v1/users?id=1' OR '1'='1")}
                    className="px-1.5 py-0.5 rounded bg-surface-primary hover:bg-surface-hover text-gray-300 border border-border-default font-mono"
                  >
                    SQLi
                  </button>
                </div>
              </div>

              <div className="flex-1 flex flex-col p-3 space-y-3 overflow-y-auto custom-scrollbar">
                <div className="space-y-1">
                  <label className="text-[11px] font-bold text-gray-400 uppercase">Headers</label>
                  <textarea
                    value={repeaterHeaders}
                    onChange={(e) => setRepeaterHeaders(e.target.value)}
                    rows={4}
                    className="w-full bg-[#0b0e14] border border-border-default rounded-lg p-2.5 text-xs font-mono text-gray-200 focus:outline-none focus:border-border-active resize-none"
                  />
                </div>

                <div className="flex-1 flex flex-col space-y-1">
                  <label className="text-[11px] font-bold text-gray-400 uppercase">Body (JSON / Raw)</label>
                  <textarea
                    value={repeaterBody}
                    onChange={(e) => setRepeaterBody(e.target.value)}
                    className="flex-1 w-full bg-[#0b0e14] border border-border-default rounded-lg p-2.5 text-xs font-mono text-border-active focus:outline-none focus:border-border-active resize-none min-h-[140px]"
                  />
                </div>
              </div>
            </div>

            {/* Response Pane */}
            <div className="flex flex-col bg-surface-secondary rounded-xl border border-border-default overflow-hidden">
              <div className="p-3 border-b border-border-default flex items-center justify-between bg-surface-tertiary/40">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-bold text-gray-300 uppercase tracking-wider">Response</span>
                  {repeaterResponse && (
                    <div className="flex items-center gap-2 font-mono text-xs">
                      <span className={cn(
                        "px-2 py-0.5 rounded font-bold",
                        repeaterResponse.status >= 200 && repeaterResponse.status < 300 ? "bg-emerald-500/20 text-emerald-400" :
                        repeaterResponse.status >= 400 ? "bg-severity-critical/20 text-severity-critical" : "bg-blue-500/20 text-blue-400"
                      )}>
                        {repeaterResponse.status} {repeaterResponse.statusText}
                      </span>
                      <span className="text-gray-500">{repeaterResponse.timeMs}ms</span>
                      <span className="text-gray-500">{repeaterResponse.sizeBytes} B</span>
                    </div>
                  )}
                </div>

                {/* View format switcher */}
                <div className="flex items-center rounded-lg bg-surface-primary p-0.5 border border-border-default text-[10px] font-bold">
                  <button
                    onClick={() => setResponseViewMode('preview')}
                    className={cn("px-2 py-0.5 rounded transition-colors", responseViewMode === 'preview' ? "bg-border-active text-white" : "text-gray-400")}
                  >
                    Formatted
                  </button>
                  <button
                    onClick={() => setResponseViewMode('raw')}
                    className={cn("px-2 py-0.5 rounded transition-colors", responseViewMode === 'raw' ? "bg-border-active text-white" : "text-gray-400")}
                  >
                    Raw
                  </button>
                  <button
                    onClick={() => setResponseViewMode('hex')}
                    className={cn("px-2 py-0.5 rounded transition-colors", responseViewMode === 'hex' ? "bg-border-active text-white" : "text-gray-400")}
                  >
                    Hex Dump
                  </button>
                </div>
              </div>

              <div className="flex-1 p-3 overflow-y-auto custom-scrollbar bg-[#0b0e14]">
                {repeaterResponse ? (
                  responseViewMode === 'hex' ? (
                    <div className="font-mono text-[11px] text-gray-400 space-y-1">
                      <div>00000000: 726f 6f74 3a78 3a30 3a30 3a72 6f6f 743a  root:x:0:0:root:</div>
                      <div>00000010: 2f72 6f6f 743a 2f62 696e 2f62 6173 680a  /root:/bin/bash.</div>
                      <div>00000020: 6865 6c69 6f73 5f61 7070 3a78 3a31 3030  helios_app:x:100</div>
                      <div>00000030: 303a 3130 3030 3a48 454c 494f 5320 5365  0:1000:HELIOS Se</div>
                    </div>
                  ) : (
                    <div className="space-y-3 font-mono text-xs">
                      <div className="text-gray-400 pb-2 border-b border-border-default/40">
                        {Object.entries(repeaterResponse.headers).map(([k, v]) => (
                          <div key={k}><span className="text-gray-500">{k}:</span> {v}</div>
                        ))}
                      </div>
                      <pre className="text-emerald-400 whitespace-pre-wrap break-all leading-relaxed">
                        {repeaterResponse.body}
                      </pre>
                    </div>
                  )
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-500 text-xs">
                    Send a request to inspect response stream.
                  </div>
                )}
              </div>
            </div>

          </div>

        </div>
      )}

      {/* Tab Content 3: JWT Lab */}
      {activeTab === 'jwt' && (
        <div className="flex-1 flex flex-col lg:flex-row overflow-hidden p-4 gap-4 bg-surface-primary">
          
          {/* Left: Raw JWT Input */}
          <div className="w-full lg:w-1/2 flex flex-col bg-surface-secondary rounded-xl border border-border-default p-4 gap-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-2">
                <Key size={14} className="text-border-active" />
                Raw Encoded JSON Web Token
              </span>
              <button
                onClick={generateAlgNoneJwt}
                className="text-[11px] px-2 py-1 rounded bg-severity-critical/20 text-severity-critical border border-severity-critical/40 hover:bg-severity-critical hover:text-white font-bold transition-all"
              >
                Simulate &ldquo;alg: none&rdquo; Exploit
              </button>
            </div>

            <textarea
              value={jwtInput}
              onChange={(e) => setJwtInput(e.target.value)}
              placeholder="Paste JWT string (header.payload.signature)..."
              className="flex-1 w-full bg-[#0b0e14] border border-border-default rounded-xl p-3 text-xs font-mono text-amber-300 focus:outline-none focus:border-border-active resize-none leading-relaxed"
            />

            <div className="flex items-center gap-2 pt-2 border-t border-border-default">
              <span className="text-xs text-gray-400 font-mono">HMAC Secret:</span>
              <input
                type="text"
                value={jwtSecret}
                onChange={(e) => setJwtSecret(e.target.value)}
                className="bg-surface-tertiary border border-border-default rounded-lg px-2.5 py-1 text-xs font-mono text-gray-200 focus:border-border-active outline-none flex-1"
              />
              <button
                onClick={() => copyToClipboard(jwtInput)}
                className="px-3 py-1 rounded-lg bg-surface-tertiary hover:bg-surface-hover text-xs text-gray-200 border border-border-default flex items-center gap-1 transition-colors"
              >
                {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                <span>{copied ? 'Copied' : 'Copy Token'}</span>
              </button>
            </div>
          </div>

          {/* Right: Decoded Payload & Security Checks */}
          <div className="w-full lg:w-1/2 flex flex-col bg-surface-secondary rounded-xl border border-border-default p-4 gap-4 overflow-y-auto custom-scrollbar">
            <span className="text-xs font-bold text-gray-300 uppercase tracking-wider">
              Decoded Claims & Security Audit
            </span>

            {parsedJwt ? (
              <div className="space-y-4">
                {/* Header */}
                <div>
                  <span className="text-[11px] font-bold text-red-400 font-mono uppercase">Header: Algorithm & Token Type</span>
                  <pre className="bg-[#0b0e14] border border-red-500/30 rounded-xl p-3 text-xs font-mono text-red-300 mt-1">
                    {JSON.stringify(parsedJwt.header, null, 2)}
                  </pre>
                </div>

                {/* Payload */}
                <div>
                  <span className="text-[11px] font-bold text-purple-400 font-mono uppercase">Payload: Claims Data</span>
                  <pre className="bg-[#0b0e14] border border-purple-500/30 rounded-xl p-3 text-xs font-mono text-purple-300 mt-1">
                    {JSON.stringify(parsedJwt.payload, null, 2)}
                  </pre>
                </div>

                {/* Security Audit Badges */}
                <div className="p-3.5 rounded-xl bg-surface-tertiary border border-border-default space-y-2 text-xs">
                  <div className="font-bold text-gray-200 flex items-center gap-1.5">
                    <ShieldAlert size={14} className="text-amber-400" />
                    <span>Automated JWT Security Findings</span>
                  </div>
                  
                  <div className="space-y-1.5 pt-1 text-[11px]">
                    <div className="flex items-center justify-between text-gray-300">
                      <span>Algorithm:</span>
                      <span className={`font-mono font-bold ${parsedJwt.header.alg === 'none' ? 'text-severity-critical' : 'text-emerald-400'}`}>
                        {parsedJwt.header.alg} {parsedJwt.header.alg === 'none' ? '(INSECURE - SIGNATURE BYPASS)' : '(Standard)'}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-gray-300">
                      <span>Claim &lsquo;role&rsquo;:</span>
                      <span className="font-mono text-amber-300 font-bold">{parsedJwt.payload.role || 'Not present'}</span>
                    </div>

                    <div className="flex items-center justify-between text-gray-300">
                      <span>Expiration Status:</span>
                      <span className="font-mono text-emerald-400">Valid (Future exp)</span>
                    </div>
                  </div>
                </div>

              </div>
            ) : (
              <div className="flex items-center justify-center h-48 text-gray-500 text-xs">
                Invalid JWT format. Provide a valid 3-part base64 token.
              </div>
            )}
          </div>

        </div>
      )}

    </div>
  );
}

import { useState, useEffect } from 'react';
import { ShieldAlert, Search, Activity, Globe, ChevronRight, AlertTriangle, Bug } from 'lucide-react';
import { useWebSecurityStore } from '../../stores/webSecurityStore';
import { cn } from '../../lib/utils';


export function WebSecurityDashboard() {
  const [scanTarget, setScanTarget] = useState('');
  const { findings, selectedFindingId, isLoading, isScanning, error, fetchFindings, triggerScan, selectFinding } = useWebSecurityStore();

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

  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'text-severity-critical bg-severity-critical/10 border-severity-critical/30';
      case 'HIGH': return 'text-orange-500 bg-orange-500/10 border-orange-500/30';
      case 'MEDIUM': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30';
      case 'LOW': return 'text-severity-low bg-severity-low/10 border-severity-low/30';
      default: return 'text-severity-info bg-severity-info/10 border-severity-info/30';
    }
  };

  const selectedFinding = findings.find(f => f.id === selectedFindingId);

  return (
    <div className="flex flex-col h-full p-8 overflow-hidden relative bg-transparent">
      
      {/* Dashboard Header */}
      <div className="flex items-center justify-between mb-8 z-10 flex-shrink-0">
        <div>
          <h1 className="text-3xl font-bold text-gray-100 neon-text flex items-center gap-3">
            <Globe className="text-border-active" size={32} />
            Web Security
          </h1>
          <p className="text-gray-400 mt-2">Dynamic application security testing and HTTP analysis.</p>
        </div>
      </div>

      {/* Control Bar (Scan Input) */}
      <div className="glass-panel p-4 rounded-2xl mb-8 z-10 border border-border-default/50 flex flex-col md:flex-row gap-4 items-center justify-between shadow-xl flex-shrink-0">
        <form onSubmit={handleScanSubmit} className="flex-1 w-full max-w-2xl relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search size={18} className="text-border-active" />
          </div>
          <input
            type="url"
            value={scanTarget}
            onChange={(e) => setScanTarget(e.target.value)}
            placeholder="Target URL (e.g. https://api.example.com)..."
            className="w-full bg-surface-primary/50 border border-border-default/50 rounded-xl py-3 pl-12 pr-32 text-gray-200 placeholder-gray-500 focus:outline-none focus:border-border-active focus:ring-1 focus:ring-border-active/50 transition-all shadow-inner"
            disabled={isScanning}
          />
          <button
            type="submit"
            disabled={!scanTarget.trim() || isScanning}
            className="absolute right-2 top-2 bottom-2 px-4 rounded-lg bg-border-active text-bg-primary font-medium flex items-center gap-2 hover:bg-opacity-90 disabled:opacity-50 disabled:bg-surface-tertiary transition-all"
          >
            {isScanning ? (
              <><Activity size={16} className="animate-spin" /> Scanning...</>
            ) : (
              <><Bug size={16} /> Run DAST Scan</>
            )}
          </button>
        </form>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-severity-critical/10 border border-severity-critical text-severity-critical flex-shrink-0">
          Error: {error}
        </div>
      )}

      {/* Master-Detail Layout */}
      <div className="flex flex-1 gap-6 min-h-0 z-10">
        
        {/* Left Pane: Findings List */}
        <div className="w-1/3 flex flex-col gap-4 overflow-y-auto pr-2 custom-scrollbar">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Activity size={32} className="text-border-active animate-spin" />
            </div>
          ) : findings.length === 0 ? (
            <div className="text-center text-gray-500 py-12 glass-panel rounded-xl">
              <ShieldAlert size={48} className="mx-auto mb-4 opacity-50" />
              <p>No vulnerabilities discovered yet.</p>
            </div>
          ) : (
            findings.map((finding) => (
              <div 
                key={finding.id}
                onClick={() => selectFinding(finding.id)}
                className={cn(
                  "p-4 rounded-xl border transition-all cursor-pointer group hover:border-border-active/50 hover:bg-surface-secondary/60 backdrop-blur shadow-sm",
                  selectedFindingId === finding.id 
                    ? "glass-panel-active border-border-active/70 shadow-[0_0_15px_rgb(var(--border-active)/0.15)]" 
                    : "glass-panel border-border-default/50"
                )}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className={cn("text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider border", getSeverityStyle(finding.severity))}>
                    {finding.severity}
                  </div>
                  <span className="text-xs text-gray-500 font-mono">{finding.method}</span>
                </div>
                <h3 className="text-sm font-semibold text-gray-200 line-clamp-1 mb-1 group-hover:text-border-active transition-colors">
                  {finding.vulnerability_type}
                </h3>
                <p className="text-xs text-gray-500 font-mono truncate">{new URL(finding.url).pathname}</p>
              </div>
            ))
          )}
        </div>

        {/* Right Pane: Finding Details */}
        <div className="flex-1 glass-panel rounded-2xl border border-border-default/50 overflow-hidden flex flex-col shadow-xl">
          {selectedFinding ? (
            <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
              
              {/* Detail Header */}
              <div className="flex items-center gap-4 mb-6">
                <div className={cn(
                  "w-12 h-12 rounded-xl flex items-center justify-center border shadow-inner",
                  getSeverityStyle(selectedFinding.severity)
                )}>
                  <AlertTriangle size={24} />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-100">{selectedFinding.vulnerability_type}</h2>
                  <div className="flex items-center gap-3 mt-1 text-sm">
                    <span className={cn("font-bold", getSeverityStyle(selectedFinding.severity).split(' ')[0])}>
                      {selectedFinding.severity}
                    </span>
                    <span className="text-gray-500">•</span>
                    <span className="text-gray-400">Discovered {new Date(selectedFinding.discovered_at).toLocaleString()}</span>
                  </div>
                </div>
              </div>

              {/* Description */}
              <div className="mb-8">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">Description</h3>
                <p className="text-gray-300 leading-relaxed bg-surface-primary/30 p-4 rounded-xl border border-border-default/30">
                  {selectedFinding.description}
                </p>
              </div>

              {/* URL */}
              <div className="mb-8">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">Target Endpoint</h3>
                <div className="flex items-center gap-3 bg-surface-primary/50 p-3 rounded-xl border border-border-default/50 font-mono text-sm">
                  <span className="text-border-active font-bold">{selectedFinding.method}</span>
                  <span className="text-gray-300 break-all">{selectedFinding.url}</span>
                </div>
              </div>

              {/* HTTP Request/Response Grids */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {/* Request Pane */}
                {(selectedFinding.request_headers || selectedFinding.request_body) && (
                  <div className="flex flex-col">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                      <ChevronRight size={16} className="text-severity-info" /> HTTP Request
                    </h3>
                    <div className="bg-[#0d1117]/80 backdrop-blur rounded-xl border border-border-default/50 overflow-hidden flex-1 shadow-lg">
                      {selectedFinding.request_headers && (
                        <pre className="p-4 text-xs font-mono text-gray-300 whitespace-pre-wrap break-all border-b border-border-default/30">
                          {selectedFinding.request_headers}
                        </pre>
                      )}
                      {selectedFinding.request_body && (
                        <pre className="p-4 text-xs font-mono text-severity-info whitespace-pre-wrap break-all">
                          {selectedFinding.request_body}
                        </pre>
                      )}
                    </div>
                  </div>
                )}

                {/* Response Pane */}
                {(selectedFinding.response_headers || selectedFinding.response_body) && (
                  <div className="flex flex-col">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                      <ChevronRight size={16} className="text-severity-critical" /> HTTP Response
                    </h3>
                    <div className="bg-[#0d1117]/80 backdrop-blur rounded-xl border border-border-default/50 overflow-hidden flex-1 shadow-lg">
                      {selectedFinding.response_headers && (
                        <pre className="p-4 text-xs font-mono text-gray-300 whitespace-pre-wrap break-all border-b border-border-default/30">
                          {selectedFinding.response_headers}
                        </pre>
                      )}
                      {selectedFinding.response_body && (
                        <pre className="p-4 text-xs font-mono text-severity-low whitespace-pre-wrap break-all">
                          {selectedFinding.response_body}
                        </pre>
                      )}
                    </div>
                  </div>
                )}
              </div>

            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 p-8 text-center">
              <Globe size={64} className="mb-4 opacity-20" />
              <h3 className="text-xl font-medium text-gray-400 mb-2">Select a Vulnerability</h3>
              <p>Click on a finding from the list to view detailed HTTP request and response traces.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
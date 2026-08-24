import { useState, useEffect } from 'react';
import { Target, Search, Server, ShieldAlert, Activity, Terminal } from 'lucide-react';
import { useReconStore } from '../../stores/reconStore';
import { cn } from '../../lib/utils';


export function ReconDashboard() {
  const [scanTarget, setScanTarget] = useState('');
  const [selectedTool, setSelectedTool] = useState('nmap');
  const { hosts, isLoading, isScanning, error, fetchHosts, triggerScan } = useReconStore();

  useEffect(() => {
    // In a real app, this would be the active project ID
    fetchHosts('default-project-id');
  }, [fetchHosts]);

  const handleScanSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (scanTarget.trim() && !isScanning) {
      triggerScan(selectedTool, scanTarget.trim());
      setScanTarget('');
    }
  };

  const getPortSeverityColor = (port: number, serviceName: string = '') => {
    const criticalPorts = [21, 22, 23, 3389, 445, 139, 1433, 3306, 5432, 2375];
    const webPorts = [80, 443, 8080, 8443];

    if (criticalPorts.includes(port)) return 'bg-severity-critical/20 text-severity-critical border-severity-critical/50 shadow-[0_0_10px_rgb(var(--severity-critical)/0.2)]';
    if (webPorts.includes(port) || serviceName.includes('http')) return 'bg-severity-info/20 text-severity-info border-severity-info/50 shadow-[0_0_10px_rgb(var(--severity-info)/0.2)]';
    return 'bg-surface-tertiary text-gray-300 border-border-default';
  };

  return (
    <div className="flex flex-col h-full p-8 overflow-y-auto relative bg-transparent">
      
      {/* Dashboard Header */}
      <div className="flex items-center justify-between mb-8 z-10">
        <div>
          <h1 className="text-3xl font-bold text-gray-100 neon-text flex items-center gap-3">
            <Target className="text-border-active" size={32} />
            Attack Surface
          </h1>
          <p className="text-gray-400 mt-2">Manage and analyze discovered infrastructure.</p>
        </div>
      </div>

      {/* Control Bar (Scan Input) */}
      <div className="glass-panel p-4 rounded-2xl mb-8 z-10 border border-border-default/50 flex flex-col md:flex-row gap-4 items-center justify-between shadow-xl">
        <form onSubmit={handleScanSubmit} className="flex-1 w-full max-w-3xl relative flex gap-3">
          <select 
            value={selectedTool} 
            onChange={e => setSelectedTool(e.target.value)}
            disabled={isScanning}
            className="bg-surface-primary/50 border border-border-default/50 rounded-xl px-4 py-3 text-gray-200 focus:outline-none focus:border-border-active transition-all shadow-inner w-48"
          >
            <optgroup label="Port Scanners">
              <option value="nmap">Nmap</option>
              <option value="masscan">Masscan</option>
              <option value="rustscan">Rustscan</option>
              <option value="naabu">Naabu</option>
            </optgroup>
            <optgroup label="Subdomain Enumeration">
              <option value="amass">Amass</option>
              <option value="subfinder">Subfinder</option>
              <option value="dnsx">Dnsx</option>
            </optgroup>
            <optgroup label="Web/Tech Probing">
              <option value="httpx">Httpx</option>
              <option value="whatweb">Whatweb</option>
              <option value="nikto">Nikto</option>
            </optgroup>
            <optgroup label="Fuzzers">
              <option value="ffuf">Ffuf</option>
              <option value="gobuster">Gobuster</option>
              <option value="dirsearch">Dirsearch</option>
            </optgroup>
            <optgroup label="Crawlers">
              <option value="katana">Katana</option>
              <option value="gau">Gau</option>
            </optgroup>
            <optgroup label="DAST">
              <option value="nuclei">Nuclei</option>
            </optgroup>
          </select>
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Terminal size={18} className="text-border-active" />
            </div>
            <input
              type="text"
              value={scanTarget}
              onChange={(e) => setScanTarget(e.target.value)}
              placeholder={selectedTool === 'nmap' ? "Target IP or CIDR (e.g. 192.168.1.0/24)..." : "Target URL (e.g. https://example.com)..."}
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
              <><Search size={16} /> Execute Scan</>
            )}
            </button>
          </div>
        </form>
        
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-severity-critical shadow-[0_0_8px_rgb(var(--severity-critical))] animate-pulse"></span>
            <span className="text-gray-300">High Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-severity-info shadow-[0_0_8px_rgb(var(--severity-info))]"></span>
            <span className="text-gray-300">Web Service</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-severity-critical/10 border border-severity-critical text-severity-critical">
          Error: {error}
        </div>
      )}

      {/* Hosts Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center flex-1">
          <Activity size={48} className="text-border-active animate-spin" />
        </div>
      ) : hosts.length === 0 ? (
        <div className="flex flex-col items-center justify-center flex-1 text-gray-500 glass-panel rounded-2xl mx-auto p-12 max-w-lg mt-12 text-center">
          <Server size={64} className="mb-4 opacity-50" />
          <h3 className="text-xl font-medium text-gray-300 mb-2">No Hosts Discovered</h3>
          <p>Execute a scan above to populate the attack surface.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 z-10 pb-12">
          {hosts.map(host => (
            <div key={host.id} className="glass-panel p-6 rounded-2xl border border-border-default/50 hover:border-border-active/50 transition-all duration-300 group hover:-translate-y-1 hover:shadow-[0_10px_30px_rgb(var(--border-active)/0.1)]">
              
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-surface-tertiary/50 border border-border-default flex items-center justify-center shadow-inner relative overflow-hidden">
                     {/* Ambient glow behind server icon */}
                    <div className="absolute inset-0 bg-border-active opacity-10 blur-md"></div>
                    <Server size={24} className="text-gray-300 relative z-10" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-100">{host.ip}</h3>
                    {host.hostname && <p className="text-sm text-border-active font-mono">{host.hostname}</p>}
                  </div>
                </div>
                <div className={cn(
                  "px-2.5 py-1 rounded-full text-xs font-medium border flex items-center gap-1.5 shadow-sm",
                  host.status === 'up' ? "bg-severity-low/20 text-severity-low border-severity-low/50" : "bg-gray-500/20 text-gray-400 border-gray-500/50"
                )}>
                  <div className={cn("w-1.5 h-1.5 rounded-full", host.status === 'up' ? "bg-severity-low" : "bg-gray-500")} />
                  {host.status.toUpperCase()}
                </div>
              </div>

              {host._enriched && (
                <div className="mb-4 flex items-center justify-between bg-surface-primary/30 p-2.5 rounded-lg border border-border-default/30">
                  <div className="flex items-center gap-2">
                    <ShieldAlert size={16} className={cn(
                      host._enriched.risk.severity === 'Critical' ? 'text-severity-critical' :
                      host._enriched.risk.severity === 'High' ? 'text-severity-high' :
                      host._enriched.risk.severity === 'Medium' ? 'text-severity-medium' :
                      'text-severity-low'
                    )} />
                    <span className="text-sm font-medium text-gray-300">Risk Score:</span>
                  </div>
                  <div className={cn(
                    "px-2 py-0.5 rounded text-xs font-bold",
                    host._enriched.risk.severity === 'Critical' ? 'bg-severity-critical/20 text-severity-critical border border-severity-critical/50' :
                    host._enriched.risk.severity === 'High' ? 'bg-severity-high/20 text-severity-high border border-severity-high/50' :
                    host._enriched.risk.severity === 'Medium' ? 'bg-severity-medium/20 text-severity-medium border border-severity-medium/50' :
                    'bg-severity-low/20 text-severity-low border border-severity-low/50'
                  )}>
                    {host._enriched.risk.risk_score} ({host._enriched.risk.severity})
                  </div>
                </div>
              )}

              <div className="space-y-4">
                {host.os && (
                  <div className="flex items-center gap-2 text-sm text-gray-400 bg-surface-primary/30 p-2.5 rounded-lg border border-border-default/30">
                    <Terminal size={14} />
                    <span className="font-mono">{host.os}</span>
                  </div>
                )}

                <div>
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Open Ports ({host.services.length})</h4>
                  <div className="flex flex-wrap gap-2">
                    {host.services.map((service, idx) => (
                      <div 
                        key={idx}
                        className={cn(
                          "px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors cursor-default",
                          getPortSeverityColor(service.port, service.name)
                        )}
                        title={`${service.name || 'unknown'} ${service.version ? `(${service.version})` : ''}`}
                      >
                        <span className="font-bold mr-1">{service.port}</span>
                        <span className="opacity-80">/ {service.name || service.protocol}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {host._enriched && (
                  <div className="space-y-2 mt-4">
                    {host._enriched.attack_surface.exposed_high_value_ports.length > 0 && (
                      <div className="text-xs flex items-start gap-2 text-severity-critical bg-severity-critical/10 p-2 rounded border border-severity-critical/20">
                        <ShieldAlert size={14} className="mt-0.5 flex-shrink-0" />
                        <span>Exposed high-value ports: {host._enriched.attack_surface.exposed_high_value_ports.join(', ')}</span>
                      </div>
                    )}
                    {host._enriched.attack_surface.outdated_services.length > 0 && (
                      <div className="text-xs flex items-start gap-2 text-severity-high bg-severity-high/10 p-2 rounded border border-severity-high/20">
                        <Activity size={14} className="mt-0.5 flex-shrink-0" />
                        <span>Outdated services detected: {host._enriched.attack_surface.outdated_services.join(', ')}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              <div className="mt-6 pt-4 border-t border-border-default/30 flex justify-between items-center text-xs text-gray-500">
                <span>Last seen: {new Date(host.last_seen).toLocaleString()}</span>
                <button className="text-border-active hover:text-white transition-colors">
                  View Details &rarr;
                </button>
              </div>

            </div>
          ))}
        </div>
      )}
    </div>
  );
}
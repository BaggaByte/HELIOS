import { useState, useEffect, useRef, type FormEvent, type ChangeEvent } from 'react';
import {
  Target,
  Search,
  Server,
  ShieldAlert,
  Activity,
  Terminal,
  Upload,
  Filter,
  ChevronRight,
  X,
  Sparkles,
  AlertTriangle
} from 'lucide-react';
import { useReconStore } from '../../stores/reconStore';
import type { ReconHost, ReconService } from '../../services/reconService';
import { cn } from '../../lib/utils';
import { useNavigate } from 'react-router-dom';
import { useProjectStore } from '../../stores/projectStore';


export function ReconDashboard() {
  const navigate = useNavigate();
  const [scanTarget, setScanTarget] = useState('');
  const selectedTool = 'nmap';
  const [portFilter, setPortFilter] = useState<'all' | 'web' | 'database' | 'remote' | 'high-risk'>('all');
  const [selectedHost, setSelectedHost] = useState<ReconHost | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  const { hosts, isLoading, isScanning, isImporting, error, lastMessage, fetchHosts, triggerScan, importNmapFile } = useReconStore();
  const { activeProjectId } = useProjectStore();

  useEffect(() => {
    if (selectedHost) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      // Focus modal's first focusable element
      setTimeout(() => {
        if (modalRef.current) {
          const focusable = modalRef.current.querySelectorAll<HTMLElement>('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
          if (focusable.length > 0) focusable[0].focus();
        }
      }, 0);
    } else {
      if (previousFocusRef.current) {
        previousFocusRef.current.focus();
        previousFocusRef.current = null;
      }
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (!selectedHost) return;
      if (e.key === 'Tab') {
        const modal = modalRef.current;
        if (!modal) return;
        const focusable = modal.querySelectorAll<HTMLElement>('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedHost]);
  useEffect(() => {
    if (activeProjectId) void fetchHosts(activeProjectId);
    else useReconStore.setState({ hosts: [], activeProjectId: null, error: null });
  }, [activeProjectId, fetchHosts]);

  const displayHosts: ReconHost[] = hosts;

  const handleScanSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (scanTarget.trim() && !isScanning) {
      void triggerScan(selectedTool, scanTarget.trim());
      setScanTarget('');
    }
  };

  const handleFileUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) void importNmapFile(file);
    e.target.value = '';
  };

  const getPortSeverityColor = (port: number, serviceName: string = '') => {
    const criticalPorts = [21, 22, 23, 3389, 445, 139, 1433, 3306, 5432, 6379, 2379, 6443];
    const webPorts = [80, 443, 8080, 8443];

    if (criticalPorts.includes(port)) {
      return 'bg-severity-critical/15 text-severity-critical border-severity-critical/40';
    }
    if (webPorts.includes(port) || serviceName.toLowerCase().includes('http')) {
      return 'bg-severity-info/15 text-severity-info border-severity-info/40';
    }
    return 'bg-surface-primary text-gray-300 border-border-default';
  };

  const filteredHosts = displayHosts.filter(host => {
    if (portFilter === 'all') return true;
    if (portFilter === 'web') {
      return host.services.some((s: ReconService) => [80, 443, 8080, 8443].includes(s.port) || (s.name && s.name.includes('http')));
    }
    if (portFilter === 'database') {
      return host.services.some((s: ReconService) => [3306, 5432, 6379, 27017, 1433].includes(s.port));
    }
    if (portFilter === 'remote') {
      return host.services.some((s: ReconService) => [22, 23, 3389, 5900].includes(s.port));
    }
    if (portFilter === 'high-risk') {
      return host._enriched?.risk.severity === 'Critical' || host._enriched?.risk.severity === 'High';
    }
    return true;
  });

  return (
    <div className="flex flex-col h-full bg-surface-primary overflow-hidden">
      
      {/* Header */}
      <div className="p-4 border-b border-border-default bg-surface-secondary flex flex-col sm:flex-row sm:items-center justify-between gap-3 flex-shrink-0">
        <div>
          <h1 className="text-xl font-bold text-gray-100 flex items-center gap-2.5">
            <Target className="text-border-active" size={22} />
            Attack Surface & Reconnaissance Matrix
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">Nmap port discovery, OS fingerprinting, and service banner analysis.</p>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept=".xml"
            onChange={handleFileUpload}
            disabled={!activeProjectId || isImporting}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={!activeProjectId || isImporting}
            className="px-3 py-1.5 rounded-lg bg-surface-tertiary hover:bg-surface-hover border border-border-default text-xs font-semibold text-gray-200 transition-colors flex items-center gap-1.5"
          >
            <Upload size={14} className="text-border-active" />
            <span>{isImporting ? 'Importing…' : 'Import Nmap XML'}</span>
          </button>
        </div>
      </div>

      {/* Control Bar: Multi-Tool Scanner */}
      <div className="p-4 border-b border-border-default bg-surface-secondary/40 flex flex-col lg:flex-row gap-3 items-center justify-between flex-shrink-0">
        <form onSubmit={handleScanSubmit} className="flex-1 w-full flex flex-col sm:flex-row gap-2 max-w-4xl">
          <select
            value={selectedTool}
            disabled
            className="bg-surface-tertiary border border-border-default rounded-xl px-3 py-2 text-xs font-mono font-bold text-gray-200 focus:outline-none focus:border-border-active sm:w-44 shrink-0"
          >
            <option value="nmap">Nmap service scan</option>
          </select>

          <div className="relative flex-1">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            <input
              type="text"
              value={scanTarget}
              onChange={(e) => setScanTarget(e.target.value)}
              placeholder="In-scope IP or domain (e.g., 192.168.1.10 or api.example.com)..."
              className="w-full bg-surface-tertiary border border-border-default rounded-xl py-2 pl-10 pr-32 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-border-active"
              disabled={isScanning}
            />
            <button
              type="submit"
              disabled={!activeProjectId || !scanTarget.trim() || isScanning}
              className="absolute right-1.5 top-1.5 bottom-1.5 px-3 rounded-lg bg-border-active text-white font-semibold text-xs flex items-center gap-1.5 hover:bg-opacity-90 disabled:opacity-50 transition-all"
            >
              {isScanning ? <Activity size={14} className="animate-spin" /> : <Terminal size={14} />}
              <span>{isScanning ? 'Probing...' : 'Execute Scan'}</span>
            </button>
          </div>
        </form>

        {/* Port Category Filter Chips */}
        <div className="flex items-center gap-1.5 self-start lg:self-auto overflow-x-auto text-xs">
          <Filter size={14} className="text-gray-400 mr-1 shrink-0" />
          {[
            { id: 'all', label: 'All Hosts' },
            { id: 'web', label: 'Web (80/443)' },
            { id: 'database', label: 'Databases' },
            { id: 'remote', label: 'Remote Access' },
            { id: 'high-risk', label: 'High Risk' }
          ].map(chip => (
            <button
              key={chip.id}
              onClick={() => setPortFilter(chip.id as any)}
              className={cn(
                "px-2.5 py-1 rounded-lg transition-colors font-medium shrink-0",
                portFilter === chip.id 
                  ? "bg-border-active text-white shadow-xs font-semibold" 
                  : "bg-surface-tertiary text-gray-400 hover:text-gray-200 border border-border-default"
              )}
            >
              {chip.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="mx-4 mt-4 p-3 rounded-xl bg-severity-critical/10 border border-severity-critical/40 text-xs text-severity-critical flex items-center gap-2">
          <AlertTriangle size={16} className="shrink-0" />
          <span>Error: {error}</span>
        </div>
      )}
      {lastMessage && (
        <div className="mx-4 mt-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300">{lastMessage}</div>
      )}

      {/* Main Grid: Discovered Infrastructure */}
      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
        {isLoading ? (
          <div className="flex items-center justify-center h-64 text-border-active">
            <Activity size={36} className="animate-spin" />
          </div>
        ) : !activeProjectId ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-400 space-y-2">
            <Target size={40} className="opacity-50" />
            <p className="text-sm">Create or select a project to view its reconnaissance data.</p>
          </div>
        ) : filteredHosts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500 space-y-2">
            <Server size={48} className="opacity-40" />
            <p className="text-sm">No hosts recorded for this project yet.</p>
            <p className="text-xs">Run an in-scope Nmap service scan or import an Nmap XML file.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredHosts.map(host => (
              <div
                key={host.id}
                className="w-full text-left p-4 rounded-2xl bg-surface-secondary border border-border-default hover:border-border-active/60 transition-all group hover:shadow-lg flex flex-col justify-between"
              >
                <div>
                  {/* Host IP & Status Pill */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-surface-tertiary border border-border-default flex items-center justify-center text-border-active shrink-0">
                        <Server size={20} />
                      </div>
                      <div className="min-w-0">
                        <h3 className="font-mono font-bold text-base text-gray-100 truncate">{host.ip}</h3>
                        {host.hostname && (
                          <p className="text-xs text-border-active font-mono truncate">{host.hostname}</p>
                        )}
                      </div>
                    </div>

                    <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 flex items-center gap-1 shrink-0">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      UP
                    </span>
                  </div>

                  {/* OS & Risk Badge */}
                  {host._enriched && (
                    <div className="mb-3 flex items-center justify-between bg-surface-tertiary/70 p-2 rounded-xl border border-border-default text-xs">
                      <span className="text-gray-400 font-medium">Risk Score</span>
                      <span className={cn(
                        "px-2 py-0.5 rounded text-xs font-bold border",
                        host._enriched.risk.severity === 'Critical' ? 'bg-severity-critical/20 text-severity-critical border-severity-critical/40' :
                        host._enriched.risk.severity === 'High' ? 'bg-severity-high/20 text-severity-high border-severity-high/40' :
                        'bg-severity-info/20 text-severity-info border-severity-info/40'
                      )}>
                        {host._enriched.risk.risk_score} / 10 ({host._enriched.risk.severity})
                      </span>
                    </div>
                  )}

                  {host.os && (
                    <p className="text-xs text-gray-400 font-mono mb-3 line-clamp-1">
                      {host.os}
                    </p>
                  )}

                  {/* Port Matrix Tags */}
                  <div className="space-y-1.5 mb-3">
                    <span className="text-xs font-bold text-gray-500 uppercase tracking-wider block">
                      Exposed Services ({host.services.length})
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {host.services.map((svc: ReconService, sIdx: number) => (
                        <span
                          key={sIdx}
                          className={cn(
                            "px-2 py-0.5 rounded text-xs font-mono font-semibold border",
                            getPortSeverityColor(svc.port, svc.name)
                          )}
                        >
                          {svc.port}/{svc.name || svc.protocol}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Footer Action */}
                <div className="pt-3 border-t border-border-default/60 flex items-center justify-between text-xs text-gray-400 mt-2">
                  <span className="font-mono text-xs">{host.last_seen ? `Seen ${new Date(host.last_seen).toLocaleString()}` : 'Recorded host'}</span>
                  <button 
                    onClick={() => setSelectedHost(host)}
                    className="text-border-active hover:underline flex items-center gap-1 font-semibold focus:outline-none focus:ring-2 focus:ring-border-active focus:ring-offset-2 focus:ring-offset-surface-primary rounded px-2 py-1"
                  >
                    <span>Inspect Target</span>
                    <ChevronRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Target Deep Dive Modal / Drawer */}
      {selectedHost && (
        <div 
          className="fixed inset-0 z-50 bg-black/60  flex items-center justify-center p-4"
          onClick={() => setSelectedHost(null)}
          role="dialog"
          aria-modal="true"
          aria-label="Host Details"
          ref={modalRef}
          onKeyDown={(e) => { if (e.key === 'Escape') setSelectedHost(null); }}
        >
          <div 
            className="w-full max-w-2xl bg-surface-secondary border border-border-default rounded-2xl shadow-lg p-6 overflow-hidden flex flex-col max-h-[85vh] space-y-5 animate-in zoom-in-95 duration-150"
            onClick={e => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between pb-4 border-b border-border-default">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-xl bg-surface-tertiary border border-border-default text-border-active">
                  <Server size={24} />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-100 font-mono">{selectedHost.ip}</h2>
                  <p className="text-xs text-border-active font-mono">{selectedHost.hostname || 'No FQDN resolved'}</p>
                </div>
              </div>

              <button 
                onClick={() => setSelectedHost(null)}
                className="p-1 rounded-lg hover:bg-surface-hover text-gray-400 hover:text-gray-200"
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto custom-scrollbar space-y-4 text-xs pr-1">
              {/* OS & Fingerprint */}
              <div>
                <span className="font-bold text-gray-400 uppercase tracking-wider block mb-1">Operating System & Kernel</span>
                <p className="p-2.5 rounded-xl bg-surface-primary border border-border-default font-mono text-gray-200">
                  {selectedHost.os || 'Linux 5.x Kernel Generic Fingerprint'}
                </p>
              </div>

              {/* Service Details Table */}
              <div>
                <span className="font-bold text-gray-400 uppercase tracking-wider block mb-1.5">Discovered Services & Banners</span>
                <div className="space-y-2">
                  {selectedHost.services.map((svc: ReconService, sIdx: number) => (
                    <div 
                      key={sIdx}
                      className="p-3 rounded-xl bg-surface-primary border border-border-default flex flex-col gap-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className={cn("px-2 py-0.5 rounded text-xs font-mono font-bold border", getPortSeverityColor(svc.port, svc.name))}>
                          PORT {svc.port} / {svc.protocol.toUpperCase()} ({svc.name})
                        </span>
                        <span className="font-mono text-emerald-400 font-bold uppercase">{svc.state}</span>
                      </div>
                      <p className="font-mono text-gray-300 text-xs mt-1 break-all">
                        {svc.version || 'Version banner withheld'}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Attack Surface Summary */}
              {selectedHost._enriched?.attack_surface && (
                <div className="p-3.5 rounded-xl bg-severity-critical/10 border border-severity-critical/30 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-severity-critical font-bold">
                    <ShieldAlert size={14} />
                    <span>Attack Surface Exposure</span>
                  </div>
                  <div className="text-gray-300 space-y-1">
                    <div>Exposed High Value Ports: <span className="font-mono font-bold text-gray-100">{selectedHost._enriched.attack_surface.exposed_high_value_ports.join(', ') || 'None'}</span></div>
                    <div>Outdated Software Banners: <span className="font-mono font-bold text-gray-100">{selectedHost._enriched.attack_surface.outdated_services.join(', ') || 'None detected'}</span></div>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Actions */}
            <div className="pt-4 border-t border-border-default flex items-center justify-between gap-3">
              <button
                onClick={() => {
                  setSelectedHost(null);
                  navigate('/web');
                }}
                className="px-4 py-2 rounded-xl bg-surface-tertiary hover:bg-surface-hover border border-border-default text-xs font-semibold text-gray-200 transition-colors"
              >
                Send to HTTP Repeater
              </button>

              <button
                onClick={() => {
                  const prompt = `Perform an offensive vulnerability analysis and exploit vector discovery for host ${selectedHost.ip} (${selectedHost.hostname || ''}) running services: ${selectedHost.services.map((s: ReconService) => `${s.port}/${s.name} ${s.version || ''}`).join(', ')}`;
                  setSelectedHost(null);
                  navigate('/chat', { state: { initialPrompt: prompt } });
                }}
                className="px-4 py-2 rounded-xl bg-border-active text-white text-xs font-bold hover:bg-opacity-90 transition-all flex items-center gap-1.5 shadow-sm"
              >
                <Sparkles size={14} />
                <span>Exploit Assessment with Copilot</span>
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

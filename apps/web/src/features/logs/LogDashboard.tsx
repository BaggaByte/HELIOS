import { useState, useRef } from 'react';
import { Activity, Upload, Search, Filter, FileText, Loader2, ChevronLeft, ChevronRight, Clock, Terminal, AlertCircle, ShieldCheck } from 'lucide-react';
import { useLogs, type LogEvent } from '../../hooks/useLogs';
import { cn } from '../../lib/utils';
import { useProjectStore } from '../../stores/projectStore';
import { getSeverityClasses } from '../../utils/severity';

export function LogDashboard() {
  const {
    events,
    isLoading,
    error,
    page,
    setPage,
    severityFilter,
    setSeverityFilter,
    sourceFilter,
    setSourceFilter,
    ingestLogs,
    isIngesting,
    ingestError
  } = useLogs();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEvent, setSelectedEvent] = useState<LogEvent | null>(null);
  const [logType, setLogType] = useState('suricata');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const activeProjectId = useProjectStore(state => state.activeProjectId);

  const filteredEvents = events.filter(evt => {
    if (severityFilter && evt.severity.toLowerCase() !== severityFilter.toLowerCase()) return false;
    if (sourceFilter && evt.source.toLowerCase() !== sourceFilter.toLowerCase()) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        evt.message.toLowerCase().includes(q) ||
        evt.source.toLowerCase().includes(q) ||
        (evt.source_ip && evt.source_ip.toLowerCase().includes(q)) ||
        (evt.dest_ip && evt.dest_ip.toLowerCase().includes(q)) ||
        evt.event_type.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const handleFileUpload = async (file: File) => {
    try {
      await ingestLogs({ file, type: logType });
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      console.error('Log ingest failed:', err);
    }
  };



  return (
    <div className="flex flex-col h-full bg-surface-primary overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border-default bg-surface-secondary flex-shrink-0">
        <div>
          <h1 className="text-xl font-bold text-gray-100 flex items-center gap-2">
            <Activity className="text-border-active" size={22} />
            SIEM & Log Intelligence
          </h1>
          <p className="text-sm text-gray-400 mt-1">Multi-source timeline reconstruction, alert correlation, and parser ingestion</p>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            onChange={(e) => {
              if (e.target.files?.[0]) handleFileUpload(e.target.files[0]);
            }}
          />
          <select
            value={logType}
            onChange={(e) => setLogType(e.target.value)}
            className="bg-surface-tertiary border border-border-default rounded-lg px-3 py-1.5 text-xs text-gray-200 focus:border-border-active outline-none"
          >
            <option value="suricata">Suricata EVE JSON</option>
            <option value="nginx">Nginx Access/Error</option>
            <option value="apache">Apache Access</option>
          </select>
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isIngesting || !activeProjectId}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-border-active text-white text-xs font-semibold hover:bg-opacity-90 disabled:opacity-50 transition-colors"
          >
            {isIngesting ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
            {isIngesting ? 'Ingesting...' : 'Ingest Log File'}
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 border-b border-border-default bg-surface-secondary/50 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-1 min-w-[280px]">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search current page of events..."
              className="w-full bg-surface-tertiary border border-border-default rounded-lg pl-9 pr-3 py-1.5 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-border-active"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Filter size={14} className="text-gray-400" />
          <div className="flex rounded-lg border border-border-default overflow-hidden text-xs">
            <button
              onClick={() => setSeverityFilter(null)}
              className={cn('px-2.5 py-1 transition-colors', !severityFilter ? 'bg-border-active text-white font-semibold' : 'bg-surface-tertiary text-gray-400 hover:text-gray-200')}
            >
              All
            </button>
            <button
              onClick={() => setSeverityFilter('critical')}
              className={cn('px-2.5 py-1 transition-colors', severityFilter === 'critical' ? 'bg-severity-critical text-white font-semibold' : 'bg-surface-tertiary text-gray-400 hover:text-gray-200')}
            >
              Critical
            </button>
            <button
              onClick={() => setSeverityFilter('high')}
              className={cn('px-2.5 py-1 transition-colors', severityFilter === 'high' ? 'bg-severity-high text-white font-semibold' : 'bg-surface-tertiary text-gray-400 hover:text-gray-200')}
            >
              High
            </button>
            <button
              onClick={() => setSeverityFilter('medium')}
              className={cn('px-2.5 py-1 transition-colors', severityFilter === 'medium' ? 'bg-severity-medium text-white font-semibold' : 'bg-surface-tertiary text-gray-400 hover:text-gray-200')}
            >
              Medium
            </button>
          </div>

          <select
            value={sourceFilter || ''}
            onChange={(e) => setSourceFilter(e.target.value ? e.target.value : null)}
            className="bg-surface-tertiary border border-border-default rounded-lg px-2.5 py-1 text-xs text-gray-200 focus:border-border-active outline-none"
          >
            <option value="">All Sources</option>
            <option value="suricata">Suricata</option>
            <option value="nginx">Nginx</option>
            <option value="apache">Apache</option>
            <option value="linux_auth">Linux Auth</option>
            <option value="sysmon">Sysmon</option>
          </select>
        </div>
      </div>

      {/* Error Banners */}
      {(error || ingestError) && (
        <div className="mx-4 mt-4 p-3 rounded-lg bg-severity-critical/10 border border-severity-critical/30 text-xs text-severity-critical flex items-center gap-2">
          <AlertCircle size={16} className="shrink-0" />
          <span>{error ? `Failed to load logs: ${error.message}` : `Ingestion error: ${(ingestError as Error)?.message || 'Failed to ingest log file'}`}</span>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 overflow-hidden flex flex-col lg:flex-row">
        {/* Events Table / Timeline */}
        <div className="flex-1 overflow-y-auto p-4 custom-scrollbar space-y-2">
          {isLoading ? (
            <div className="flex items-center justify-center h-64 text-border-active">
              <Loader2 size={32} className="animate-spin" />
            </div>
          ) : !activeProjectId ? (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500 space-y-2">
              <ShieldCheck size={40} className="opacity-40 text-amber-400" />
              <p className="text-sm font-semibold">No Project Selected</p>
              <p className="text-xs text-center max-w-md">You must select a project to view its SIEM feed and log events.</p>
            </div>
          ) : filteredEvents.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500 space-y-2">
              <FileText size={40} className="opacity-40" />
              <p className="text-sm">No log events match the current filter.</p>
            </div>
          ) : (
            filteredEvents.map((evt) => (
              <button
                key={evt.id}
                onClick={() => setSelectedEvent(evt)}
                className={cn(
                  'w-full text-left p-3 rounded-xl border text-sm transition-all cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-3 focus:outline-none focus:ring-2 focus:ring-border-active focus:ring-offset-2 focus:ring-offset-surface-primary',
                  selectedEvent?.id === evt.id
                    ? 'bg-surface-tertiary border-border-active shadow-md'
                    : 'bg-surface-secondary/70 border-border-default hover:border-gray-500 hover:bg-surface-secondary'
                )}
              >
                <div className="flex items-start md:items-center gap-3 flex-1 min-w-0">
                  <span className={cn('px-2 py-0.5 rounded text-xs font-bold uppercase border shrink-0', getSeverityClasses(evt.severity))}>
                    {evt.severity}
                  </span>

                  <div className="flex items-center gap-2 text-xs text-gray-400 font-mono shrink-0">
                    <Clock size={12} />
                    <span>{new Date(evt.timestamp).toLocaleTimeString()}</span>
                  </div>

                  <span className="px-2 py-0.5 rounded text-xs bg-surface-tertiary text-gray-300 border border-border-default shrink-0 font-mono">
                    {evt.source}
                  </span>

                  <span className="text-gray-200 truncate font-medium">{evt.message}</span>
                </div>

                <div className="flex items-center gap-3 text-xs font-mono text-gray-400 shrink-0 self-end md:self-center">
                  {evt.source_ip && (
                    <span className="bg-surface-primary/60 px-2 py-0.5 rounded border border-border-default">
                      SRC: {evt.source_ip}
                    </span>
                  )}
                  {evt.dest_ip && (
                    <span className="bg-surface-primary/60 px-2 py-0.5 rounded border border-border-default">
                      DST: {evt.dest_ip}
                    </span>
                  )}
                </div>
              </button>
            ))
          )}
        </div>

        {/* Selected Event Inspector Side Panel */}
        {selectedEvent && (
          <div className="w-full lg:w-96 border-t lg:border-t-0 lg:border-l border-border-default bg-surface-secondary p-5 overflow-y-auto flex flex-col gap-4 shadow-md">
            <div className="flex items-center justify-between border-b border-border-default/60 pb-3">
              <div className="flex items-center gap-2">
                <Terminal size={16} className="text-border-active" />
                <h3 className="font-bold text-gray-100 text-sm">Event Details</h3>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-xs text-gray-400 hover:text-gray-200"
              >
                Close
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-gray-500 uppercase font-bold tracking-wider block mb-1">Timestamp</span>
                <span className="font-mono text-gray-200 bg-surface-primary p-2 rounded border border-border-default block">
                  {new Date(selectedEvent.timestamp).toUTCString()} ({selectedEvent.timestamp})
                </span>
              </div>

              <div>
                <span className="text-gray-500 uppercase font-bold tracking-wider block mb-1">Message</span>
                <p className="text-gray-200 bg-surface-primary p-2 rounded border border-border-default leading-relaxed">
                  {selectedEvent.message}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-gray-500 uppercase font-bold tracking-wider block mb-1">Source IP</span>
                  <span className="font-mono text-gray-200 bg-surface-primary p-1.5 rounded border border-border-default block">
                    {selectedEvent.source_ip || 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500 uppercase font-bold tracking-wider block mb-1">Destination IP</span>
                  <span className="font-mono text-gray-200 bg-surface-primary p-1.5 rounded border border-border-default block">
                    {selectedEvent.dest_ip || 'N/A'}
                  </span>
                </div>
              </div>

              {selectedEvent.metadata && Object.keys(selectedEvent.metadata).length > 0 && (
                <div>
                  <span className="text-gray-500 uppercase font-bold tracking-wider block mb-1">Parser Metadata</span>
                  <pre className="bg-surface-primary p-2.5 rounded border border-border-default text-gray-300 font-mono text-xs overflow-x-auto">
                    {JSON.stringify(selectedEvent.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Pagination Footer */}
      <div className="p-3 border-t border-border-default bg-surface-secondary flex items-center justify-between text-xs text-gray-400">
        <span>Showing page {page}</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page <= 1}
            className="p-1.5 rounded bg-surface-tertiary border border-border-default hover:text-gray-200 disabled:opacity-40 transition-colors"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="px-2 font-mono">{page}</span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={filteredEvents.length < 50}
            className="p-1.5 rounded bg-surface-tertiary border border-border-default hover:text-gray-200 disabled:opacity-40 transition-colors"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

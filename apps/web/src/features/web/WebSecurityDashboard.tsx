import { useRef, useState, type ChangeEvent } from 'react';
import { Activity, AlertTriangle, FileUp, Globe, ShieldAlert } from 'lucide-react';
import { useWebSecurity } from '../../hooks/useWebSecurity';
import { useProjectStore } from '../../stores/projectStore';
import { cn } from '../../lib/utils';
import { getSeverityClasses } from '../../utils/severity';

export function WebSecurityDashboard() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { findings = [], isLoading, error, uploadZap, isUploading, uploadError } = useWebSecurity();
  const activeProjectId = useProjectStore(state => state.activeProjectId);
  const selected = findings.find(finding => finding.id === selectedId) ?? findings[0];



  const handleImport = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      await uploadZap(file);
    } finally {
      event.target.value = '';
    }
  };

  return (
    <div className="flex h-full flex-col overflow-hidden bg-surface-primary">
      <header className="flex items-center justify-between gap-4 border-b border-border-default bg-surface-secondary p-4">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold text-gray-100"><Globe className="text-border-active" size={22} />Web Security Findings</h1>
          <p className="mt-1 text-xs text-gray-400">Review persisted findings imported from OWASP ZAP XML for the selected project.</p>
        </div>
        <div>
          <input ref={inputRef} type="file" accept=".xml" className="hidden" onChange={handleImport} />
          <button onClick={() => inputRef.current?.click()} disabled={!activeProjectId || isUploading} className="flex items-center gap-2 rounded-lg bg-border-active px-3 py-2 text-xs font-semibold text-white disabled:opacity-50">
            {isUploading ? <Activity size={15} className="animate-spin" /> : <FileUp size={15} />}
            {isUploading ? 'Importing report…' : 'Import ZAP XML'}
          </button>
        </div>
      </header>

      {(error || uploadError) && <div className="mx-4 mt-3 rounded-lg border border-severity-critical/30 bg-severity-critical/10 p-3 text-xs text-severity-critical">{(error ?? uploadError) instanceof Error ? (error ?? uploadError)?.message : 'Could not load web security findings.'}</div>}

      {!activeProjectId ? (
        <div className="flex flex-1 items-center justify-center p-6 text-sm text-gray-400">Create or select a project to view its findings.</div>
      ) : isLoading ? (
        <div className="flex flex-1 items-center justify-center text-border-active"><Activity className="animate-spin" /></div>
      ) : findings.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 p-6 text-center text-gray-400">
          <ShieldAlert size={38} className="opacity-50" />
          <p className="text-sm">No web findings have been imported for this project.</p>
          <p className="max-w-md text-xs">Export an XML report from OWASP ZAP and import it here. HELIOS currently does not run a DAST scanner itself.</p>
        </div>
      ) : (
        <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
          <div className="w-full shrink-0 space-y-2 overflow-y-auto border-b border-border-default p-3 lg:w-96 lg:border-b-0 lg:border-r">
            {findings.map(finding => (
              <button key={finding.id} onClick={() => setSelectedId(finding.id)} className={cn('w-full rounded-xl border p-3 text-left transition-colors', selected?.id === finding.id ? 'border-border-active bg-surface-tertiary' : 'border-border-default bg-surface-secondary hover:bg-surface-tertiary')}>
                <div className="mb-2 flex items-center justify-between gap-2">
                  <span className={cn('rounded border px-2 py-0.5 text-xs font-bold uppercase', getSeverityClasses(finding.severity))}>{finding.severity}</span>
                  <span className="text-xs text-gray-500">{finding.status}</span>
                </div>
                <h2 className="text-sm font-semibold text-gray-100">{finding.title}</h2>
                {finding.cwe_id && <p className="mt-1 font-mono text-xs text-gray-500">{finding.cwe_id}</p>}
              </button>
            ))}
          </div>

          {selected && <article className="min-h-0 flex-1 overflow-y-auto p-5 lg:p-8">
            <div className="mx-auto max-w-4xl space-y-5">
              <div className="flex items-start gap-3 border-b border-border-default pb-4">
                <div className={cn('rounded-xl border p-3', getSeverityClasses(selected.severity))}><AlertTriangle size={22} /></div>
                <div>
                  <h2 className="text-xl font-bold text-gray-100">{selected.title}</h2>
                  <p className="mt-1 text-xs text-gray-400">{selected.severity} · Confidence: {selected.confidence} · {selected.created_at ? new Date(selected.created_at).toLocaleString() : 'Date unavailable'}</p>
                </div>
              </div>
              <section><h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-gray-400">Description</h3><p className="whitespace-pre-wrap rounded-xl border border-border-default bg-surface-secondary p-4 text-sm leading-relaxed text-gray-200">{selected.description}</p></section>
              {selected.impact && <section><h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-gray-400">Impact</h3><p className="whitespace-pre-wrap rounded-xl border border-border-default bg-surface-secondary p-4 text-sm text-gray-200">{selected.impact}</p></section>}
              {selected.remediation && <section><h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-gray-400">Remediation</h3><p className="whitespace-pre-wrap rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-4 text-sm text-gray-200">{selected.remediation}</p></section>}
              {!!selected.references?.length && <section><h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-gray-400">References</h3><ul className="list-inside list-disc space-y-1 text-sm text-border-active">{selected.references.map(reference => <li key={reference}><a href={reference} target="_blank" rel="noreferrer" className="break-all underline">{reference}</a></li>)}</ul></section>}
            </div>
          </article>}
        </div>
      )}
    </div>
  );
}

import { useQuery } from '@tanstack/react-query';
import { Activity, Cpu, Database, RefreshCw, Shield, Wrench, Sparkles, AlertCircle, CheckCircle2, Terminal } from 'lucide-react';
import { useProjectStore } from '../../stores/projectStore';
import { apiClient } from '../../services/apiClient';

interface SystemStatus {
  os?: string;
  release?: string;
  cpu_percent?: number;
  memory?: { total_gb: number; available_gb: number; percent: number };
  openvino?: Record<string, unknown>;
}

interface PublicSettings {
  app_name: string;
  app_version: string;
  debug_mode: boolean;
  ov_device: string;
  ov_model_path: string;
}

async function getJson<T>(path: string): Promise<T> {
  return apiClient.get<T>(path);
}

export function SettingsDashboard() {
  const { data: status, error: statusError, isLoading: statusLoading, refetch } = useQuery({
    queryKey: ['system_status'],
    queryFn: () => getJson<SystemStatus>('/system/status'),
  });
  const { data: settings } = useQuery({
    queryKey: ['system_settings'],
    queryFn: () => getJson<PublicSettings>('/system/settings'),
  });
  const activeProjectId = useProjectStore(state => state.activeProjectId);
  const activeProject = useProjectStore(state => state.projects.find(project => project.id === state.activeProjectId));

  const metrics = [
    { label: 'Operating system', value: status ? `${status.os ?? 'Unknown'} ${status.release ?? ''}` : '—' },
    { label: 'CPU load', value: status?.cpu_percent == null ? '—' : `${status.cpu_percent}%` },
    { label: 'Memory', value: status?.memory ? `${status.memory.available_gb} GB available / ${status.memory.total_gb} GB` : '—' },
    { label: 'OpenVINO device', value: settings?.ov_device ?? '—' },
  ];

  // Parse AI model status from the openvino runtime report
  const ovStatus = status?.openvino as Record<string, unknown> | undefined;
  const modelLoaded = Boolean(ovStatus?.model_loaded ?? ovStatus?.pipeline_loaded ?? false);
  const mockMode = !modelLoaded;
  const modelPath = settings?.ov_model_path ?? '../models/phi4_mini_int4_ov';

  return (
    <div className="h-full overflow-y-auto bg-surface-primary p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <header className="flex items-center justify-between gap-4">
          <div>
            <h1 className="flex items-center gap-3 text-2xl font-bold text-gray-100"><Activity className="text-border-active" />System Status</h1>
            <p className="mt-1 text-sm text-gray-400">Read-only diagnostics for the local HELIOS backend and active project.</p>
          </div>
          <button onClick={() => void refetch()} className="flex items-center gap-2 rounded-lg border border-border-default bg-surface-secondary px-3 py-2 text-xs text-gray-200 hover:bg-surface-tertiary"><RefreshCw size={14} />Refresh</button>
        </header>

        {statusError && <div className="rounded-lg border border-severity-critical/30 bg-severity-critical/10 p-3 text-sm text-severity-critical">{statusError instanceof Error ? statusError.message : 'Backend is unavailable.'}</div>}

        {/* ── AI Model Status Card ─────────────────────────────────────────── */}
        <section className={`rounded-2xl border p-5 ${modelLoaded ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-amber-500/30 bg-amber-500/5'}`}>
          <h2 className="mb-4 flex items-center gap-2 text-sm font-bold text-gray-100">
            <Sparkles size={17} className={modelLoaded ? 'text-emerald-400' : 'text-amber-400'} />
            AI Model Status
          </h2>
          {statusLoading ? (
            <p className="text-sm text-gray-400">Checking model status…</p>
          ) : (
            <div className="flex items-start gap-4">
              <div className={`mt-0.5 flex-shrink-0 rounded-full p-1.5 ${modelLoaded ? 'bg-emerald-500/20' : 'bg-amber-500/20'}`}>
                {modelLoaded
                  ? <CheckCircle2 size={20} className="text-emerald-400" />
                  : <AlertCircle size={20} className="text-amber-400" />
                }
              </div>
              <div className="flex-1">
                <p className={`font-semibold ${modelLoaded ? 'text-emerald-300' : 'text-amber-300'}`}>
                  {modelLoaded ? 'AI Model Loaded — Full inference active' : 'AI Model Missing — Running in Mock Mode'}
                </p>
                {mockMode && (
                  <div className="mt-3 space-y-3">
                    <p className="text-sm text-gray-400">
                      The Phi-4 Mini INT4 OpenVINO model is not present at{' '}
                      <code className="rounded bg-surface-tertiary px-1 py-0.5 font-mono text-xs text-gray-200">{modelPath}</code>.
                      AI chat, AI report summaries, and context-aware analysis will return placeholder responses until the model is downloaded.
                    </p>
                    <div className="rounded-xl border border-border-default bg-surface-primary p-4">
                      <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-gray-300">
                        <Terminal size={13} />
                        To enable full AI, run one of the following in the HELIOS root directory:
                      </p>
                      <pre className="text-xs text-emerald-400 font-mono whitespace-pre-wrap">{`# Windows PowerShell\npowershell scripts/download_model.ps1\n\n# Linux / macOS\nbash scripts/download_model.sh`}</pre>
                      <p className="mt-2 text-xs text-gray-500">
                        This downloads ~2 GB. An internet connection is required only for the initial download.
                        All inference runs locally on your CPU/GPU/NPU — no data leaves your machine.
                      </p>
                    </div>
                  </div>
                )}
                {modelLoaded && (
                  <p className="mt-1 text-sm text-gray-400">
                    Inference device: <span className="font-mono text-gray-200">{String(ovStatus?.device ?? settings?.ov_device ?? 'AUTO')}</span>
                  </p>
                )}
              </div>
            </div>
          )}
        </section>

        {/* ── Runtime diagnostics ───────────────────────────────────────────── */}
        <section className="rounded-2xl border border-border-default bg-surface-secondary p-5">
          <h2 className="mb-4 flex items-center gap-2 text-sm font-bold text-gray-100"><Cpu size={17} className="text-border-active" />Runtime diagnostics</h2>
          {statusLoading ? <p className="text-sm text-gray-400">Loading status…</p> : <dl className="grid gap-4 sm:grid-cols-2">
            {metrics.map(metric => <div key={metric.label} className="rounded-xl border border-border-default bg-surface-primary p-4"><dt className="text-xs uppercase tracking-wide text-gray-500">{metric.label}</dt><dd className="mt-1 break-all font-mono text-sm text-gray-200">{metric.value}</dd></div>)}
          </dl>}
          <div className="mt-4 rounded-xl border border-border-default bg-surface-primary p-4">
            <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-gray-300"><Wrench size={14} />OpenVINO runtime report</div>
            <pre className="overflow-x-auto whitespace-pre-wrap text-xs text-gray-400">{JSON.stringify(status?.openvino ?? { status: statusLoading ? 'loading' : 'unavailable' }, null, 2)}</pre>
          </div>
        </section>

        <section className="grid gap-6 md:grid-cols-2">
          <div className="rounded-2xl border border-border-default bg-surface-secondary p-5">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-bold text-gray-100"><Database size={17} className="text-border-active" />Application configuration</h2>
            <dl className="space-y-3 text-xs">
              <div className="flex justify-between gap-4"><dt className="text-gray-500">Application</dt><dd className="font-mono text-gray-200">{settings?.app_name ?? '—'} {settings?.app_version ?? ''}</dd></div>
              <div className="flex justify-between gap-4"><dt className="text-gray-500">Debug mode</dt><dd className="font-mono text-gray-200">{settings ? String(settings.debug_mode) : '—'}</dd></div>
              <div><dt className="text-gray-500">Configured model path</dt><dd className="mt-1 break-all font-mono text-gray-200">{settings?.ov_model_path ?? '—'}</dd></div>
              <p className="border-t border-border-default pt-3 text-gray-400">Runtime settings are read from the backend environment. Change them in the services configuration and restart the backend.</p>
            </dl>
          </div>
          <div className="rounded-2xl border border-border-default bg-surface-secondary p-5">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-bold text-gray-100"><Shield size={17} className="text-border-active" />Active project scope</h2>
            {activeProjectId && activeProject ? <><p className="text-sm font-semibold text-gray-200">{activeProject.name}</p><p className="mt-2 whitespace-pre-wrap font-mono text-xs text-gray-400">{activeProject.scope}</p>{activeProject.out_of_scope && <p className="mt-3 text-xs text-gray-500">Excluded: <span className="font-mono text-gray-300">{activeProject.out_of_scope}</span></p>}</> : <p className="text-sm text-gray-400">Select a project in the top bar to see its scope.</p>}
            <p className="mt-4 border-t border-border-default pt-3 text-xs text-gray-500">Scope is used to guard active Nmap scans. Keep it limited to assets you are authorized to assess.</p>
          </div>
        </section>
      </div>
    </div>
  );
}

import { useState } from 'react';
import { FileText, Download, Play, CheckCircle2, Cpu, Loader2, AlertTriangle, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useReports } from '../../hooks/useReports';
import { cn } from '../../lib/utils';
import { useProjectStore } from '../../stores/projectStore';

export function ReportsDashboard() {
  const { reportMarkdown, generateReport, isGenerating, error, downloadReport } = useReports();
  const activeProjectId = useProjectStore(state => state.activeProjectId);

  // AI summary is now a real, interactive toggle.
  // The backend falls back to a statistics-based summary when the OpenVINO
  // model is not loaded — so it always produces useful output.
  const [includeAiSummary, setIncludeAiSummary] = useState(false);

  const handleGenerate = async () => {
    try {
      await generateReport({ includeAiSummary });
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex flex-col h-full bg-surface-primary overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border-default bg-surface-secondary flex-shrink-0">
        <div>
          <h1 className="text-xl font-bold text-gray-100 flex items-center gap-2">
            <FileText className="text-border-active" />
            Automated Reporting
          </h1>
          <p className="text-sm text-gray-400 mt-1">Generate a Markdown report from the selected project's stored findings and scope.</p>
        </div>

        {reportMarkdown && (
          <button
            onClick={downloadReport}
            className="flex items-center gap-2 px-4 py-2 bg-border-active text-white rounded-lg font-semibold text-sm hover:bg-blue-600 transition-colors shadow-lg shadow-blue-500/20"
          >
            <Download size={16} />
            Download Markdown
          </button>
        )}
      </div>

      {error && <div className="mx-4 mt-3 rounded-lg border border-severity-critical/30 bg-severity-critical/10 p-3 text-xs text-severity-critical">{error instanceof Error ? error.message : 'Report generation failed.'}</div>}
      <div className="flex-1 overflow-hidden flex flex-col md:flex-row">

        {/* Settings Panel (Left) */}
        <div className="w-full md:w-80 border-r border-border-default bg-surface-secondary p-6 flex flex-col gap-6 overflow-y-auto">

          <div className="space-y-4">
            <h3 className="font-semibold text-gray-200">Report Settings</h3>

            <div className="p-4 border border-border-default rounded-lg bg-surface-primary space-y-3">
              {/* Always-on: Technical Findings */}
              <label className="flex items-start gap-3 cursor-default">
                <div className="relative flex items-start">
                  <input
                    type="checkbox"
                    checked={true}
                    disabled
                    className="peer sr-only"
                  />
                  <div className="w-5 h-5 border-2 border-border-active bg-border-active rounded flex items-center justify-center">
                    <CheckCircle2 size={14} className="text-white" />
                  </div>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-200">Include Technical Findings</span>
                  <p className="text-xs text-gray-500 mt-0.5">Aggregates all vulnerabilities and their severity.</p>
                </div>
              </label>

              {/* Always-on: Project Scope */}
              <label className="flex items-start gap-3 cursor-default">
                <div className="relative flex items-start">
                  <input
                    type="checkbox"
                    checked={true}
                    disabled
                    className="peer sr-only"
                  />
                  <div className="w-5 h-5 border-2 border-border-active bg-border-active rounded flex items-center justify-center">
                    <CheckCircle2 size={14} className="text-white" />
                  </div>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-200">Project Scope Definition</span>
                  <p className="text-xs text-gray-500 mt-0.5">Includes defined in-scope and out-of-scope parameters.</p>
                </div>
              </label>

              {/* Interactive: AI Executive Summary */}
              <div className="border-t border-border-default pt-3 mt-3">
                <label
                  className="flex items-start gap-3 cursor-pointer group"
                  htmlFor="ai-summary-toggle"
                >
                  <div className="relative flex items-start mt-0.5">
                    <input
                      id="ai-summary-toggle"
                      type="checkbox"
                      checked={includeAiSummary}
                      onChange={(e) => setIncludeAiSummary(e.target.checked)}
                      className="peer sr-only"
                    />
                    <div
                      className={cn(
                        "w-5 h-5 border-2 rounded transition-all duration-150 flex items-center justify-center",
                        includeAiSummary
                          ? "border-purple-500 bg-purple-500"
                          : "border-gray-600 bg-surface-tertiary group-hover:border-purple-400"
                      )}
                    >
                      {includeAiSummary && <CheckCircle2 size={14} className="text-white" />}
                    </div>
                  </div>
                  <div>
                    <span className="text-sm font-medium text-gray-200 flex items-center gap-1.5">
                      <Sparkles size={14} className="text-purple-400" />
                      AI Executive Summary
                    </span>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Uses the local HELIOS AI to generate an executive narrative.
                      Falls back to a statistics summary if the model is not loaded.
                    </p>
                  </div>
                </label>

                {/* Inline status pill */}
                {includeAiSummary && (
                  <div className="mt-2 ml-8 flex items-center gap-1.5 text-xs text-purple-400">
                    <Cpu size={11} />
                    <span>AI summary will be included in the report</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          <button
            id="generate-report-btn"
            onClick={handleGenerate}
            disabled={isGenerating || !activeProjectId}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-white text-black rounded-lg font-bold text-sm hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            {isGenerating ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
            {isGenerating ? 'Generating...' : 'Generate Report'}
          </button>

          {error && (
            <div className="p-3 bg-severity-critical/10 border border-severity-critical/30 rounded-lg flex items-start gap-2 text-severity-critical text-sm">
              <AlertTriangle size={16} className="shrink-0 mt-0.5" />
              <span>{error.message}</span>
            </div>
          )}
        </div>

        {/* Live Preview Panel (Right) */}
        <div className="flex-1 bg-surface-primary overflow-y-auto p-8 relative">
          {isGenerating ? (
            <div className="absolute inset-0 bg-surface-primary/50  flex flex-col items-center justify-center z-10 animate-in fade-in">
              <Loader2 className="animate-spin text-border-active mb-4" size={48} />
              <h2 className="text-xl font-bold text-gray-200 mb-2">Generating Report</h2>
              <p className="text-sm text-gray-400 max-w-sm text-center">
                {includeAiSummary
                  ? 'Compiling findings and running AI inference for the executive summary...'
                  : 'Compiling findings, assessing risk factors, and structuring the Markdown output...'}
              </p>
            </div>
          ) : null}

          {reportMarkdown ? (
            <div className="max-w-4xl mx-auto bg-surface-secondary border border-border-default rounded-xl p-8 shadow-lg">
               <div className="prose prose-invert prose-blue max-w-none prose-headings:border-b prose-headings:border-border-default prose-headings:pb-2 prose-h1:text-3xl prose-a:text-border-active">
                  <ReactMarkdown>{reportMarkdown}</ReactMarkdown>
               </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-gray-500">
              <FileText size={64} className="mb-4 opacity-30 text-gray-400" />
              <h3 className="text-2xl font-semibold text-gray-300 mb-2">No Report Generated</h3>
              <p className="text-sm text-center max-w-md text-gray-500">
                Configure your settings in the left panel and click Generate to preview your final pentest report.
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

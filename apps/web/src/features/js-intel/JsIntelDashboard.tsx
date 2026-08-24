import { useState, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { Upload, Search, Link2, KeyRound, Code2, Loader2 } from 'lucide-react';
import { useJsIntel } from '../../hooks/useJsIntel';
import { cn } from '../../lib/utils';

export function JsIntelDashboard() {
  const { analysisResult, analyzeFile, isAnalyzing, error } = useJsIntel();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await handleFileUpload(e.target.files[0]);
    }
  };

  const handleFileUpload = async (file: File) => {
    try {
      await analyzeFile(file);
      if (fileInputRef.current) fileInputRef.current.value = '';
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
            <Code2 className="text-border-active" />
            JavaScript Intelligence
          </h1>
          <p className="text-sm text-gray-400 mt-1">Statically analyze minified frontend bundles to extract hidden API endpoints and secrets.</p>
        </div>
      </div>

      <div className="flex-1 overflow-hidden flex flex-col xl:flex-row">
        
        {/* Left Panel: Upload or Editor */}
        <div className="w-full xl:w-2/3 border-r border-border-default flex flex-col">
          {!analysisResult && !isAnalyzing ? (
            <div className="flex-1 p-8 flex flex-col items-center justify-center">
              <div 
                className={cn(
                  "w-full max-w-xl border-2 border-dashed rounded-xl p-12 flex flex-col items-center justify-center text-center cursor-pointer transition-colors h-64",
                  dragActive ? "border-border-active bg-border-active/10" : "border-border-default hover:border-gray-500 hover:bg-surface-hover"
                )}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  type="file"
                  className="hidden"
                  ref={fileInputRef}
                  accept=".js"
                  onChange={handleFileSelect}
                />
                <Upload size={48} className="text-gray-400 mb-4 opacity-50" />
                <h3 className="text-xl font-semibold text-gray-200 mb-2">Upload JS Bundle</h3>
                <p className="text-sm text-gray-400">Drag and drop a .js file here, or click to browse.</p>
              </div>
              
              {error && (
                <div className="mt-6 p-4 bg-severity-critical/10 border border-severity-critical/30 rounded-lg text-severity-critical max-w-xl w-full text-center">
                  {error.message}
                </div>
              )}
            </div>
          ) : isAnalyzing ? (
             <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
               <Loader2 className="animate-spin mb-4 text-border-active" size={48} />
               <p className="text-lg">Deobfuscating and analyzing JavaScript...</p>
             </div>
          ) : (
            <>
              <div className="p-2 bg-surface-secondary border-b border-border-default text-xs text-gray-400 font-bold uppercase tracking-wider flex items-center gap-2">
                <Search size={14} /> Beautified Source Code
              </div>
              <div className="flex-1 relative">
                <Editor
                  height="100%"
                  defaultLanguage="javascript"
                  theme="vs-dark"
                  value={analysisResult?.beautified_code || ''}
                  options={{
                    readOnly: true,
                    minimap: { enabled: true },
                    fontSize: 13,
                    wordWrap: 'on',
                    scrollBeyondLastLine: false,
                  }}
                />
              </div>
            </>
          )}
        </div>

        {/* Right Panel: Findings Data */}
        <div className="w-full xl:w-1/3 bg-surface-secondary flex flex-col overflow-hidden">
          {analysisResult ? (
            <div className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar">
              
              {/* Tokens Table */}
              <div className="bg-surface-primary border border-border-default rounded-xl overflow-hidden shadow-sm">
                <div className="px-4 py-3 border-b border-border-default bg-surface-tertiary flex items-center gap-2">
                  <KeyRound size={16} className="text-severity-critical" />
                  <h3 className="font-semibold text-gray-200">Extracted Secrets & Tokens</h3>
                  <span className="ml-auto bg-surface-secondary text-gray-300 text-xs px-2 py-0.5 rounded border border-border-default">
                    {analysisResult.findings.tokens.length}
                  </span>
                </div>
                
                {analysisResult.findings.tokens.length > 0 ? (
                  <div className="divide-y divide-border-default">
                    {analysisResult.findings.tokens.map((token, idx) => (
                      <div key={idx} className="p-3 hover:bg-surface-hover transition-colors">
                        <div className="text-xs font-bold text-severity-critical mb-1 uppercase">{token.type}</div>
                        <code className="text-sm text-gray-300 break-all">{token.value}</code>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center text-gray-500 text-sm">No secrets detected.</div>
                )}
              </div>

              {/* Endpoints Table */}
              <div className="bg-surface-primary border border-border-default rounded-xl overflow-hidden shadow-sm">
                <div className="px-4 py-3 border-b border-border-default bg-surface-tertiary flex items-center gap-2">
                  <Link2 size={16} className="text-severity-info" />
                  <h3 className="font-semibold text-gray-200">Discovered Endpoints</h3>
                  <span className="ml-auto bg-surface-secondary text-gray-300 text-xs px-2 py-0.5 rounded border border-border-default">
                    {analysisResult.findings.endpoints.length}
                  </span>
                </div>
                
                {analysisResult.findings.endpoints.length > 0 ? (
                  <div className="divide-y divide-border-default">
                    {analysisResult.findings.endpoints.map((ep, idx) => (
                      <div key={idx} className="p-3 hover:bg-surface-hover transition-colors">
                        <code className="text-sm text-severity-info break-all block">{ep}</code>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-8 text-center text-gray-500 text-sm">No endpoints detected.</div>
                )}
              </div>

            </div>
          ) : (
             <div className="flex-1 flex flex-col items-center justify-center text-gray-500 p-8 text-center">
                <Search size={48} className="mb-4 opacity-30 text-gray-400" />
                <h3 className="text-xl font-semibold text-gray-300 mb-2">Awaiting Analysis</h3>
                <p className="text-sm text-gray-500">
                  Upload a JS bundle to see extracted endpoints, URLs, and potential secrets.
                </p>
             </div>
          )}
        </div>

      </div>
    </div>
  );
}

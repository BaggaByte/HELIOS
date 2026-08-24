import React, { useState, useEffect, useRef } from 'react';
import { Code2, FileCode2, Terminal, ShieldAlert, Activity, GitCommit, FileText, Settings, Upload } from 'lucide-react';
import { useSourceCodeStore } from '../../stores/sourceCodeStore';
import { cn } from '../../lib/utils';
import type { CodeFinding } from '../../services/sourceCodeService';

export function SourceCodeDashboard() {
  const { analyzedFiles, selectedFileId, isLoading, fetchAnalyzedFiles, selectFile } = useSourceCodeStore();
  const [activeTab, setActiveTab] = useState<'code' | 'findings'>('findings');

  useEffect(() => {
    fetchAnalyzedFiles('default-project-id');
  }, [fetchAnalyzedFiles]);

  const selectedFile = analyzedFiles.find(f => f.id === selectedFileId);

  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'text-severity-critical bg-severity-critical/10 border-severity-critical/30';
      case 'HIGH': return 'text-orange-500 bg-orange-500/10 border-orange-500/30';
      case 'MEDIUM': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30';
      case 'LOW': return 'text-severity-low bg-severity-low/10 border-severity-low/30';
      default: return 'text-severity-info bg-severity-info/10 border-severity-info/30';
    }
  };

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      const extension = file.name.split('.').pop() || '';
      let language = 'unknown';
      if (['py', 'pyw'].includes(extension)) language = 'python';
      else if (['js', 'ts', 'jsx', 'tsx'].includes(extension)) language = 'javascript';
      else if (['java'].includes(extension)) language = 'java';
      else if (['c', 'cpp', 'h', 'hpp'].includes(extension)) language = 'c++';
      
      useSourceCodeStore.getState().analyzeSnippet(content, language, file.name);
    };
    reader.readAsText(file);
    // Reset input so the same file can be uploaded again if needed
    event.target.value = '';
  };

  return (
    <div className="flex flex-col h-full p-8 overflow-hidden relative bg-transparent">
      
      {/* Dashboard Header */}
      <div className="flex items-center justify-between mb-8 z-10 flex-shrink-0">
        <div>
          <h1 className="text-3xl font-bold text-gray-100 neon-text flex items-center gap-3">
            <Code2 className="text-border-active" size={32} />
            Source Code Analysis
          </h1>
          <p className="text-gray-400 mt-2">Static analysis and AST intelligence mapping.</p>
        </div>
        <div>
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileUpload} 
            className="hidden" 
            accept=".py,.js,.ts,.java,.c,.cpp" 
          />
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="px-4 py-2 rounded-lg bg-border-active/10 text-border-active border border-border-active/50 hover:bg-border-active hover:text-bg-primary transition-all flex items-center gap-2"
          >
            <Upload size={16} />
            Analyze New File
          </button>
        </div>
      </div>

      {/* Split-Pane Layout */}
      <div className="flex flex-1 gap-6 min-h-0 z-10">
        
        {/* Left Pane: File Explorer */}
        <div className="w-64 flex flex-col flex-shrink-0 glass-panel rounded-2xl border border-border-default/50 overflow-hidden shadow-xl">
          <div className="p-4 border-b border-border-default/50 bg-surface-secondary/40 backdrop-blur">
            <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2 uppercase tracking-wider">
              <Terminal size={16} /> Repository
            </h3>
          </div>
          <div className="flex-1 overflow-y-auto p-2 custom-scrollbar">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Activity size={24} className="text-border-active animate-spin" />
              </div>
            ) : analyzedFiles.length === 0 ? (
              <div className="text-center text-gray-500 py-12">
                <p className="text-sm">No files analyzed.</p>
              </div>
            ) : (
              analyzedFiles.map(file => (
                <button
                  key={file.id}
                  onClick={() => selectFile(file.id)}
                  className={cn(
                    "w-full text-left px-3 py-2.5 rounded-lg flex items-center justify-between gap-3 transition-all text-sm mb-1 group",
                    selectedFileId === file.id
                      ? "bg-border-active/10 text-border-active shadow-[inset_0_0_10px_rgb(var(--border-active)/0.2)]"
                      : "text-gray-400 hover:bg-surface-tertiary hover:text-gray-200"
                  )}
                >
                  <div className="flex items-center gap-2 truncate">
                    <FileCode2 size={16} className={selectedFileId === file.id ? "text-border-active" : "text-gray-500"} />
                    <span className="truncate">{file.filename}</span>
                  </div>
                  {file.security_findings.length > 0 && (
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-severity-critical/20 text-severity-critical border border-severity-critical/30">
                      {file.security_findings.length}
                    </span>
                  )}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Right Pane: Code & Findings Viewer */}
        <div className="flex-1 flex flex-col min-w-0 glass-panel rounded-2xl border border-border-default/50 overflow-hidden shadow-xl">
          {selectedFile ? (
            <>
              {/* Tab Bar */}
              <div className="flex bg-surface-secondary/40 border-b border-border-default/50 backdrop-blur">
                <button
                  onClick={() => setActiveTab('findings')}
                  className={cn(
                    "px-6 py-3 text-sm font-medium transition-all flex items-center gap-2 border-b-2",
                    activeTab === 'findings' 
                      ? "text-border-active border-border-active bg-border-active/5" 
                      : "text-gray-400 border-transparent hover:text-gray-200 hover:bg-surface-tertiary/50"
                  )}
                >
                  <ShieldAlert size={16} /> Security Findings ({selectedFile.security_findings.length})
                </button>
                <button
                  onClick={() => setActiveTab('code')}
                  className={cn(
                    "px-6 py-3 text-sm font-medium transition-all flex items-center gap-2 border-b-2",
                    activeTab === 'code' 
                      ? "text-border-active border-border-active bg-border-active/5" 
                      : "text-gray-400 border-transparent hover:text-gray-200 hover:bg-surface-tertiary/50"
                  )}
                >
                  <FileText size={16} /> Source Code
                </button>
              </div>

              {/* Content Area */}
              <div className="flex-1 overflow-hidden relative bg-[#0d1117]/60">
                {activeTab === 'findings' ? (
                  <div className="h-full overflow-y-auto p-6 custom-scrollbar">
                    {/* File Meta Info */}
                    <div className="grid grid-cols-3 gap-4 mb-8">
                      <div className="glass-panel p-4 rounded-xl border border-border-default/50">
                        <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Language</div>
                        <div className="font-mono text-gray-200">{selectedFile.language}</div>
                      </div>
                      <div className="glass-panel p-4 rounded-xl border border-border-default/50">
                        <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Classes Discovered</div>
                        <div className="font-mono text-gray-200">{selectedFile.classes.length}</div>
                      </div>
                      <div className="glass-panel p-4 rounded-xl border border-border-default/50">
                        <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Functions Discovered</div>
                        <div className="font-mono text-gray-200">{selectedFile.functions.length}</div>
                      </div>
                    </div>

                    <h3 className="text-lg font-bold text-gray-200 mb-4 flex items-center gap-2">
                      <ShieldAlert className="text-severity-critical" /> Static Analysis Findings
                    </h3>
                    
                    {selectedFile.security_findings.length === 0 ? (
                      <div className="p-8 text-center text-gray-500 border border-dashed border-border-default rounded-xl">
                        No security findings detected by static analysis.
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {selectedFile.security_findings.map((finding, idx) => (
                          <div key={idx} className="glass-panel p-4 rounded-xl border border-border-default/50 flex gap-4 items-start">
                            <div className={cn("px-2 py-1 rounded text-xs font-bold border uppercase tracking-wider mt-0.5", getSeverityStyle(finding.severity))}>
                              {finding.severity}
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="text-sm font-semibold text-gray-200">{finding.description}</h4>
                              <div className="flex items-center gap-2 mt-2 text-xs text-gray-400 font-mono">
                                <GitCommit size={14} /> Line: <span className="text-border-active">{finding.line}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="h-full overflow-y-auto p-4 custom-scrollbar">
                    <pre className="text-sm font-mono text-gray-300">
                      <code>
                        {selectedFile.code.split('\n').map((line, i) => {
                          const lineNumber = i + 1;
                          const hasFinding = selectedFile.security_findings.some(f => f.line === lineNumber);
                          
                          return (
                            <div 
                              key={i} 
                              className={cn(
                                "flex px-4 py-0.5 hover:bg-surface-tertiary/50 transition-colors group",
                                hasFinding && "bg-severity-critical/10 hover:bg-severity-critical/20"
                              )}
                            >
                              <span className="w-12 text-right pr-4 text-gray-600 select-none group-hover:text-gray-400">
                                {lineNumber}
                              </span>
                              <span className={hasFinding ? "text-red-400 font-bold relative" : ""}>
                                {line || ' '}
                                {hasFinding && (
                                  <div className="absolute left-full ml-4 whitespace-nowrap text-xs bg-severity-critical text-white px-2 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity z-10">
                                    VULNERABILITY DETECTED
                                  </div>
                                )}
                              </span>
                            </div>
                          );
                        })}
                      </code>
                    </pre>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 p-8 text-center bg-surface-primary/20">
              <Code2 size={64} className="mb-4 opacity-20" />
              <h3 className="text-xl font-medium text-gray-400 mb-2">Select a File</h3>
              <p>Choose a file from the repository explorer to view its source code and static analysis intelligence.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

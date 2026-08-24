import { useState } from 'react';
import {
  Settings as SettingsIcon,
  Cpu,
  Terminal,
  Shield,
  Key,
  Database,
  Save,
  Check,
  RefreshCw,
  Lock,
  Download
} from 'lucide-react';
import { cn } from '../../lib/utils';

export function SettingsDashboard() {
  const [activeTab, setActiveTab] = useState<'ai' | 'tools' | 'intel' | 'scope' | 'vault'>('ai');
  const [savedSuccess, setSavedSuccess] = useState(false);

  // AI Configuration State
  const [aiProvider, setAiProvider] = useState('openvino');
  const [modelName, setModelName] = useState('Qwen/Qwen2.5-Coder-7B-Instruct');
  const [deviceTarget, setDeviceTarget] = useState('NPU');
  const [contextWindow, setContextWindow] = useState(16384);
  const [temperature, setTemperature] = useState(0.2);
  const [topP, setTopP] = useState(0.9);
  const [embeddingModel, setEmbeddingModel] = useState('BAAI/bge-large-en-v1.5');

  // Tool integration status
  const [tools] = useState([
    { name: 'Nmap Port Scanner', path: '/usr/bin/nmap', version: '7.94SVN', status: 'ready' },
    { name: 'Masscan High-Speed SYN', path: '/usr/local/bin/masscan', version: '1.3.2', status: 'ready' },
    { name: 'FFuF Web Fuzzer', path: '/usr/bin/ffuf', version: '2.1.0-dev', status: 'ready' },
    { name: 'Nuclei Vulnerability Engine', path: '/usr/local/bin/nuclei', version: 'v3.2.0', status: 'ready' },
    { name: 'Katana Web Crawler', path: '/usr/bin/katana', version: 'v1.0.5', status: 'ready' },
    { name: 'Subfinder Subdomain OSINT', path: '/usr/bin/subfinder', version: 'v2.6.4', status: 'ready' },
    { name: 'YARA Pattern Matcher', path: '/usr/bin/yara', version: '4.3.2', status: 'ready' },
    { name: 'Ghidra Headless Decompiler', path: '/opt/ghidra/support/analyzeHeadless', version: '11.0.1', status: 'ready' },
    { name: 'OWASP ZAP Daemon Bridge', path: 'http://127.0.0.1:8080', version: '2.14.0', status: 'connected' }
  ]);

  // Threat Intel Keys
  const [vtApiKey, setVtApiKey] = useState('vt_live_948f98a287c91823...');
  const [shodanApiKey, setShodanApiKey] = useState('sh_87ba190287dfa19b8...');
  const [otxApiKey, setOtxApiKey] = useState('otx_981a87db73619283...');
  const [greyNoiseApiKey, setGreyNoiseApiKey] = useState('');

  // Scope & Rules of Engagement
  const [inScopeCidr, setInScopeCidr] = useState('192.168.1.0/24\n10.0.0.0/16\napi.helios.corp\nauth.helios.corp');
  const [blacklistScope, setBlacklistScope] = useState('192.168.1.1 (Gateway)\n10.0.0.1 (Domain Controller)\n*.mil\n*.gov');
  const [stealthMode, setStealthMode] = useState(true);

  const handleSave = () => {
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  return (
    <div className="flex flex-col h-full bg-surface-primary overflow-hidden">
      
      {/* Header */}
      <div className="p-4 border-b border-border-default bg-surface-secondary flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-surface-tertiary border border-border-default text-gray-200">
            <SettingsIcon size={20} className="text-border-active" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-100">System Settings & Engine Config</h1>
            <p className="text-xs text-gray-400">Configure local AI copilot runtime, binary security tools, API feeds, and scope guard.</p>
          </div>
        </div>

        <button
          onClick={handleSave}
          className="px-4 py-2 rounded-lg bg-border-active text-white text-xs font-bold hover:bg-opacity-90 transition-all flex items-center gap-2 shadow-sm"
        >
          {savedSuccess ? <Check size={14} className="text-emerald-300" /> : <Save size={14} />}
          <span>{savedSuccess ? 'Configuration Saved!' : 'Save Changes'}</span>
        </button>
      </div>

      {/* Tabs Layout */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        
        {/* Navigation Sidebar */}
        <div className="w-full md:w-64 border-b md:border-b-0 md:border-r border-border-default bg-surface-secondary/40 p-3 space-y-1 flex-shrink-0 overflow-y-auto custom-scrollbar">
          <button
            onClick={() => setActiveTab('ai')}
            className={cn(
              "w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs font-semibold text-left transition-all",
              activeTab === 'ai' ? "bg-border-active text-white shadow-xs" : "text-gray-400 hover:bg-surface-tertiary hover:text-gray-200"
            )}
          >
            <Cpu size={16} />
            <span>AI Inference Engine</span>
          </button>

          <button
            onClick={() => setActiveTab('tools')}
            className={cn(
              "w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs font-semibold text-left transition-all",
              activeTab === 'tools' ? "bg-border-active text-white shadow-xs" : "text-gray-400 hover:bg-surface-tertiary hover:text-gray-200"
            )}
          >
            <Terminal size={16} />
            <span>Tool Integrations</span>
          </button>

          <button
            onClick={() => setActiveTab('intel')}
            className={cn(
              "w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs font-semibold text-left transition-all",
              activeTab === 'intel' ? "bg-border-active text-white shadow-xs" : "text-gray-400 hover:bg-surface-tertiary hover:text-gray-200"
            )}
          >
            <Key size={16} />
            <span>Threat Intel API Keys</span>
          </button>

          <button
            onClick={() => setActiveTab('scope')}
            className={cn(
              "w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs font-semibold text-left transition-all",
              activeTab === 'scope' ? "bg-border-active text-white shadow-xs" : "text-gray-400 hover:bg-surface-tertiary hover:text-gray-200"
            )}
          >
            <Shield size={16} />
            <span>Scope Guard & RoE</span>
          </button>

          <button
            onClick={() => setActiveTab('vault')}
            className={cn(
              "w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs font-semibold text-left transition-all",
              activeTab === 'vault' ? "bg-border-active text-white shadow-xs" : "text-gray-400 hover:bg-surface-tertiary hover:text-gray-200"
            )}
          >
            <Database size={16} />
            <span>Security Vault & Storage</span>
          </button>
        </div>

        {/* Tab Detail Pane */}
        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-surface-primary">
          
          {/* TAB 1: AI Engine */}
          {activeTab === 'ai' && (
            <div className="max-w-3xl space-y-6 animate-in fade-in duration-150">
              <div className="pb-4 border-b border-border-default">
                <h2 className="text-base font-bold text-gray-100 flex items-center gap-2">
                  <Cpu size={18} className="text-border-active" />
                  Local AI Copilot Runtime (OpenVINO / ONNX)
                </h2>
                <p className="text-xs text-gray-400 mt-1">Configure hardware-accelerated local neural execution for real-time security reasoning.</p>
              </div>

              <div className="space-y-4 text-xs">
                <div>
                  <label className="font-bold text-gray-300 block mb-1.5">Runtime Architecture</label>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {['openvino', 'onnx', 'gemini'].map((provider) => (
                      <button
                        key={provider}
                        type="button"
                        onClick={() => setAiProvider(provider)}
                        className={cn(
                          "p-3 rounded-xl border text-left transition-all",
                          aiProvider === provider 
                            ? "bg-border-active/15 border-border-active text-gray-100 font-bold" 
                            : "bg-surface-secondary border-border-default text-gray-400 hover:bg-surface-tertiary"
                        )}
                      >
                        <span className="capitalize block">{provider === 'openvino' ? 'Intel OpenVINO' : provider === 'onnx' ? 'ONNX Runtime' : 'Google Gemini Pro API'}</span>
                        <span className="text-[10px] text-gray-500 font-normal">
                          {provider === 'openvino' ? 'Optimized for Intel NPU / Arc GPU' : provider === 'onnx' ? 'Universal DirectML acceleration' : 'Cloud server-side inference'}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="font-bold text-gray-300 block mb-1.5">Local LLM Model</label>
                    <select
                      value={modelName}
                      onChange={(e) => setModelName(e.target.value)}
                      className="w-full bg-surface-secondary border border-border-default rounded-xl p-2.5 text-xs text-gray-200 font-mono focus:border-border-active outline-none"
                    >
                      <option value="Qwen/Qwen2.5-Coder-7B-Instruct">Qwen2.5-Coder-7B-Instruct (INT4)</option>
                      <option value="DeepSeek-R1-Distill-Qwen-8B">DeepSeek-R1-Distill-Qwen-8B</option>
                      <option value="Mistral-7B-Instruct-v0.3">Mistral-7B-Instruct-v0.3 (FP16)</option>
                      <option value="Meta-Llama-3.1-8B-Instruct">Meta-Llama-3.1-8B-Instruct</option>
                    </select>
                  </div>

                  <div>
                    <label className="font-bold text-gray-300 block mb-1.5">Hardware Accelerator Target</label>
                    <select
                      value={deviceTarget}
                      onChange={(e) => setDeviceTarget(e.target.value)}
                      className="w-full bg-surface-secondary border border-border-default rounded-xl p-2.5 text-xs text-gray-200 font-mono focus:border-border-active outline-none"
                    >
                      <option value="NPU">Intel NPU (Neural Processing Unit)</option>
                      <option value="GPU">Intel Arc / Iris Xe GPU</option>
                      <option value="CPU">Host CPU (AVX-512 VNNI / AMX)</option>
                      <option value="AUTO">AUTO (Dynamic Scheduling)</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between">
                    <label className="font-bold text-gray-300">Context Window Size</label>
                    <span className="font-mono text-border-active font-bold">{contextWindow.toLocaleString()} tokens</span>
                  </div>
                  <input
                    type="range"
                    min={4096}
                    max={32768}
                    step={2048}
                    value={contextWindow}
                    onChange={(e) => setContextWindow(Number(e.target.value))}
                    className="w-full accent-border-active"
                  />
                  <div className="flex justify-between text-[10px] text-gray-500 font-mono">
                    <span>4K (Low RAM)</span>
                    <span>16K (Balanced)</span>
                    <span>32K (Full Codebase)</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-2">
                  <div>
                    <label className="font-bold text-gray-300 block mb-1">Temperature ({temperature})</label>
                    <input
                      type="range"
                      min={0.0}
                      max={1.0}
                      step={0.05}
                      value={temperature}
                      onChange={(e) => setTemperature(Number(e.target.value))}
                      className="w-full accent-border-active"
                    />
                  </div>
                  <div>
                    <label className="font-bold text-gray-300 block mb-1">Top-P Sampling ({topP})</label>
                    <input
                      type="range"
                      min={0.1}
                      max={1.0}
                      step={0.05}
                      value={topP}
                      onChange={(e) => setTopP(Number(e.target.value))}
                      className="w-full accent-border-active"
                    />
                  </div>
                </div>

                <div>
                  <label className="font-bold text-gray-300 block mb-1.5">Vector Memory Embedding Model</label>
                  <input
                    type="text"
                    value={embeddingModel}
                    onChange={(e) => setEmbeddingModel(e.target.value)}
                    className="w-full bg-surface-secondary border border-border-default rounded-xl p-2.5 text-xs text-gray-200 font-mono focus:border-border-active outline-none"
                  />
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: Tool Integrations */}
          {activeTab === 'tools' && (
            <div className="max-w-3xl space-y-6 animate-in fade-in duration-150">
              <div className="pb-4 border-b border-border-default flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-gray-100 flex items-center gap-2">
                    <Terminal size={18} className="text-border-active" />
                    Offensive Security Tool Wrappers
                  </h2>
                  <p className="text-xs text-gray-400 mt-1">Binary executable paths, daemons, and automated wrappers registered in HELIOS.</p>
                </div>
                <button
                  onClick={() => handleSave()}
                  className="px-3 py-1.5 rounded-lg bg-surface-secondary hover:bg-surface-tertiary border border-border-default text-xs text-gray-200 flex items-center gap-1.5 transition-colors"
                >
                  <RefreshCw size={12} />
                  <span>Probe Binaries</span>
                </button>
              </div>

              <div className="space-y-2.5">
                {tools.map((tool, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-surface-secondary border border-border-default flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-gray-200">{tool.name}</span>
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-tertiary text-gray-400 border border-border-default">
                          {tool.version}
                        </span>
                      </div>
                      <div className="font-mono text-[11px] text-gray-500 mt-0.5">{tool.path}</div>
                    </div>

                    <div className="flex items-center gap-2 self-start sm:self-center">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        READY
                      </span>
                      <button className="px-2 py-1 rounded bg-surface-tertiary hover:bg-surface-hover text-gray-300 border border-border-default text-[11px]">
                        Test Run
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: Threat Intel */}
          {activeTab === 'intel' && (
            <div className="max-w-3xl space-y-6 animate-in fade-in duration-150">
              <div className="pb-4 border-b border-border-default">
                <h2 className="text-base font-bold text-gray-100 flex items-center gap-2">
                  <Key size={18} className="text-border-active" />
                  Threat Intelligence & OSINT API Keys
                </h2>
                <p className="text-xs text-gray-400 mt-1">Configure external intelligence feeds for automated IP, domain, hash, and CVE correlation.</p>
              </div>

              <div className="space-y-4 text-xs">
                <div>
                  <label className="font-bold text-gray-300 block mb-1">VirusTotal v3 API Key</label>
                  <div className="flex gap-2">
                    <input
                      type="password"
                      value={vtApiKey}
                      onChange={(e) => setVtApiKey(e.target.value)}
                      className="flex-1 bg-surface-secondary border border-border-default rounded-xl p-2.5 text-xs font-mono text-gray-200 focus:border-border-active outline-none"
                    />
                    <button className="px-3 py-2 rounded-xl bg-surface-secondary hover:bg-surface-tertiary border border-border-default text-gray-300 font-medium">
                      Verify
                    </button>
                  </div>
                </div>

                <div>
                  <label className="font-bold text-gray-300 block mb-1">Shodan API Key</label>
                  <div className="flex gap-2">
                    <input
                      type="password"
                      value={shodanApiKey}
                      onChange={(e) => setShodanApiKey(e.target.value)}
                      className="flex-1 bg-surface-secondary border border-border-default rounded-xl p-2.5 text-xs font-mono text-gray-200 focus:border-border-active outline-none"
                    />
                    <button className="px-3 py-2 rounded-xl bg-surface-secondary hover:bg-surface-tertiary border border-border-default text-gray-300 font-medium">
                      Verify
                    </button>
                  </div>
                </div>

                <div>
                  <label className="font-bold text-gray-300 block mb-1">AlienVault OTX API Key</label>
                  <div className="flex gap-2">
                    <input
                      type="password"
                      value={otxApiKey}
                      onChange={(e) => setOtxApiKey(e.target.value)}
                      className="flex-1 bg-surface-secondary border border-border-default rounded-xl p-2.5 text-xs font-mono text-gray-200 focus:border-border-active outline-none"
                    />
                    <button className="px-3 py-2 rounded-xl bg-surface-secondary hover:bg-surface-tertiary border border-border-default text-gray-300 font-medium">
                      Verify
                    </button>
                  </div>
                </div>

                <div>
                  <label className="font-bold text-gray-300 block mb-1">GreyNoise Enterprise Key</label>
                  <div className="flex gap-2">
                    <input
                      type="password"
                      value={greyNoiseApiKey}
                      onChange={(e) => setGreyNoiseApiKey(e.target.value)}
                      placeholder="Optional API key..."
                      className="flex-1 bg-surface-secondary border border-border-default rounded-xl p-2.5 text-xs font-mono text-gray-200 focus:border-border-active outline-none"
                    />
                    <button className="px-3 py-2 rounded-xl bg-surface-secondary hover:bg-surface-tertiary border border-border-default text-gray-300 font-medium">
                      Verify
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: Scope Guard */}
          {activeTab === 'scope' && (
            <div className="max-w-3xl space-y-6 animate-in fade-in duration-150">
              <div className="pb-4 border-b border-border-default">
                <h2 className="text-base font-bold text-gray-100 flex items-center gap-2">
                  <Shield size={18} className="text-border-active" />
                  Scope Guard & Rules of Engagement (RoE)
                </h2>
                <p className="text-xs text-gray-400 mt-1">Enforce strict operational boundaries to prevent scanning out-of-scope infrastructure.</p>
              </div>

              <div className="space-y-4 text-xs">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="font-bold text-emerald-400 block mb-1.5">Authorized In-Scope Targets (1 per line)</label>
                    <textarea
                      value={inScopeCidr}
                      onChange={(e) => setInScopeCidr(e.target.value)}
                      rows={6}
                      className="w-full bg-[#0b0e14] border border-border-default rounded-xl p-3 text-xs font-mono text-emerald-300 focus:border-border-active outline-none resize-none leading-relaxed"
                    />
                  </div>

                  <div>
                    <label className="font-bold text-severity-critical block mb-1.5">Hard Blacklist / Out of Scope (Never Scan)</label>
                    <textarea
                      value={blacklistScope}
                      onChange={(e) => setBlacklistScope(e.target.value)}
                      rows={6}
                      className="w-full bg-[#0b0e14] border border-border-default rounded-xl p-3 text-xs font-mono text-severity-critical focus:border-border-active outline-none resize-none leading-relaxed"
                    />
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-surface-secondary border border-border-default flex items-center justify-between">
                  <div>
                    <div className="font-bold text-gray-200">Evasion & Stealth Mode</div>
                    <div className="text-gray-400 text-[11px] mt-0.5">Fragment packets, randomize user-agents, and apply jitter delays.</div>
                  </div>
                  <button
                    onClick={() => setStealthMode(!stealthMode)}
                    className={cn(
                      "w-12 h-6 rounded-full transition-colors relative p-0.5",
                      stealthMode ? "bg-border-active" : "bg-surface-tertiary border border-border-default"
                    )}
                  >
                    <div className={cn(
                      "w-5 h-5 rounded-full bg-white transition-transform",
                      stealthMode ? "translate-x-6" : "translate-x-0"
                    )} />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: Security Vault */}
          {activeTab === 'vault' && (
            <div className="max-w-3xl space-y-6 animate-in fade-in duration-150">
              <div className="pb-4 border-b border-border-default">
                <h2 className="text-base font-bold text-gray-100 flex items-center gap-2">
                  <Database size={18} className="text-border-active" />
                  Security Vault & Cryptographic Storage
                </h2>
                <p className="text-xs text-gray-400 mt-1">Manage project encryption keys, vector embeddings, and full workspace exports.</p>
              </div>

              <div className="space-y-4 text-xs">
                <div className="p-4 rounded-xl bg-surface-secondary border border-border-default flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                      <Lock size={20} />
                    </div>
                    <div>
                      <div className="font-bold text-gray-200">AES-256-GCM Vault Status</div>
                      <div className="text-gray-400 font-mono text-[11px]">Hardware-backed key active (PBKDF2 600k iterations)</div>
                    </div>
                  </div>
                  <span className="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                    LOCKED & SECURED
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-surface-secondary border border-border-default flex items-center justify-between">
                  <div>
                    <div className="font-bold text-gray-200">Export Encrypted Project Backup</div>
                    <div className="text-gray-400 text-[11px] mt-0.5">Package all target evidence, knowledge graphs, chat history, and reports.</div>
                  </div>
                  <button className="px-3 py-2 rounded-lg bg-border-active text-white font-semibold text-xs flex items-center gap-1.5 hover:bg-opacity-90 transition-all">
                    <Download size={14} />
                    <span>Download .helios-pack</span>
                  </button>
                </div>
              </div>
            </div>
          )}

        </div>

      </div>

    </div>
  );
}

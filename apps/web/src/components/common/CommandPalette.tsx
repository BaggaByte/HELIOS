import { useState, useEffect, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Target,
  Globe,
  Code2,
  FileText,
  Bug,
  Network,
  Database,
  FileBox,
  Settings,
  MessageSquare,
  Zap,
  Terminal,
  Cpu,
  CornerDownLeft,
  X
} from 'lucide-react';

interface CommandItem {
  id: string;
  title: string;
  category: 'Navigation' | 'Actions' | 'Targets' | 'Vulnerabilities' | 'Intelligence';
  icon: any;
  shortcut?: string;
  action: () => void;
  description?: string;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  const commands: CommandItem[] = useMemo(() => [
    // Navigation
    {
      id: 'nav-dashboard',
      title: 'Go to Mission Control',
      category: 'Navigation',
      icon: Zap,
      action: () => { navigate('/'); onClose(); },
      description: 'View threat posture, engagement status & operations'
    },
    {
      id: 'nav-chat',
      title: 'Open AI Copilot Chat',
      category: 'Navigation',
      icon: MessageSquare,
      action: () => { navigate('/chat'); onClose(); },
      description: 'Interact with local OpenVINO security LLM'
    },
    {
      id: 'nav-recon',
      title: 'Target Reconnaissance & Network Matrix',
      category: 'Navigation',
      icon: Target,
      action: () => { navigate('/recon'); onClose(); },
      description: 'Inspect hosts, open ports, banners & Nmap scans'
    },
    {
      id: 'nav-web',
      title: 'Web Security',
      category: 'Navigation',
      icon: Globe,
      action: () => { navigate('/web'); onClose(); },
      description: 'Review findings or import a ZAP report'
    },
    {
      id: 'nav-code',
      title: 'Source Code & Secret Audit',
      category: 'Navigation',
      icon: Code2,
      action: () => { navigate('/code'); onClose(); },
      description: 'Static application security testing & leaked secrets'
    },
    {
      id: 'nav-logs',
      title: 'SIEM & Log Intelligence',
      category: 'Navigation',
      icon: FileText,
      action: () => { navigate('/logs'); onClose(); },
      description: 'View and filter ingested security logs'
    },
    {
      id: 'nav-malware',
      title: 'Malware Triage & Reverse Engineering',
      category: 'Navigation',
      icon: Bug,
      action: () => { navigate('/malware'); onClose(); },
      description: 'PE section entropy, suspicious IATs & YARA scanning'
    },
    {
      id: 'nav-graph',
      title: 'Knowledge Graph & Attack Paths',
      category: 'Navigation',
      icon: Network,
      action: () => { navigate('/graph'); onClose(); },
      description: 'Graph-based infrastructure and cyber kill chain visualizer'
    },
    {
      id: 'nav-evidence',
      title: 'Evidence Locker',
      category: 'Navigation',
      icon: Database,
      action: () => { navigate('/evidence'); onClose(); },
      description: 'Manage and view stored project evidence'
    },
    {
      id: 'nav-reports',
      title: 'Automated Security Report Studio',
      category: 'Navigation',
      icon: FileBox,
      action: () => { navigate('/reports'); onClose(); },
      description: 'Generate Markdown executive summaries and briefs'
    },
    {
      id: 'nav-settings',
      title: 'System Settings',
      category: 'Navigation',
      icon: Settings,
      action: () => { navigate('/settings'); onClose(); },
      description: 'Configure application settings and preferences'
    },

    // Quick Actions
    {
      id: 'act-new-scan',
      title: 'Open Recon',
      category: 'Actions',
      icon: Target,
      action: () => { navigate('/recon'); onClose(); },
      description: 'Navigate to network reconnaissance tools'
    },

    {
      id: 'act-yara',
      title: 'Open Malware Triage',
      category: 'Actions',
      icon: Terminal,
      action: () => { navigate('/malware'); onClose(); },
      description: 'Navigate to binary analysis and YARA scanning'
    },
    {
      id: 'act-export-report',
      title: 'Open Report Studio',
      category: 'Actions',
      icon: FileBox,
      action: () => { navigate('/reports'); onClose(); },
      description: 'Navigate to Markdown report generator'
    },

    // Targets & Vulnerabilities

    {
      id: 'intel-openvino',
      title: 'AI Engine: Local OpenVINO Phi-4 Runtime',
      category: 'Intelligence',
      icon: Cpu,
      action: () => { navigate('/settings'); onClose(); },
      description: 'Device: Intel NPU/GPU/CPU'
    }
  ], [navigate, onClose]);

  const filteredCommands = useMemo(() => {
    if (!query.trim()) return commands;
    const q = query.toLowerCase();
    return commands.filter(cmd =>
      cmd.title.toLowerCase().includes(q) ||
      cmd.category.toLowerCase().includes(q) ||
      (cmd.description && cmd.description.toLowerCase().includes(q))
    );
  }, [commands, query]);

  const activeIndex = Math.min(selectedIndex, Math.max(0, filteredCommands.length - 1));

  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement as HTMLElement;
      // Focus modal's first focusable element (input)
      setTimeout(() => {
        if (inputRef.current) inputRef.current.focus();
      }, 0);
    } else {
      if (previousFocusRef.current) {
        previousFocusRef.current.focus();
        previousFocusRef.current = null;
      }
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex(prev => (prev + 1) % Math.max(1, filteredCommands.length));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(prev => (prev - 1 + filteredCommands.length) % Math.max(1, filteredCommands.length));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredCommands[activeIndex]) {
          filteredCommands[activeIndex].action();
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      } else if (e.key === 'Tab') {
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
  }, [isOpen, filteredCommands, activeIndex, onClose]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 bg-black/70  flex items-start justify-center pt-20 p-4 animate-in fade-in duration-200" 
      role="dialog" 
      aria-modal="true" 
      aria-label="Command Palette"
      ref={modalRef}
      onClick={onClose}
    >
      <div 
        className="w-full max-w-2xl bg-surface-secondary border border-border-default rounded-2xl shadow-lg overflow-hidden flex flex-col max-h-[80vh] divide-y divide-border-default"
        onClick={e => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3.5 bg-surface-tertiary/40">
          <Search size={20} className="text-border-active mr-3 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder="Type a command to navigate..."
            className="w-full bg-transparent border-none text-gray-100 text-base placeholder-gray-500 focus:outline-none"
          />
          <button 
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-surface-hover text-gray-400 hover:text-gray-200 transition-colors ml-2"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        {/* Command List */}
        <div className="overflow-y-auto p-2 custom-scrollbar max-h-[460px] space-y-1">
          {filteredCommands.length === 0 ? (
            <div className="py-12 text-center text-gray-500 text-sm">
              No matching commands or resources found for &ldquo;{query}&rdquo;
            </div>
          ) : (
            filteredCommands.map((cmd, idx) => {
              const Icon = cmd.icon;
              const isSelected = idx === activeIndex;
              return (
                <button
                  key={cmd.id}
                  onClick={cmd.action}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`w-full flex items-center justify-between p-3 rounded-xl text-left transition-all ${
                    isSelected
                      ? 'bg-border-active/15 border border-border-active/40 text-gray-100'
                      : 'hover:bg-surface-tertiary/60 text-gray-300 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`p-2 rounded-lg shrink-0 ${isSelected ? 'bg-border-active text-white' : 'bg-surface-tertiary text-gray-400'}`}>
                      <Icon size={18} />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold truncate text-gray-100">{cmd.title}</span>
                        <span className="text-xs uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-surface-primary text-gray-400 border border-border-default shrink-0">
                          {cmd.category}
                        </span>
                      </div>
                      {cmd.description && (
                        <p className="text-xs text-gray-400 truncate mt-0.5">{cmd.description}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 ml-3">
                    {cmd.shortcut && (
                      <kbd className="px-2 py-0.5 text-xs font-mono bg-surface-primary text-gray-400 rounded border border-border-default">
                        {cmd.shortcut}
                      </kbd>
                    )}
                    {isSelected && (
                      <CornerDownLeft size={14} className="text-border-active" />
                    )}
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="px-4 py-2 bg-surface-primary text-xs text-gray-500 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span><kbd className="px-1 py-0.5 bg-surface-tertiary rounded text-xs font-mono">↑</kbd> <kbd className="px-1 py-0.5 bg-surface-tertiary rounded text-xs font-mono">↓</kbd> to navigate</span>
            <span><kbd className="px-1 py-0.5 bg-surface-tertiary rounded text-xs font-mono">↵</kbd> to select</span>
            <span><kbd className="px-1 py-0.5 bg-surface-tertiary rounded text-xs font-mono">esc</kbd> to dismiss</span>
          </div>
          <span className="font-mono text-border-active/80">HELIOS v1.4.0 Engine</span>
        </div>
      </div>
    </div>
  );
}

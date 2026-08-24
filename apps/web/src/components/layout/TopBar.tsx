import { useState, useEffect } from 'react';
import { Search, Bell, Shield, Activity, ChevronDown, Check } from 'lucide-react';
import { CommandPalette } from '../common/CommandPalette';
import { NotificationDrawer } from '../common/NotificationDrawer';

const ENGAGEMENT_PROJECTS = [
  { id: 'proj-1', name: 'Operation Red Horizon', scope: '192.168.1.0/24, api.helios.corp', status: 'ACTIVE' },
  { id: 'proj-2', name: 'FinTech Sovereign Cloud Audit', scope: 'aws:us-east-1 (10.0.0.0/16)', status: 'MONITORING' },
  { id: 'proj-3', name: 'PCI-DSS v4.0 Perimeter Scope', scope: 'payment-gw.helios.io', status: 'COMPLETED' },
];

export function TopBar() {
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [activeProject, setActiveProject] = useState(ENGAGEMENT_PROJECTS[0]);
  const [isProjectDropdownOpen, setIsProjectDropdownOpen] = useState(false);

  // Global hotkey ⌘K / Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <>
      <header className="h-14 border-b border-border-default bg-surface-secondary/90 backdrop-blur-md flex items-center justify-between px-4 sticky top-0 z-30 flex-shrink-0">
        {/* Left: Engagement Switcher & Scope Pill */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <button
              onClick={() => setIsProjectDropdownOpen(prev => !prev)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-tertiary border border-border-default hover:border-border-active/60 text-xs font-semibold text-gray-200 transition-all shadow-xs"
            >
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shrink-0" />
              <span className="truncate max-w-[160px] md:max-w-[220px]">{activeProject.name}</span>
              <ChevronDown size={14} className="text-gray-400" />
            </button>

            {isProjectDropdownOpen && (
              <div 
                className="absolute top-full left-0 mt-1.5 w-72 bg-surface-secondary border border-border-default rounded-xl shadow-2xl p-1.5 z-50 animate-in fade-in zoom-in-95 duration-150"
                onMouseLeave={() => setIsProjectDropdownOpen(false)}
              >
                <div className="px-2.5 py-1.5 text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                  Active Engagements
                </div>
                {ENGAGEMENT_PROJECTS.map(proj => (
                  <button
                    key={proj.id}
                    onClick={() => {
                      setActiveProject(proj);
                      setIsProjectDropdownOpen(false);
                    }}
                    className={`w-full text-left p-2 rounded-lg text-xs flex items-center justify-between transition-colors ${
                      proj.id === activeProject.id
                        ? 'bg-border-active/15 text-border-active font-semibold'
                        : 'text-gray-300 hover:bg-surface-tertiary'
                    }`}
                  >
                    <div className="truncate mr-2">
                      <div className="truncate font-medium">{proj.name}</div>
                      <div className="text-[10px] text-gray-500 font-mono truncate">{proj.scope}</div>
                    </div>
                    {proj.id === activeProject.id && <Check size={14} className="shrink-0" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-md bg-surface-primary/70 border border-border-default text-[11px] text-gray-400 font-mono">
            <span className="text-gray-500">SCOPE:</span>
            <span className="text-gray-300 truncate max-w-[200px]">{activeProject.scope}</span>
          </div>
        </div>

        {/* Center: Omni Search & Command Bar */}
        <div className="flex-1 max-w-md mx-4">
          <button
            onClick={() => setIsCommandPaletteOpen(true)}
            className="w-full flex items-center justify-between bg-surface-tertiary/70 hover:bg-surface-tertiary border border-border-default hover:border-border-active/60 rounded-lg py-1.5 px-3 text-xs text-gray-400 transition-all group shadow-xs"
          >
            <div className="flex items-center gap-2 truncate">
              <Search size={15} className="text-gray-400 group-hover:text-border-active transition-colors shrink-0" />
              <span className="truncate">Search targets, CVEs, tools, or press</span>
            </div>
            <div className="flex items-center gap-1 text-[10px] font-mono text-gray-400 shrink-0 ml-2">
              <kbd className="px-1.5 py-0.5 bg-surface-primary rounded border border-border-default font-mono">⌘</kbd>
              <kbd className="px-1.5 py-0.5 bg-surface-primary rounded border border-border-default font-mono">K</kbd>
            </div>
          </button>
        </div>

        {/* Right: Engine Status & Notifications & Profile */}
        <div className="flex items-center gap-2.5">
          {/* AI Engine Status Pill */}
          <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-tertiary border border-border-default text-[11px] font-medium text-gray-300">
            <Activity size={13} className="text-border-active animate-pulse" />
            <span>OpenVINO NPU</span>
            <span className="text-emerald-400 font-mono text-[10px]">99.8%</span>
          </div>

          {/* Notifications Button */}
          <button
            onClick={() => setIsNotificationOpen(true)}
            className="relative p-2 text-gray-400 hover:text-gray-100 hover:bg-surface-tertiary rounded-lg transition-colors"
            aria-label="Security Alerts"
          >
            <Bell size={18} />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-severity-critical rounded-full ring-2 ring-surface-secondary animate-pulse" />
          </button>

          {/* User Profile / Clearance */}
          <div className="flex items-center gap-2 pl-2 border-l border-border-default">
            <div className="flex flex-col text-right hidden sm:block">
              <span className="text-xs font-semibold text-gray-200">G. Bagga</span>
              <span className="text-[9px] font-mono text-border-active uppercase tracking-wider">Top Secret // SCI</span>
            </div>
            <div className="w-8 h-8 rounded-lg bg-surface-tertiary border border-border-default flex items-center justify-center text-border-active font-mono text-xs font-bold shadow-xs">
              <Shield size={16} />
            </div>
          </div>
        </div>
      </header>

      {/* Global Modals */}
      <CommandPalette 
        isOpen={isCommandPaletteOpen} 
        onClose={() => setIsCommandPaletteOpen(false)} 
      />

      <NotificationDrawer 
        isOpen={isNotificationOpen} 
        onClose={() => setIsNotificationOpen(false)} 
      />
    </>
  );
}

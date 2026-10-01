import { useState, useEffect, type FormEvent } from 'react';
import { Search, Activity, ChevronDown, Check, Plus, LoaderCircle, LogOut } from 'lucide-react';
import { CommandPalette } from '../common/CommandPalette';
import { useAuthStore } from '../../stores/authStore';
import { useProjectStore } from '../../stores/projectStore';

export function TopBar() {
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isProjectDropdownOpen, setIsProjectDropdownOpen] = useState(false);
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [projectScope, setProjectScope] = useState('');
  const [createError, setCreateError] = useState<string | null>(null);
  
  const [isScopeModalOpen, setIsScopeModalOpen] = useState(false);
  const [editScope, setEditScope] = useState('');
  const [editOutOfScope, setEditOutOfScope] = useState('');
  const [scopeError, setScopeError] = useState<string | null>(null);
  const [isUpdatingScope, setIsUpdatingScope] = useState(false);
  
  const { projects, activeProjectId, isLoading: projectsLoading, error: projectsError, loadProjects, createProject, updateProjectScope, setActiveProject } = useProjectStore();
  const activeProject = projects.find(project => project.id === activeProjectId);
  const { user, logout } = useAuthStore();

  useEffect(() => { void loadProjects(); }, [loadProjects]);

  const handleCreateProject = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setCreateError(null);
    try {
      await createProject({ name: projectName.trim(), scope: projectScope.trim() });
      setProjectName('');
      setProjectScope('');
      setIsCreatingProject(false);
      setIsProjectDropdownOpen(false);
    } catch (error) {
      setCreateError(error instanceof Error ? error.message : 'Could not create project');
    }
  };

  const handleUpdateScope = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!activeProject) return;
    setScopeError(null);
    setIsUpdatingScope(true);
    try {
      await updateProjectScope(activeProject.id, editScope.trim(), editOutOfScope.trim() || undefined);
      setIsScopeModalOpen(false);
    } catch (error) {
      setScopeError(error instanceof Error ? error.message : 'Could not update scope');
    } finally {
      setIsUpdatingScope(false);
    }
  };

  const openScopeEditor = () => {
    if (!activeProject) return;
    setEditScope(activeProject.scope);
    setEditOutOfScope(activeProject.out_of_scope || '');
    setScopeError(null);
    setIsScopeModalOpen(true);
  };

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
      <header className="h-14 border-b border-border-default bg-surface-secondary/90  flex items-center justify-between px-4 sticky top-0 z-30 flex-shrink-0">
        {/* Left: Engagement Switcher & Scope Pill */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <button
              onClick={() => setIsProjectDropdownOpen(prev => !prev)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-tertiary border border-border-default hover:border-border-active/60 text-xs font-semibold text-gray-200 transition-all shadow-xs"
            >
              <div className={`w-2 h-2 rounded-full shrink-0 ${activeProject ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              <span className="truncate max-w-[160px] md:max-w-[220px]">{activeProject?.name ?? (projectsLoading ? 'Loading projects…' : 'No project selected')}</span>
              <ChevronDown size={14} className="text-gray-400" />
            </button>

            {isProjectDropdownOpen && (
              <div 
                className="absolute top-full left-0 mt-1.5 w-72 bg-surface-secondary border border-border-default rounded-xl shadow-lg p-1.5 z-50 animate-in fade-in zoom-in-95 duration-150"
                onMouseLeave={() => setIsProjectDropdownOpen(false)}
              >
                <div className="px-2.5 py-1.5 text-xs font-bold text-gray-400 uppercase tracking-wider">
                  Projects
                </div>
                {projects.map(proj => (
                  <button
                    key={proj.id}
                    onClick={() => {
                      setActiveProject(proj.id);
                      setIsProjectDropdownOpen(false);
                    }}
                    className={`w-full text-left p-2 rounded-lg text-xs flex items-center justify-between transition-colors ${
                      proj.id === activeProjectId
                        ? 'bg-border-active/15 text-border-active font-semibold'
                        : 'text-gray-300 hover:bg-surface-tertiary'
                    }`}
                  >
                    <div className="truncate mr-2">
                      <div className="truncate font-medium">{proj.name}</div>
                      <div className="text-xs text-gray-500 font-mono truncate">{proj.scope}</div>
                    </div>
                    {proj.id === activeProjectId && <Check size={14} className="shrink-0" />}
                  </button>
                ))}
                {(projectsError || createError) && <p className="px-2.5 py-1.5 text-xs text-severity-critical">{createError ?? projectsError}</p>}
                {isCreatingProject ? (
                  <form onSubmit={handleCreateProject} className="border-t border-border-default mt-1 p-2 space-y-2">
                    <input required minLength={2} maxLength={120} value={projectName} onChange={event => setProjectName(event.target.value)} placeholder="Project name" className="w-full rounded-md bg-surface-primary border border-border-default px-2 py-1.5 text-xs text-gray-100" />
                    <input required value={projectScope} onChange={event => setProjectScope(event.target.value)} placeholder="Authorized scope (IP, CIDR, domain)" className="w-full rounded-md bg-surface-primary border border-border-default px-2 py-1.5 text-xs text-gray-100" />
                    <div className="flex gap-2">
                      <button type="submit" className="flex-1 rounded-md bg-border-active px-2 py-1.5 text-xs font-semibold text-white">Create project</button>
                      <button type="button" onClick={() => setIsCreatingProject(false)} className="rounded-md border border-border-default px-2 py-1.5 text-xs text-gray-300">Cancel</button>
                    </div>
                  </form>
                ) : (
                  <button onClick={() => setIsCreatingProject(true)} className="mt-1 flex w-full items-center gap-2 rounded-lg border-t border-border-default px-2.5 py-2 text-left text-xs text-border-active hover:bg-surface-tertiary">
                    <Plus size={14} /> Create project
                  </button>
                )}
              </div>
            )}
          </div>

          <button 
            onClick={openScopeEditor}
            disabled={!activeProject}
            className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-md bg-surface-primary/70 border border-border-default hover:border-border-active/60 text-xs text-gray-400 font-mono transition-colors cursor-pointer"
            title={activeProject ? "Click to edit scope" : ""}
          >
            <span className="text-gray-500">SCOPE:</span>
            <span className="text-gray-300 truncate max-w-[200px]">{activeProject?.scope ?? 'Create or select a project to begin'}</span>
          </button>
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
            <div className="flex items-center gap-1 text-xs font-mono text-gray-400 shrink-0 ml-2">
              <kbd className="px-1.5 py-0.5 bg-surface-primary rounded border border-border-default font-mono">⌘</kbd>
              <kbd className="px-1.5 py-0.5 bg-surface-primary rounded border border-border-default font-mono">K</kbd>
            </div>
          </button>
        </div>

        {/* Right: Runtime status and local workspace */}
        <div className="flex items-center gap-2.5">
          {/* AI Engine Status Pill */}
          <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-tertiary border border-border-default text-xs font-medium text-gray-300">
            {projectsLoading ? <LoaderCircle size={13} className="text-border-active animate-spin" /> : <Activity size={13} className="text-border-active" />}
            <span>Local analysis</span>
            <span className="text-gray-400 font-mono text-xs">status in Settings</span>
          </div>

          {/* User profile & Logout */}
          <div className="flex items-center gap-3 pl-3 border-l border-border-default">
            <div className="flex flex-col text-right hidden sm:block">
              <span className="text-xs font-semibold text-gray-200">{user?.username || 'Operator'}</span>
              <span className="text-[9px] font-mono text-gray-500 uppercase tracking-wider">{user?.role || 'Analyst'}</span>
            </div>
            <button 
              onClick={logout}
              className="w-8 h-8 rounded-lg bg-surface-tertiary hover:bg-surface-hover border border-border-default flex items-center justify-center text-gray-400 hover:text-rose-400 font-mono text-xs font-bold shadow-xs transition-colors"
              title="Logout"
            >
              <LogOut size={14} />
            </button>
          </div>
        </div>
      </header>

      {/* Global Modals */}
      <CommandPalette 
        isOpen={isCommandPaletteOpen} 
        onClose={() => setIsCommandPaletteOpen(false)} 
      />

      {/* Scope Editor Modal */}
      {isScopeModalOpen && activeProject && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-surface-secondary border border-border-default rounded-xl shadow-lg p-5">
            <h2 className="text-lg font-bold text-gray-100 mb-2">Edit Project Scope</h2>
            <p className="text-xs text-gray-400 mb-4">Update authorized networks, domains, or IPs for this engagement.</p>
            <form onSubmit={handleUpdateScope} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">In-Scope Targets</label>
                <textarea
                  value={editScope}
                  onChange={e => setEditScope(e.target.value)}
                  className="w-full rounded-md bg-surface-primary border border-border-default px-3 py-2 text-xs text-gray-100"
                  rows={3}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1">Out-of-Scope (Optional)</label>
                <textarea
                  value={editOutOfScope}
                  onChange={e => setEditOutOfScope(e.target.value)}
                  className="w-full rounded-md bg-surface-primary border border-border-default px-3 py-2 text-xs text-gray-100"
                  rows={2}
                />
              </div>
              {scopeError && <p className="text-xs text-severity-critical">{scopeError}</p>}
              <div className="flex justify-end gap-2 mt-4">
                <button type="button" onClick={() => setIsScopeModalOpen(false)} className="px-3 py-1.5 text-xs text-gray-300 hover:text-white">Cancel</button>
                <button type="submit" disabled={isUpdatingScope} className="px-3 py-1.5 rounded bg-border-active text-white text-xs font-semibold hover:bg-opacity-90 disabled:opacity-50">
                  {isUpdatingScope ? 'Saving...' : 'Save Scope'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

import { Search, Bell, User } from 'lucide-react';

export function TopBar() {
  return (
    <header className="h-14 border-b border-border-default bg-surface-secondary flex items-center justify-between px-4 sticky top-0 z-10">
      <div className="flex-1 max-w-xl">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={18} />
          <input
            type="text"
            placeholder="Search across all projects..."
            aria-label="Search across all projects"
            className="w-full bg-surface-tertiary border border-border-default rounded-lg py-2 pl-10 pr-20 text-sm text-gray-200 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-border-active/50 focus:border-border-active transition-all"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-xs text-gray-500 pointer-events-none">
            <kbd className="px-1.5 py-0.5 bg-surface-hover rounded border border-border-default font-mono">⌘</kbd>
            <kbd className="px-1.5 py-0.5 bg-surface-hover rounded border border-border-default font-mono">K</kbd>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3 ml-4">
        <button
          className="relative p-2 text-gray-400 hover:text-gray-200 hover:bg-surface-tertiary rounded-lg transition-colors"
          aria-label="Notifications"
          aria-haspopup="true"
        >
          <Bell size={20} />
          {/* ring-2 prevents the border from shrinking the dot size */}
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-severity-critical rounded-full ring-2 ring-surface-secondary"></span>
        </button>

        <button
          className="flex items-center justify-center w-9 h-9 rounded-full bg-surface-tertiary text-gray-300 hover:text-white transition-all border border-border-default hover:border-border-active hover:shadow-sm"
          aria-label="User profile"
          aria-haspopup="menu"
        >
          <User size={18} />
        </button>
      </div>
    </header>
  );
}
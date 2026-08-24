import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, MessageSquare, Target, Globe, Code2, FileText,
  Bug, Network, Database, FileBox, Settings, ChevronLeft, ChevronRight
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { useUiStore } from '../../stores/uiStore';
import { cn } from '../../lib/utils';

interface NavItemConfig {
  icon: LucideIcon;
  label: string;
  path: string;
}

const navItems: NavItemConfig[] = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
  { icon: MessageSquare, label: 'Chat', path: '/chat' },
  { icon: Target, label: 'Recon', path: '/recon' },
  { icon: Globe, label: 'Web Security', path: '/web' },
  { icon: Code2, label: 'Source Code', path: '/code' },
  { icon: FileText, label: 'Logs', path: '/logs' },
  { icon: Bug, label: 'Malware', path: '/malware' },
  { icon: Network, label: 'Knowledge Graph', path: '/graph' },
  { icon: Database, label: 'Evidence', path: '/evidence' },
  { icon: FileBox, label: 'Reports', path: '/reports' },
];

const bottomNavItems: NavItemConfig[] = [
  { icon: Settings, label: 'Settings', path: '/settings' },
];

// Extracted component to prevent code duplication
function NavItem({ item, isExpanded }: { item: NavItemConfig; isExpanded: boolean }) {
  return (
    <NavLink
      to={item.path}
      title={!isExpanded ? item.label : undefined} // Fallback for native tooltip
      aria-label={item.label}
      className={({ isActive }) =>
        cn(
          "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-300 overflow-hidden",
          isActive
            ? "bg-border-active/10 text-border-active shadow-[inset_0_1px_0_rgba(255,255,255,0.1)] border border-border-active/20"
            : "text-gray-400 hover:bg-surface-tertiary/50 hover:text-gray-200 border border-transparent",
          !isExpanded && "justify-center px-0"
        )
      }
    >
      {({ isActive }) => (
        <>
          {isActive && (
            <span className="absolute left-0 top-1/2 h-full w-1 -translate-y-1/2 bg-border-active shadow-[0_0_10px_rgb(var(--border-active))]" />
          )}
          <item.icon size={20} className="flex-shrink-0" />
          {isExpanded && <span className="truncate">{item.label}</span>}

          {/* Custom CSS Tooltip for collapsed state */}
          {!isExpanded && (
            <span className="invisible absolute left-full top-1/2 ml-2 -translate-y-1/2 whitespace-nowrap rounded-md bg-surface-hover px-2 py-1 text-xs text-gray-200 shadow-lg group-hover:visible z-50">
              {item.label}
            </span>
          )}
        </>
      )}
    </NavLink>
  );
}

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUiStore();

  return (
    <aside
      className={cn(
        "flex flex-col h-screen bg-surface-secondary/80 backdrop-blur-xl border-r border-border-default/50 transition-[width] duration-300 ease-in-out relative z-10",
        sidebarOpen ? "w-64" : "w-16"
      )}
      aria-label="Main Navigation"
    >
      <div className="flex items-center justify-between p-4 border-b border-border-default h-14">
        {sidebarOpen && (
          <span className="font-bold text-lg tracking-wide text-gray-100">
            HELIOS
          </span>
        )}
        <button
          onClick={toggleSidebar}
          aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
          className="p-1.5 rounded-md hover:bg-surface-hover text-gray-400 hover:text-gray-200 transition-colors ml-auto"
        >
          {sidebarOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto overflow-x-hidden py-4 px-2 space-y-1" aria-label="Primary">
        {navItems.map((item) => (
          <NavItem key={item.path} item={item} isExpanded={sidebarOpen} />
        ))}
      </nav>

      <div className="p-2 border-t border-border-default">
        {bottomNavItems.map((item) => (
          <NavItem key={item.path} item={item} isExpanded={sidebarOpen} />
        ))}
      </div>
    </aside>
  );
}
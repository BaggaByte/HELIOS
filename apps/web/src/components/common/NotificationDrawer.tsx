import { useState } from 'react';
import {
  Bell,
  ShieldAlert,
  Target,
  CheckCircle2,
  X,
  AlertTriangle,
  FileText,
  ExternalLink
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export interface SecurityNotification {
  id: string;
  title: string;
  message: string;
  timestamp: string;
  type: 'critical' | 'warning' | 'info' | 'success';
  link?: string;
  read: boolean;
}

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export function NotificationDrawer({ isOpen, onClose }: NotificationDrawerProps) {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<SecurityNotification[]>([
    {
      id: 'notif-1',
      title: 'Critical CVE-2021-41773 Discovered',
      message: 'Apache HTTP Server 2.4.49 path traversal identified on target host 192.168.1.15:80. Exploit PoC validated.',
      timestamp: '2 mins ago',
      type: 'critical',
      link: '/web',
      read: false,
    },
    {
      id: 'notif-2',
      title: 'SYN Port Sweep Completed',
      message: 'Recon scan finished for subnet 192.168.1.0/24. 4 active hosts and 14 exposed services mapped to knowledge graph.',
      timestamp: '18 mins ago',
      type: 'info',
      link: '/recon',
      read: false,
    },
    {
      id: 'notif-3',
      title: 'Hardcoded Secret Detected in Source',
      message: 'High-entropy AWS Secret Access Key identified in src/api/v1/auth_service.py line 42.',
      timestamp: '45 mins ago',
      type: 'warning',
      link: '/code',
      read: true,
    },
    {
      id: 'notif-4',
      title: 'Evidence SHA-256 Verified',
      message: 'Integrity validation passed for memory dump snapshot dump_0x847a.raw against baseline hash.',
      timestamp: '1 hour ago',
      type: 'success',
      link: '/evidence',
      read: true,
    }
  ]);

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const getIcon = (type: SecurityNotification['type']) => {
    switch (type) {
      case 'critical':
        return <ShieldAlert size={16} className="text-severity-critical shrink-0" />;
      case 'warning':
        return <AlertTriangle size={16} className="text-severity-high shrink-0" />;
      case 'success':
        return <CheckCircle2 size={16} className="text-severity-low shrink-0" />;
      default:
        return <Target size={16} className="text-severity-info shrink-0" />;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden" onClick={onClose}>
      <div className="absolute inset-0 bg-black/40 backdrop-blur-xs transition-opacity" />
      
      <div 
        className="absolute inset-y-0 right-0 max-w-md w-full bg-surface-secondary border-l border-border-default shadow-2xl flex flex-col animate-in slide-in-from-right duration-200"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 border-b border-border-default flex items-center justify-between bg-surface-tertiary/40">
          <div className="flex items-center gap-2">
            <Bell size={18} className="text-border-active" />
            <h2 className="text-base font-bold text-gray-100">Operational Alerts</h2>
            <span className="px-2 py-0.5 text-xs bg-severity-critical/20 text-severity-critical rounded-full font-mono font-bold">
              {notifications.filter(n => !n.read).length}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={markAllAsRead}
              className="text-xs text-gray-400 hover:text-gray-200 transition-colors"
            >
              Mark all read
            </button>
            <button
              onClick={onClose}
              className="p-1 rounded-lg hover:bg-surface-hover text-gray-400 hover:text-gray-200"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Notifications List */}
        <div className="flex-1 overflow-y-auto p-4 custom-scrollbar space-y-3">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-gray-500 text-sm">
              <FileText size={32} className="opacity-40 mb-2" />
              <span>No alerts in feed</span>
            </div>
          ) : (
            notifications.map(notif => (
              <div
                key={notif.id}
                onClick={() => {
                  if (notif.link) {
                    navigate(notif.link);
                    onClose();
                  }
                }}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                  !notif.read
                    ? 'bg-surface-tertiary border-border-active/40 hover:border-border-active'
                    : 'bg-surface-primary/60 border-border-default/80 hover:bg-surface-tertiary'
                }`}
              >
                <div className="flex items-start gap-2.5">
                  {getIcon(notif.type)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h4 className="text-xs font-bold text-gray-200 truncate">{notif.title}</h4>
                      <span className="text-[10px] text-gray-500 font-mono shrink-0">{notif.timestamp}</span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1 leading-relaxed">{notif.message}</p>
                    
                    {notif.link && (
                      <div className="flex items-center gap-1 text-[11px] text-border-active hover:underline mt-2 font-medium">
                        <span>Investigate Finding</span>
                        <ExternalLink size={11} />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-border-default bg-surface-primary text-xs text-gray-500 flex items-center justify-between">
          <span>Continuous Threat Telemetry Active</span>
          <span className="font-mono text-emerald-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            LIVE
          </span>
        </div>
      </div>
    </div>
  );
}

import { Activity, Target, ShieldAlert, FileText, Bug, Network, ShieldCheck, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';

import { useRecon } from '../../hooks/useRecon';
import { useWebSecurity } from '../../hooks/useWebSecurity';
import { useLogs } from '../../hooks/useLogs';
import { useEvidence } from '../../hooks/useEvidence';

export function MainDashboard() {
  const { hosts } = useRecon();
  const { findings } = useWebSecurity();
  const { events } = useLogs();
  const { evidenceList } = useEvidence();

  const openPorts = hosts?.reduce((acc, host) => acc + (host.services?.length || 0), 0) || 0;
  const criticalFindings = findings?.filter(f => f.severity.toLowerCase() === 'critical').length || 0;
  const highFindings = findings?.filter(f => f.severity.toLowerCase() === 'high').length || 0;

  const statCards = [
    {
      title: 'Active Targets',
      value: hosts?.length || 0,
      subtext: `${openPorts} open ports discovered`,
      icon: Target,
      color: 'text-blue-400',
      bg: 'bg-blue-400/10',
      link: '/recon',
    },
    {
      title: 'Web Vulnerabilities',
      value: findings?.length || 0,
      subtext: `${criticalFindings} Critical, ${highFindings} High`,
      icon: ShieldAlert,
      color: criticalFindings > 0 ? 'text-severity-critical' : 'text-severity-high',
      bg: criticalFindings > 0 ? 'bg-severity-critical/10' : 'bg-severity-high/10',
      link: '/web',
    },
    {
      title: 'SIEM Log Events',
      value: events?.length || 0,
      subtext: 'Ingested events in timeline',
      icon: Activity,
      color: 'text-purple-400',
      bg: 'bg-purple-400/10',
      link: '/logs',
    },
    {
      title: 'Secured Evidence',
      value: evidenceList?.length || 0,
      subtext: 'Cryptographically verified',
      icon: ShieldCheck,
      color: 'text-green-400',
      bg: 'bg-green-400/10',
      link: '/evidence',
    },
  ];

  return (
    <div className="flex flex-col h-full bg-surface-primary overflow-y-auto custom-scrollbar p-6 space-y-8 animate-in fade-in duration-500">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-100 flex items-center gap-3">
          <Zap className="text-border-active" size={32} />
          HELIOS Mission Control
        </h1>
        <p className="text-gray-400 mt-2 text-lg">
          Offensive security copilot and centralized intelligence dashboard.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, idx) => (
          <Link 
            key={idx} 
            to={stat.link}
            className="block p-6 rounded-2xl bg-surface-secondary border border-border-default hover:border-border-active transition-all hover:shadow-lg hover:-translate-y-1 group"
          >
            <div className="flex items-start justify-between mb-4">
              <div className={`p-3 rounded-xl ${stat.bg} ${stat.color}`}>
                <stat.icon size={24} />
              </div>
            </div>
            <h3 className="text-3xl font-bold text-gray-100 mb-1">{stat.value}</h3>
            <p className="text-sm font-medium text-gray-300">{stat.title}</p>
            <p className="text-xs text-gray-500 mt-2 font-mono">{stat.subtext}</p>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Quick Actions */}
        <div className="p-6 rounded-2xl bg-surface-secondary border border-border-default shadow-sm">
          <h2 className="text-xl font-bold text-gray-100 mb-4 flex items-center gap-2">
            <Activity size={20} className="text-gray-400" />
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Link to="/chat" className="flex items-center gap-3 p-4 rounded-xl bg-surface-tertiary border border-border-default hover:border-border-active transition-colors group">
              <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg group-hover:scale-110 transition-transform">
                <Zap size={20} />
              </div>
              <div className="text-sm font-semibold text-gray-200">Chat with AI Copilot</div>
            </Link>
            <Link to="/malware" className="flex items-center gap-3 p-4 rounded-xl bg-surface-tertiary border border-border-default hover:border-border-active transition-colors group">
              <div className="p-2 bg-red-500/10 text-red-400 rounded-lg group-hover:scale-110 transition-transform">
                <Bug size={20} />
              </div>
              <div className="text-sm font-semibold text-gray-200">Analyze Malware</div>
            </Link>
            <Link to="/recon" className="flex items-center gap-3 p-4 rounded-xl bg-surface-tertiary border border-border-default hover:border-border-active transition-colors group">
              <div className="p-2 bg-purple-500/10 text-purple-400 rounded-lg group-hover:scale-110 transition-transform">
                <Target size={20} />
              </div>
              <div className="text-sm font-semibold text-gray-200">Ingest Nmap Scan</div>
            </Link>
            <Link to="/graph" className="flex items-center gap-3 p-4 rounded-xl bg-surface-tertiary border border-border-default hover:border-border-active transition-colors group">
              <div className="p-2 bg-green-500/10 text-green-400 rounded-lg group-hover:scale-110 transition-transform">
                <Network size={20} />
              </div>
              <div className="text-sm font-semibold text-gray-200">View Knowledge Graph</div>
            </Link>
          </div>
        </div>

        {/* Recent Logs Snippet */}
        <div className="p-6 rounded-2xl bg-surface-secondary border border-border-default shadow-sm flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-100 flex items-center gap-2">
              <FileText size={20} className="text-gray-400" />
              Recent Log Events
            </h2>
            <Link to="/logs" className="text-sm text-border-active hover:underline">View All</Link>
          </div>
          
          <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-3">
            {events && events.length > 0 ? (
              events.slice(0, 5).map(evt => (
                <div key={evt.id} className="p-3 bg-surface-tertiary rounded-lg border border-border-default text-sm flex gap-3">
                  <span className={`flex-shrink-0 text-xs px-2 py-0.5 rounded font-bold uppercase self-start ${
                    evt.severity.toLowerCase() === 'critical' ? 'bg-severity-critical/20 text-severity-critical' :
                    evt.severity.toLowerCase() === 'high' ? 'bg-severity-high/20 text-severity-high' :
                    evt.severity.toLowerCase() === 'medium' ? 'bg-severity-medium/20 text-severity-medium' :
                    'bg-severity-info/20 text-severity-info'
                  }`}>
                    {evt.severity}
                  </span>
                  <div className="flex-1 truncate">
                    <span className="text-gray-400 font-mono mr-2">{new Date(evt.timestamp).toLocaleTimeString()}</span>
                    <span className="text-gray-200">{evt.message}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500 text-sm italic py-8">
                No recent events found. Ingest logs to populate this feed.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}

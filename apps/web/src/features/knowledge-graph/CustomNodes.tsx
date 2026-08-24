import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Server, ShieldAlert, Binary, Users, Key, Box, Cpu } from 'lucide-react';
import { cn } from '../../lib/utils';

const iconMap: Record<string, any> = {
  host: Server,
  vulnerability: ShieldAlert,
  malware: Binary,
  user: Users,
  credential: Key,
  service: Box,
  default: Cpu
};

const colorMap: Record<string, string> = {
  host: 'border-blue-500/50 bg-blue-500/10 text-blue-400',
  vulnerability: 'border-red-500/50 bg-red-500/10 text-red-400',
  malware: 'border-purple-500/50 bg-purple-500/10 text-purple-400',
  user: 'border-green-500/50 bg-green-500/10 text-green-400',
  service: 'border-orange-500/50 bg-orange-500/10 text-orange-400',
  default: 'border-gray-500/50 bg-gray-500/10 text-gray-400'
};

export const CustomNode = memo(({ data }: any) => {
  const type = data.type?.toLowerCase() || 'default';
  const Icon = iconMap[type] || iconMap.default;
  const colors = colorMap[type] || colorMap.default;

  return (
    <div className={cn("px-4 py-2 shadow-md rounded-md border-2 min-w-[150px] transition-all hover:scale-105", colors, "bg-surface-secondary backdrop-blur-md")}>
      <Handle type="target" position={Position.Top} className="w-16 !bg-border-active" />
      
      <div className="flex flex-col items-center justify-center">
        <div className="flex items-center gap-2 mb-1">
          <Icon size={16} />
          <span className="text-[10px] font-bold uppercase tracking-wider opacity-80">{type}</span>
        </div>
        <div className="text-sm font-bold text-gray-100 text-center">{data.label}</div>
      </div>
      
      <Handle type="source" position={Position.Bottom} className="w-16 !bg-border-active" />
    </div>
  );
});

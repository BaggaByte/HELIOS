import { useState, useEffect, useRef } from 'react';
import { Network, Server, ShieldAlert, Globe, Link2, X, Plus, Activity, Crosshair } from 'lucide-react';
import { useGraphStore } from '../../stores/graphStore';
import { cn } from '../../lib/utils';
import type { NodeType } from '../../services/graphService';

export function KnowledgeGraphDashboard() {
  const { data, selectedNodeId, isLoading, fetchGraph, selectNode, updateNodePosition } = useGraphStore();
  const [isDragging, setIsDragging] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchGraph('default-project-id');
  }, [fetchGraph]);

  // Handle Dragging Logic
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    updateNodePosition(isDragging, x, y);
  };

  const handleMouseUp = () => {
    setIsDragging(null);
  };

  const getNodeIcon = (type: NodeType) => {
    switch (type) {
      case 'Host': return <Server size={24} className="text-gray-200" />;
      case 'Vulnerability': return <ShieldAlert size={24} className="text-white" />;
      case 'Domain': return <Globe size={24} className="text-gray-200" />;
      case 'Service': return <Link2 size={24} className="text-gray-200" />;
      default: return <Network size={24} className="text-gray-200" />;
    }
  };

  const getNodeStyle = (type: NodeType, isSelected: boolean) => {
    const baseStyle = "absolute w-16 h-16 -ml-8 -mt-8 rounded-2xl flex items-center justify-center cursor-pointer transition-shadow shadow-lg z-20 ";
    const selectedStyle = isSelected ? "ring-2 ring-white ring-offset-2 ring-offset-[#0d1117] shadow-[0_0_30px_rgba(255,255,255,0.2)] " : "";
    
    switch (type) {
      case 'Vulnerability': 
        return baseStyle + selectedStyle + "bg-severity-critical border border-severity-critical/50 shadow-severity-critical/30";
      case 'Host': 
        return baseStyle + selectedStyle + "bg-surface-tertiary border border-border-default hover:border-border-active";
      case 'Service': 
        return baseStyle + selectedStyle + "bg-severity-info/20 border border-severity-info hover:bg-severity-info/30";
      case 'Domain': 
        return baseStyle + selectedStyle + "bg-purple-500/20 border border-purple-500 hover:bg-purple-500/30";
      default: 
        return baseStyle + selectedStyle + "bg-surface-tertiary border border-border-default";
    }
  };

  const selectedNode = data.nodes.find(n => n.id === selectedNodeId);

  return (
    <div className="flex flex-col h-full overflow-hidden relative bg-transparent">
      
      {/* Dashboard Header Overlay */}
      <div className="absolute top-8 left-8 z-30 pointer-events-none">
        <h1 className="text-3xl font-bold text-gray-100 neon-text flex items-center gap-3">
          <Network className="text-border-active" size={32} />
          Knowledge Graph
        </h1>
        <p className="text-gray-400 mt-2">Visualizing attack paths and infrastructure relationships.</p>
      </div>

      {/* Control Bar Overlay */}
      <div className="absolute top-8 right-8 z-30 glass-panel p-2 rounded-xl border border-border-default/50 flex gap-2 shadow-2xl">
        <button className="px-4 py-2 rounded-lg bg-surface-secondary text-sm font-medium hover:bg-surface-tertiary transition-colors flex items-center gap-2">
          <Crosshair size={16} /> Re-center
        </button>
        <button className="px-4 py-2 rounded-lg bg-border-active text-bg-primary text-sm font-medium hover:opacity-90 transition-opacity flex items-center gap-2">
          <Plus size={16} /> Cypher Query
        </button>
      </div>

      {/* Main SVG/CSS Canvas */}
      <div 
        ref={containerRef}
        className="flex-1 w-full h-full relative cursor-grab active:cursor-grabbing bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-surface-tertiary/10 via-[#0d1117] to-[#0d1117]"
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {isLoading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <Activity size={48} className="text-border-active animate-spin opacity-50" />
          </div>
        ) : (
          <>
            {/* Draw Edges (SVG) */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
              {data.edges.map(edge => {
                const sourceNode = data.nodes.find(n => n.id === edge.source);
                const targetNode = data.nodes.find(n => n.id === edge.target);
                if (!sourceNode || !targetNode) return null;

                // Calculate center points
                const x1 = sourceNode.x || 0;
                const y1 = sourceNode.y || 0;
                const x2 = targetNode.x || 0;
                const y2 = targetNode.y || 0;

                // Simple straight line for now
                return (
                  <g key={edge.id}>
                    <line 
                      x1={x1} y1={y1} x2={x2} y2={y2} 
                      stroke="rgba(255, 255, 255, 0.15)" 
                      strokeWidth="2"
                    />
                    <text 
                      x={(x1 + x2) / 2} 
                      y={(y1 + y2) / 2 - 8} 
                      fill="rgba(255, 255, 255, 0.4)" 
                      fontSize="10" 
                      textAnchor="middle"
                      className="font-mono tracking-widest uppercase pointer-events-none"
                    >
                      {edge.label}
                    </text>
                  </g>
                );
              })}
            </svg>

            {/* Draw Nodes (HTML/CSS) */}
            {data.nodes.map(node => (
              <div 
                key={node.id}
                className={getNodeStyle(node.type, selectedNodeId === node.id)}
                style={{ left: node.x, top: node.y }}
                onMouseDown={() => {
                  selectNode(node.id);
                  setIsDragging(node.id);
                }}
              >
                {getNodeIcon(node.type)}
                
                {/* Node Label (below icon) */}
                <div className="absolute top-full mt-3 left-1/2 -translate-x-1/2 whitespace-nowrap text-center pointer-events-none">
                  <div className="text-sm font-bold text-gray-200 drop-shadow-md">{node.label}</div>
                  <div className="text-[10px] text-border-active font-mono uppercase tracking-wider">{node.type}</div>
                </div>
              </div>
            ))}
          </>
        )}
      </div>

      {/* Floating Detail Panel (Right Side) */}
      <div className={cn(
        "absolute right-8 top-28 bottom-8 w-80 glass-panel rounded-2xl border border-border-default/50 shadow-2xl transition-all duration-300 transform z-40 flex flex-col overflow-hidden",
        selectedNode ? "translate-x-0 opacity-100" : "translate-x-full opacity-0 pointer-events-none"
      )}>
        {selectedNode && (
          <>
            <div className="flex items-center justify-between p-4 border-b border-border-default/50 bg-surface-secondary/40 backdrop-blur">
              <h3 className="font-bold text-gray-100 flex items-center gap-2">
                {getNodeIcon(selectedNode.type)}
                {selectedNode.type} Details
              </h3>
              <button 
                onClick={() => selectNode(null)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-6 custom-scrollbar space-y-6">
              <div>
                <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Label</div>
                <div className="font-mono text-lg text-gray-200 break-all">{selectedNode.label}</div>
              </div>

              <div>
                <div className="text-xs text-gray-500 uppercase tracking-wider mb-3">Properties</div>
                <div className="space-y-2">
                  {Object.entries(selectedNode.properties).map(([key, value]) => (
                    <div key={key} className="bg-surface-primary/30 p-3 rounded-lg border border-border-default/30">
                      <span className="text-gray-500 font-mono text-xs">{key}: </span>
                      <span className={cn(
                        "font-medium text-sm",
                        key === 'severity' && value === 'CRITICAL' ? 'text-severity-critical font-bold' : 'text-gray-300'
                      )}>
                        {String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              
              {selectedNode.type === 'Vulnerability' && (
                <button className="w-full py-3 rounded-xl bg-severity-critical/20 text-severity-critical font-bold border border-severity-critical/50 hover:bg-severity-critical hover:text-white transition-all shadow-[0_0_15px_rgb(var(--severity-critical)/0.2)]">
                  Generate Exploit Payload
                </button>
              )}
            </div>
          </>
        )}
      </div>

    </div>
  );
}

import { useState, useCallback, useMemo } from 'react';
import ReactFlow, { 
  Controls, 
  Background, 
  useNodesState, 
  useEdgesState,
  Panel,
  MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Share2, RefreshCw, Layers } from 'lucide-react';

import { useGraph } from '../../hooks/useGraph';
import { CustomNode } from './CustomNodes';

const nodeTypes = {
  customNode: CustomNode,
};

export function GraphDashboard() {
  const { graphData, isLoading, error } = useGraph();
  
  // Need to handle state if graph data loads
  const initialNodes = useMemo(() => graphData?.nodes || [], [graphData]);
  const initialEdges = useMemo(() => {
    return (graphData?.edges || []).map(edge => ({
      ...edge,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#3b82f6', // blue-500
      },
      style: { stroke: '#3b82f6', strokeWidth: 2 }
    }));
  }, [graphData]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  
  // Sync state when data loads
  useMemo(() => {
    if (graphData) {
      setNodes(graphData.nodes);
      setEdges(graphData.edges.map(edge => ({
        ...edge,
        markerEnd: { type: MarkerType.ArrowClosed, color: '#3b82f6' },
        style: { stroke: '#3b82f6', strokeWidth: 2 }
      })));
    }
  }, [graphData, setNodes, setEdges]);

  const [selectedNode, setSelectedNode] = useState<any>(null);

  const onNodeClick = useCallback((_: any, node: any) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  return (
    <div className="flex flex-col h-full bg-surface-primary overflow-hidden relative">
      {/* Header Overlay */}
      <div className="absolute top-0 left-0 right-0 p-4 flex items-center justify-between z-10 pointer-events-none">
        <div className="pointer-events-auto flex items-center gap-2 bg-surface-secondary/80 backdrop-blur-md p-3 rounded-lg border border-border-default shadow-lg">
          <Share2 className="text-border-active" size={20} />
          <div>
            <h1 className="text-lg font-bold text-gray-100 leading-tight">Knowledge Graph</h1>
            <p className="text-xs text-gray-400">Interactive Attack Surface Topology</p>
          </div>
        </div>
        
        {isLoading && (
          <div className="pointer-events-auto bg-surface-secondary/80 backdrop-blur-md px-4 py-2 rounded-lg border border-border-default flex items-center gap-2 text-border-active shadow-lg">
            <RefreshCw size={16} className="animate-spin" />
            <span className="text-sm font-semibold">Loading Graph...</span>
          </div>
        )}
      </div>

      {/* Main Graph Area */}
      <div className="flex-1 w-full h-full">
        {error ? (
          <div className="h-full flex items-center justify-center text-severity-critical">
            Failed to load graph: {error.message}
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            nodeTypes={nodeTypes}
            fitView
            className="bg-[#0f1115]"
          >
            <Background color="#2a2d36" gap={20} size={1} />
            <Controls className="!bg-surface-secondary !border-border-default !fill-gray-300" />
            
            {/* Properties Panel (Right side) */}
            {selectedNode && (
              <Panel position="top-right" className="!m-4 mt-20 pointer-events-auto w-80 bg-surface-secondary border border-border-default rounded-lg shadow-xl overflow-hidden animate-in fade-in slide-in-from-right-4">
                <div className="p-3 border-b border-border-default bg-surface-tertiary flex items-center gap-2">
                  <Layers size={16} className="text-border-active" />
                  <h3 className="font-bold text-gray-100 text-sm">Entity Details</h3>
                </div>
                <div className="p-4">
                  <div className="mb-4">
                    <span className="text-xs text-gray-500 uppercase font-bold tracking-wider block mb-1">Type</span>
                    <span className="text-sm font-semibold text-gray-200 capitalize bg-surface-primary px-2 py-1 rounded border border-border-default inline-block">
                      {selectedNode.data?.type || 'Unknown'}
                    </span>
                  </div>
                  <div className="mb-4">
                    <span className="text-xs text-gray-500 uppercase font-bold tracking-wider block mb-1">Label</span>
                    <span className="text-base font-mono text-gray-100 break-words block">
                      {selectedNode.data?.label}
                    </span>
                  </div>
                  
                  {selectedNode.data?.properties && Object.keys(selectedNode.data.properties).length > 0 && (
                    <div>
                      <span className="text-xs text-gray-500 uppercase font-bold tracking-wider block mb-2">Properties</span>
                      <div className="bg-surface-primary rounded border border-border-default p-2 space-y-2">
                        {Object.entries(selectedNode.data.properties).map(([key, value]) => (
                          <div key={key} className="flex justify-between items-start text-sm">
                            <span className="text-gray-400 capitalize">{key}:</span>
                            <span className="font-mono text-gray-200 text-right max-w-[60%] break-all">
                              {String(value)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </Panel>
            )}
          </ReactFlow>
        )}
      </div>
    </div>
  );
}

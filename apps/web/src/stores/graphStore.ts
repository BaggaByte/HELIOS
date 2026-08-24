import { create } from 'zustand';
import { graphService, type GraphData, type GraphNode } from '../services/graphService';

interface GraphState {
  data: GraphData;
  selectedNodeId: string | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  fetchGraph: (projectId: string) => Promise<void>;
  selectNode: (id: string | null) => void;
  updateNodePosition: (id: string, x: number, y: number) => void;
}

export const useGraphStore = create<GraphState>((set, get) => ({
  data: { nodes: [], edges: [] },
  selectedNodeId: null,
  isLoading: false,
  error: null,

  fetchGraph: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      // Mock data representing a typical attack path
      const data = await graphService.getGraph(projectId).catch(() => ({
        nodes: [
          { id: 'n1', type: 'Domain', label: 'example.com', properties: { registrar: 'Namecheap' }, x: 150, y: 300 },
          { id: 'n2', type: 'Host', label: '192.168.1.10', properties: { os: 'Linux 5.4', status: 'up' }, x: 400, y: 200 },
          { id: 'n3', type: 'Host', label: '192.168.1.15', properties: { os: 'Windows Server', status: 'up' }, x: 400, y: 400 },
          { id: 'n4', type: 'Service', label: 'HTTP (80)', properties: { product: 'Apache', version: '2.4.41' }, x: 650, y: 150 },
          { id: 'n5', type: 'Service', label: 'RDP (3389)', properties: { product: 'ms-wbt-server' }, x: 650, y: 400 },
          { id: 'n6', type: 'Vulnerability', label: 'CVE-2021-41773', properties: { severity: 'CRITICAL', description: 'Path Traversal in Apache 2.4.49' }, x: 900, y: 150 },
        ],
        edges: [
          { id: 'e1', source: 'n1', target: 'n2', label: 'RESOLVES_TO' },
          { id: 'e2', source: 'n1', target: 'n3', label: 'RESOLVES_TO' },
          { id: 'e3', source: 'n2', target: 'n4', label: 'HOSTS_SERVICE' },
          { id: 'e4', source: 'n3', target: 'n5', label: 'HOSTS_SERVICE' },
          { id: 'e5', source: 'n4', target: 'n6', label: 'VULNERABLE_TO' },
        ]
      } as GraphData));
      
      set({ data, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  selectNode: (id) => set({ selectedNodeId: id }),
  
  updateNodePosition: (id, x, y) => set((state) => ({
    data: {
      ...state.data,
      nodes: state.data.nodes.map(node => 
        node.id === id ? { ...node, x, y } : node
      )
    }
  }))
}));

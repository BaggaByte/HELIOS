import { create } from 'zustand';
import { graphService, type GraphData } from '../services/graphService';

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

export const useGraphStore = create<GraphState>((set) => ({
  data: { nodes: [], edges: [] },
  selectedNodeId: null,
  isLoading: false,
  error: null,

  fetchGraph: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const data = await graphService.getGraph(projectId);
      
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

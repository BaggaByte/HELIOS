import { useQuery } from '@tanstack/react-query';
import { useProjectStore } from '../stores/projectStore';
import { API_BASE_URL } from '../services/apiClient';

export interface GraphNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    label: string;
    type: string;
    properties?: Record<string, any>;
  };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  animated: boolean;
  type: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export function useGraph() {
  const projectId = useProjectStore(state => state.projectId);

  const { data, isLoading, error } = useQuery<GraphData>({
    queryKey: ['knowledge_graph', projectId],
    queryFn: async () => {
      if (!projectId) throw new Error('No project selected');
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/graph`);
      if (!response.ok) {
        throw new Error('Failed to fetch knowledge graph');
      }
      const res = await response.json();
      return res.data;
    },
    enabled: !!projectId,
  });

  return {
    graphData: data,
    isLoading,
    error,
  };
}

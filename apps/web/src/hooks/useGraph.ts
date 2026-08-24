import { useQuery } from '@tanstack/react-query';

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
  const { data, isLoading, error } = useQuery<GraphData>({
    queryKey: ['knowledge_graph'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/v1/knowledge-graph');
      if (!response.ok) {
        throw new Error('Failed to fetch knowledge graph');
      }
      const res = await response.json();
      return res.data;
    },
  });

  return {
    graphData: data,
    isLoading,
    error,
  };
}

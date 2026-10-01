import { useQuery } from '@tanstack/react-query';
import { useProjectStore } from '../stores/projectStore';
import { apiClient } from '../services/apiClient';

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
  const projectId = useProjectStore(state => state.activeProjectId);
  const { data, isLoading, error } = useQuery<GraphData>({
    queryKey: ['knowledge_graph', projectId],
    enabled: Boolean(projectId),
    queryFn: async () => {
      const body = await apiClient.get<any>(`/projects/${projectId}/graph/`);
      const graph = body.data ?? body;
      return {
        nodes: (graph.nodes ?? []).map((node: any, index: number) => ({
          id: node.id,
          type: 'customNode',
          position: { x: 120 + (index % 3) * 250, y: 100 + Math.floor(index / 3) * 180 },
          data: { label: node.label, type: node.type, properties: node.properties ?? {} },
        })),
        edges: (graph.edges ?? []).map((edge: any) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          label: edge.relation,
          animated: false,
          type: 'smoothstep',
        })),
      } as GraphData;
    },
  });

  return {
    graphData: data,
    isLoading,
    error,
  };
}

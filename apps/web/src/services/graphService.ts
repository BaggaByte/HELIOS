import { apiClient } from './apiClient';

export type NodeType = 'Host' | 'Service' | 'Vulnerability' | 'User' | 'Domain';

export interface GraphNode {
  id: string;
  type: NodeType;
  label: string;
  properties: Record<string, any>;
  // UI Coordinates (managed by frontend, not backend)
  x?: number;
  y?: number;
}

export interface GraphEdge {
  id: string;
  source: string; // Node ID
  target: string; // Node ID
  label: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export const graphService = {
  /**
   * Fetches the complete intelligence graph.
   */
  async getGraph(projectId: string): Promise<GraphData> {
    const res = await apiClient.get<any>(`/knowledge-graph?project_id=${projectId}`);
    return res.data || res;
  },
  
  /**
   * Query the graph using Cypher.
   */
  async queryGraph(query: string): Promise<GraphData> {
    const res = await apiClient.post<any>(`/knowledge-graph/query`, { query });
    return res.data || res;
  }
};

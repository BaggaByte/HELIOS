import { apiClient } from './apiClient';

export interface ReconService {
  port: number;
  protocol: string;
  state: string;
  name?: string;
  version?: string;
}

export interface ReconHost {
  id: string;
  ip: string;
  hostname?: string;
  os?: string;
  status: string;
  last_seen: string;
  services: ReconService[];
  _enriched?: {
    attack_surface: {
      exposed_high_value_ports: number[];
      potential_web_services: number[];
      outdated_services: string[];
    };
    risk: {
      risk_score: number;
      severity: string;
    };
  };
}

export interface PluginExecuteResponse {
  plugin: string;
  version: string;
  result: any;
}

export const reconService = {
  /**
   * Fetches all known hosts from the database.
   * Assuming the API endpoint is GET /api/v1/recon/hosts (Needs to be added to backend)
   */
  async getHosts(projectId: string): Promise<ReconHost[]> {
    const url = `/projects/${projectId}/recon/hosts`;
    const response = await apiClient.get<any>(url);
    const hosts = response.hosts || response || [];
    if (hosts.length === 0) {
      throw new Error("Database is empty, fallback to mock data");
    }
    return hosts;
  },

  /**
   * Triggers a plugin execution dynamically.
   */
  async triggerPlugin(projectId: string, pluginName: string, payload: any): Promise<PluginExecuteResponse> {
    return await apiClient.post<PluginExecuteResponse>(`/projects/${projectId}/recon/plugins/${pluginName}`, {
      payload
    });
  }
};

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
  ipv6?: string;
  hostname?: string;
  os?: string;
  last_seen?: string;
  created_at?: string;
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

export interface NmapIngestResponse {
  status: string;
  project_id: string;
  project_name: string;
  hosts_created: number;
  hosts_updated: number;
  services_created: number;
  services_updated: number;
  total_hosts_in_file: number;
  message: string;
}

export const reconService = {
  /**
   * Fetches all known hosts from the database.
   * Fetches persisted hosts for the selected project.
   */
  async getHosts(projectId: string): Promise<ReconHost[]> {
    const url = `/projects/${projectId}/recon/hosts`;
    const response = await apiClient.get<{ hosts: ReconHost[] }>(url);
    return response.hosts;
  },

  async ingestNmapXml(projectId: string, file: File): Promise<NmapIngestResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return await apiClient.post<NmapIngestResponse>(`/projects/${projectId}/recon/ingest/nmap`, formData);
  },

  /**
   * Triggers a plugin execution dynamically.
   */
  async triggerPlugin(projectId: string, pluginName: string, target: string): Promise<PluginExecuteResponse> {
    return apiClient.post<PluginExecuteResponse>(`/projects/${projectId}/recon/plugins/${pluginName}`, {
      payload: { target },
    });
  }
};

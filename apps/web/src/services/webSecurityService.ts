import { apiClient } from './apiClient';
import type { PluginExecuteResponse } from './reconService';

export interface WebFinding {
  id: string;
  url: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'OPTIONS' | 'HEAD';
  vulnerability_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  description: string;
  request_headers?: string;
  request_body?: string;
  response_headers?: string;
  response_body?: string;
  discovered_at: string;
}

export const webSecurityService = {
  /**
   * Fetches all known web findings from the database.
   */
  async getFindings(projectId: string): Promise<WebFinding[]> {
    const url = projectId === 'default-project-id' ? '/web/findings' : `/web/findings?project_id=${projectId}`;
    const response = await apiClient.get<any>(url);
    const findings = response.findings || response || [];
    if (findings.length === 0) {
      throw new Error("Database is empty, fallback to mock data");
    }
    return findings;
  },

  /**
   * Triggers a web vulnerability scan (e.g. via nuclei plugin).
   */
  async triggerScan(targetUrl: string): Promise<PluginExecuteResponse> {
    return await apiClient.post<PluginExecuteResponse>(`/recon/plugins/nuclei`, {
      payload: {
        target: targetUrl
      }
    });
  }
};

import { apiClient } from './apiClient';

export interface Project {
  id: string;
  name: string;
  description?: string | null;
  scope: string;
  out_of_scope?: string | null;
  status: string;
  created_at: string;
}

export interface CreateProjectInput {
  name: string;
  scope: string;
  description?: string;
  out_of_scope?: string;
}

export const projectService = {
  list: () => apiClient.get<Project[]>('/projects'),
  create: (project: CreateProjectInput) => apiClient.post<Project>('/projects', project),
  updateScope: (projectId: string, scope: { scope: string, out_of_scope?: string }) => apiClient.post<Project>(`/projects/${projectId}/scope`, scope),
};

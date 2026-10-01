import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useProjectStore } from '../stores/projectStore';
import { apiClient } from '../services/apiClient';

export interface WebFinding {
  id: string;
  title: string;
  description: string;
  severity: string;
  confidence: string;
  status: string;
  cwe_id?: string;
  remediation?: string;
  impact?: string;
  references?: string[];
  created_at: string;
}

export function useWebSecurity() {
  const queryClient = useQueryClient();
  const projectId = useProjectStore(state => state.activeProjectId);

  const { data: findings, isLoading, error, refetch } = useQuery<WebFinding[]>({
    queryKey: ['web_findings', projectId],
    enabled: Boolean(projectId),
    queryFn: async () => {
      return await apiClient.get<WebFinding[]>(`/projects/${projectId}/web-security/findings`);
    },
  });

  const uploadZapMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!projectId) throw new Error('Create or select a project before importing a report.');
      const formData = new FormData();
      formData.append('file', file);
      return await apiClient.post<any>(`/projects/${projectId}/web-security/ingest/zap`, formData);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['web_findings', projectId] }),
  });

  return {
    findings,
    isLoading,
    error,
    refetch,
    uploadZap: uploadZapMutation.mutateAsync,
    isUploading: uploadZapMutation.isPending,
    uploadError: uploadZapMutation.error,
  };
}

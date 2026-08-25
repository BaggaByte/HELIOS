import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useProjectStore } from '../stores/projectStore';
import { API_BASE_URL } from '../services/apiClient';

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
  const projectId = useProjectStore(state => state.projectId);

  const { data: findings, isLoading, error } = useQuery<WebFinding[]>({
    queryKey: ['web_findings', projectId],
    queryFn: async () => {
      if (!projectId) throw new Error('No project selected');
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/web-security/findings`);
      if (!response.ok) {
        throw new Error('Failed to fetch findings');
      }
      return response.json();
    },
    enabled: !!projectId,
  });

  const uploadZapMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!projectId) throw new Error('No project selected');
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/web-security/ingest/zap`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Failed to upload ZAP file');
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['web_findings'] });
    },
  });

  return {
    findings,
    isLoading,
    error,
    uploadZap: uploadZapMutation.mutateAsync,
    isUploading: uploadZapMutation.isPending,
    uploadError: uploadZapMutation.error,
  };
}

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

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

  const { data: findings, isLoading, error } = useQuery<WebFinding[]>({
    queryKey: ['web_findings'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/v1/web/findings');
      if (!response.ok) {
        throw new Error('Failed to fetch findings');
      }
      return response.json();
    },
  });

  const uploadZapMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/api/v1/web/ingest/zap', {
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

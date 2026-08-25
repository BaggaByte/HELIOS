import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useProjectStore } from '../stores/projectStore';
import { API_BASE_URL } from '../services/apiClient';

export interface Evidence {
  id: string;
  type: string;
  description: string;
  file_hash: string;
  original_filename: string;
  created_at: string;
}

export function useEvidence() {
  const queryClient = useQueryClient();
  const projectId = useProjectStore(state => state.projectId);

  const { data: evidenceList, isLoading, error } = useQuery<Evidence[]>({
    queryKey: ['evidence', projectId],
    queryFn: async () => {
      if (!projectId) throw new Error('No project selected');
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/evidence`);
      if (!response.ok) throw new Error('Failed to fetch evidence');
      const res = await response.json();
      return res.data;
    },
    enabled: !!projectId,
  });

  const uploadMutation = useMutation({
    mutationFn: async ({ file, description, type }: { file: File; description?: string; type: string }) => {
      if (!projectId) throw new Error('No project selected');
      const formData = new FormData();
      formData.append('file', file);
      if (description) formData.append('description', description);
      formData.append('type', type);

      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/evidence/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Failed to upload evidence');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence'] });
    },
  });

  const verifyMutation = useMutation({
    mutationFn: async (id: string) => {
      if (!projectId) throw new Error('No project selected');
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/evidence/${id}/verify`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to verify evidence');
      const res = await response.json();
      return res.data as { valid: boolean; current_hash: string; expected_hash: string; error?: string };
    },
  });

  return {
    evidenceList,
    isLoading,
    error,
    uploadEvidence: uploadMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
    verifyEvidence: verifyMutation.mutateAsync,
  };
}

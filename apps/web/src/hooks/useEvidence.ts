import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useProjectStore } from '../stores/projectStore';
import { apiClient } from '../services/apiClient';

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
  const projectId = useProjectStore(state => state.activeProjectId);

  const { data: evidenceList, isLoading, error, refetch } = useQuery<Evidence[]>({
    queryKey: ['evidence', projectId],
    enabled: Boolean(projectId),
    queryFn: async () => {
      const res = await apiClient.get<any>(`/projects/${projectId}/evidence/`);
      return res.data ?? [];
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async ({ file, description, type }: { file: File; description?: string; type: string }) => {
      if (!projectId) throw new Error('Create or select a project before uploading evidence.');
      const formData = new FormData();
      formData.append('file', file);
      if (description) formData.append('description', description);
      formData.append('type', type);

      return await apiClient.post<any>(`/projects/${projectId}/evidence/upload`, formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence', projectId] });
    },
  });

  const verifyMutation = useMutation({
    mutationFn: async (id: string) => {
      if (!projectId) throw new Error('Select a project to verify evidence.');
      const res = await apiClient.post<any>(`/projects/${projectId}/evidence/${id}/verify`, {});
      return res.data as { valid: boolean; current_hash: string; expected_hash: string; error?: string };
    },
  });

  return {
    evidenceList,
    isLoading,
    error,
    refetch,
    uploadEvidence: uploadMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
    verifyEvidence: verifyMutation.mutateAsync,
  };
}

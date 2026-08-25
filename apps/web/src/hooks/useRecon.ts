import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useProjectStore } from '../stores/projectStore';
import { API_BASE_URL } from '../services/apiClient';

export interface ReconService {
  id: string;
  port: number;
  protocol: string;
  name?: string;
  version?: string;
  state: string;
}

export interface ReconHost {
  id: string;
  ip: string;
  hostname?: string;
  os?: string;
  services: ReconService[];
}

export function useRecon() {
  const queryClient = useQueryClient();
  const projectId = useProjectStore(state => state.projectId);

  const { data: hosts, isLoading, error } = useQuery<ReconHost[]>({
    queryKey: ['recon_hosts', projectId],
    queryFn: async () => {
      if (!projectId) throw new Error('No project selected');
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/recon/hosts`);
      if (!response.ok) {
        throw new Error('Failed to fetch hosts');
      }
      return response.json();
    },
    enabled: !!projectId,
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!projectId) throw new Error('No project selected');
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/recon/ingest/nmap`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Failed to upload nmap file');
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recon_hosts'] });
    },
  });

  return {
    hosts,
    isLoading,
    error,
    uploadNmap: uploadMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
    uploadError: uploadMutation.error,
  };
}

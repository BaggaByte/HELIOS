import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useProjectStore } from '../stores/projectStore';
import { apiClient } from '../services/apiClient';

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
  const projectId = useProjectStore(state => state.activeProjectId);

  const { data, isLoading, error, refetch } = useQuery<{ hosts: ReconHost[] }>({
    queryKey: ['recon_hosts', projectId],
    enabled: Boolean(projectId),
    queryFn: async () => {
      return await apiClient.get<{ hosts: ReconHost[] }>(`/projects/${projectId}/recon/hosts`);
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);

      return await apiClient.post<any>(`/projects/${projectId}/recon/ingest/nmap`, formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recon_hosts', projectId] });
    },
  });

  return {
    hosts: data?.hosts ?? [],
    isLoading,
    error,
    refetch,
    uploadNmap: uploadMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
    uploadError: uploadMutation.error,
  };
}

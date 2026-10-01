import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useProjectStore } from '../stores/projectStore';
import { apiClient } from '../services/apiClient';

export interface LogEvent {
  id: string;
  timestamp: string;
  source: string;
  event_type: string;
  severity: string;
  message: string;
  source_ip?: string;
  dest_ip?: string;
  metadata?: Record<string, any>;
}

export interface TimelineResponse {
  events: LogEvent[];
  page: number;
  limit: number;
}

export function useLogs() {
  const queryClient = useQueryClient();
  const projectId = useProjectStore(state => state.activeProjectId);
  const [page, setPage] = useState(1);
  const [severityFilter, setSeverityFilter] = useState<string | null>(null);
  const [sourceFilter, setSourceFilter] = useState<string | null>(null);

  const { data, isLoading, error, refetch } = useQuery<TimelineResponse>({
    queryKey: ['log_timeline', projectId, page, severityFilter, sourceFilter],
    enabled: Boolean(projectId),
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '100', // Load 100 at a time for the feed
      });
      if (severityFilter) params.append('severity', severityFilter);
      if (sourceFilter) params.append('source', sourceFilter);

      return await apiClient.get<TimelineResponse>(`/projects/${projectId}/logs/timeline?${params.toString()}`);
    },
  });

  const ingestLogsMutation = useMutation({
    mutationFn: async ({ file, type }: { file: File, type: string }) => {
      if (!projectId) throw new Error('Create or select a project before importing logs.');
      const formData = new FormData();
      formData.append('file', file);
      formData.append('log_type', type);

      return await apiClient.post<any>(`/projects/${projectId}/logs/ingest`, formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['log_timeline', projectId] });
      setPage(1); // Reset to newest on new ingest
    },
  });

  return {
    events: data?.events || [],
    isLoading,
    error,
    refetch,
    page,
    setPage,
    severityFilter,
    setSeverityFilter,
    sourceFilter,
    setSourceFilter,
    ingestLogs: ingestLogsMutation.mutateAsync,
    isIngesting: ingestLogsMutation.isPending,
    ingestError: ingestLogsMutation.error,
  };
}

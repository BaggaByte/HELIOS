import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

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
  const [page, setPage] = useState(1);
  const [severityFilter, setSeverityFilter] = useState<string | null>(null);
  const [sourceFilter, setSourceFilter] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery<TimelineResponse>({
    queryKey: ['log_timeline', page, severityFilter, sourceFilter],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '100', // Load 100 at a time for the feed
      });
      if (severityFilter) params.append('severity', severityFilter);
      if (sourceFilter) params.append('source', sourceFilter);

      const response = await fetch(`http://localhost:8000/api/v1/logs/timeline?${params.toString()}`);
      if (!response.ok) {
        throw new Error('Failed to fetch timeline');
      }
      return response.json();
    },
  });

  const ingestLogsMutation = useMutation({
    mutationFn: async ({ file, type }: { file: File, type: string }) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('log_type', type);

      const response = await fetch('http://localhost:8000/api/v1/logs/ingest', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Failed to ingest log file');
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['log_timeline'] });
      setPage(1); // Reset to newest on new ingest
    },
  });

  return {
    events: data?.events || [],
    isLoading,
    error,
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

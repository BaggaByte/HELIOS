import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { useProjectStore } from '../stores/projectStore';
import { apiClient } from '../services/apiClient';

export function useReports() {
  const [reportMarkdown, setReportMarkdown] = useState<string | null>(null);
  const projectId = useProjectStore(state => state.activeProjectId);

  const generateMutation = useMutation({
    mutationFn: async ({ includeAiSummary }: { includeAiSummary: boolean }) => {
      if (!projectId) throw new Error('Create or select a project before generating a report.');
      try {
        const result = await apiClient.post<any>(`/projects/${projectId}/reports/generate?include_ai_summary=${includeAiSummary}`, {});
        if (typeof result.data?.markdown !== 'string') throw new Error('The server returned an empty report.');
        return result.data.markdown as string;
      } catch (err: any) {
        throw new Error(err?.response?.data?.detail || err.message || 'Report generation failed');
      }
    },
    onSuccess: setReportMarkdown,
  });

  const downloadReport = () => {
    if (!reportMarkdown) return;
    const blob = new Blob([reportMarkdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `helios_report_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  return {
    reportMarkdown,
    generateReport: generateMutation.mutateAsync,
    isGenerating: generateMutation.isPending,
    error: generateMutation.error,
    downloadReport,
  };
}

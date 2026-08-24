import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';

export function useReports() {
  const [reportMarkdown, setReportMarkdown] = useState<string | null>(null);

  const generateMutation = useMutation({
    mutationFn: async ({ includeAiSummary, projectId }: { includeAiSummary: boolean, projectId?: string }) => {
      const response = await fetch('http://localhost:8000/api/v1/reports/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          include_ai_summary: includeAiSummary,
          project_id: projectId
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => null);
        throw new Error(err?.detail || 'Failed to generate report');
      }
      
      const res = await response.json();
      return res.data.markdown as string;
    },
    onSuccess: (data) => {
      setReportMarkdown(data);
    }
  });

  const downloadReport = () => {
    if (!reportMarkdown) return;
    const blob = new Blob([reportMarkdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pentest_report_${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return {
    reportMarkdown,
    generateReport: generateMutation.mutateAsync,
    isGenerating: generateMutation.isPending,
    error: generateMutation.error,
    downloadReport
  };
}

import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { useProjectStore } from '../stores/projectStore';
import { API_BASE_URL } from '../services/apiClient';

export interface CodeVulnerability {
  title: string;
  severity: string;
  line: number;
  snippet: string;
  impact: string;
}

export interface AnalysisResult {
  status: string;
  filename: string;
  content: string;
  vulnerabilities: CodeVulnerability[];
}

export function useSourceCode() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const projectId = useProjectStore(state => state.projectId);

  const analyzeCodeMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!projectId) throw new Error('No project selected');
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/source-code/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || 'Failed to analyze source code file');
      }

      return response.json() as Promise<AnalysisResult>;
    },
    onSuccess: (data) => {
      setAnalysisResult(data);
    },
  });

  return {
    analysisResult,
    analyzeCode: analyzeCodeMutation.mutateAsync,
    isAnalyzing: analyzeCodeMutation.isPending,
    error: analyzeCodeMutation.error,
    clearAnalysis: () => setAnalysisResult(null),
  };
}

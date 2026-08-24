import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';

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

  const analyzeCodeMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/api/v1/source-code/analyze', {
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

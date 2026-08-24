import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';

export interface JsAnalysisResult {
  status: string;
  beautified_code: string;
  findings: {
    endpoints: string[];
    tokens: Array<{
      type: string;
      value: string;
    }>;
  };
}

export function useJsIntel() {
  const [analysisResult, setAnalysisResult] = useState<JsAnalysisResult | null>(null);

  const analyzeCodeMutation = useMutation({
    mutationFn: async (code: string) => {
      const response = await fetch('http://localhost:8000/api/v1/js-intel/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });
      if (!response.ok) throw new Error('Failed to analyze code');
      return response.json() as Promise<JsAnalysisResult>;
    },
    onSuccess: (data) => {
      setAnalysisResult(data);
    },
  });

  const analyzeFileMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch('http://localhost:8000/api/v1/js-intel/analyze-file', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Failed to analyze file');
      return response.json() as Promise<JsAnalysisResult>;
    },
    onSuccess: (data) => {
      setAnalysisResult(data);
    },
  });

  return {
    analysisResult,
    analyzeCode: analyzeCodeMutation.mutateAsync,
    analyzeFile: analyzeFileMutation.mutateAsync,
    isAnalyzing: analyzeCodeMutation.isPending || analyzeFileMutation.isPending,
    error: analyzeCodeMutation.error || analyzeFileMutation.error,
  };
}

import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { useProjectStore } from '../stores/projectStore';
import { API_BASE_URL } from '../services/apiClient';

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
  const projectId = useProjectStore(state => state.projectId);

  const analyzeCodeMutation = useMutation({
    mutationFn: async (code: string) => {
      if (!projectId) throw new Error('No project selected');
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/js-intel/analyze`, {
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
      
      if (!projectId) throw new Error('No project selected');
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/js-intel/analyze-file`, {
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

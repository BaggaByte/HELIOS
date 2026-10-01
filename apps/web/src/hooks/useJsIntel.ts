import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { apiClient } from '../services/apiClient';
import { useProjectStore } from '../stores/projectStore';

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
  const projectId = useProjectStore(state => state.activeProjectId);

  const analyzeCodeMutation = useMutation({
    mutationFn: async (code: string) => {
      if (!projectId) throw new Error('Create or select a project before analyzing JavaScript.');
      return await apiClient.post<JsAnalysisResult>(`/projects/${projectId}/js-intel/analyze`, { code });
    },
    onSuccess: (data) => {
      setAnalysisResult(data);
    },
  });

  const analyzeFileMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!projectId) throw new Error('Create or select a project before analyzing JavaScript.');
      const formData = new FormData();
      formData.append('file', file);
      
      return await apiClient.post<JsAnalysisResult>(`/projects/${projectId}/js-intel/analyze-file`, formData);
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

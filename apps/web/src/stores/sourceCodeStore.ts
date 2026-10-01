import { create } from 'zustand';
import { sourceCodeService, type AnalyzedFile } from '../services/sourceCodeService';

interface SourceCodeState {
  analyzedFiles: AnalyzedFile[];
  selectedFileId: string | null;
  isLoading: boolean;
  isAnalyzing: boolean;
  error: string | null;
  fetchAnalyzedFiles: (projectId: string) => Promise<void>;
  analyzeSnippet: (projectId: string, code: string, language: string, filename?: string) => Promise<void>;
  selectFile: (id: string | null) => void;
}

export const useSourceCodeStore = create<SourceCodeState>((set) => ({
  analyzedFiles: [],
  selectedFileId: null,
  isLoading: false,
  isAnalyzing: false,
  error: null,

  fetchAnalyzedFiles: async (projectId) => {
    set({ isLoading: true, error: null });
    try {
      const files = await sourceCodeService.getAnalyzedFiles(projectId);
      set({ analyzedFiles: files, selectedFileId: files[0]?.id ?? null, isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Could not load source findings', isLoading: false });
    }
  },

  analyzeSnippet: async (projectId, code, language, filename = 'snippet.py') => {
    set({ isAnalyzing: true, error: null });
    try {
      const result = await sourceCodeService.analyzeSnippet(projectId, code, language, filename);
      set(state => ({ analyzedFiles: [result, ...state.analyzedFiles], selectedFileId: result.id, isAnalyzing: false }));
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Source analysis failed', isAnalyzing: false });
    }
  },

  selectFile: (id) => set({ selectedFileId: id }),
}));

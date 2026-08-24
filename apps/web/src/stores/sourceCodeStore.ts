import { create } from 'zustand';
import { sourceCodeService, type AnalyzedFile } from '../services/sourceCodeService';

interface SourceCodeState {
  analyzedFiles: AnalyzedFile[];
  selectedFileId: string | null;
  isLoading: boolean;
  isAnalyzing: boolean;
  error: string | null;
  
  // Actions
  fetchAnalyzedFiles: (projectId: string) => Promise<void>;
  analyzeSnippet: (code: string, language: string, filename?: string) => Promise<void>;
  selectFile: (id: string | null) => void;
}

export const useSourceCodeStore = create<SourceCodeState>((set) => ({
  analyzedFiles: [],
  selectedFileId: null,
  isLoading: false,
  isAnalyzing: false,
  error: null,

  fetchAnalyzedFiles: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const files = await sourceCodeService.getAnalyzedFiles(projectId);
      set({ analyzedFiles: files, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  analyzeSnippet: async (code: string, language: string, filename: string = 'snippet.py') => {
    set({ isAnalyzing: true, error: null });
    try {
      const newFile = await sourceCodeService.analyzeSnippet(code, language, filename);
      set((state) => ({ 
        analyzedFiles: [newFile, ...state.analyzedFiles],
        selectedFileId: newFile.id,
        isAnalyzing: false 
      }));
    } catch (error: any) {
      set({ error: error.message, isAnalyzing: false });
    }
  },

  selectFile: (id) => set({ selectedFileId: id }),
}));

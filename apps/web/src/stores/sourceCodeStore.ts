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

const mockPythonCode = `import os
import subprocess
import pickle

class VulnApp:
    def __init__(self):
        self.data = []
        
    @app.route('/exec')
    def execute_command(self, user_input):
        # Danger: eval
        result = eval(user_input)
        
        # Danger: system
        os.system(f"echo {user_input}")
        
        # Danger: Popen
        subprocess.Popen(user_input, shell=True)
        
        return result

    def load_data(self, payload):
        # Danger: insecure deserialization
        return pickle.loads(payload)
`;

export const useSourceCodeStore = create<SourceCodeState>((set) => ({
  analyzedFiles: [],
  selectedFileId: null,
  isLoading: false,
  isAnalyzing: false,
  error: null,

  fetchAnalyzedFiles: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      // Mock data representing the output of the PythonASTVisitor we built earlier
      const files = await sourceCodeService.getAnalyzedFiles(projectId).catch(() => [
        {
          id: 'mock-file-1',
          filename: 'vuln_app.py',
          language: 'python',
          code: mockPythonCode,
          imports: ['os', 'subprocess', 'pickle'],
          functions: [
            { name: '__init__', line: 6, decorators: [] },
            { name: 'execute_command', line: 10, decorators: ["@app.route('/exec')"] },
            { name: 'load_data', line: 22, decorators: [] }
          ],
          classes: ['VulnApp'],
          security_findings: [
            { type: 'VULNERABILITY', severity: 'HIGH' as const, line: 12, description: 'Code execution via eval()' },
            { type: 'VULNERABILITY', severity: 'HIGH' as const, line: 15, description: 'Command injection via os.system()' },
            { type: 'VULNERABILITY', severity: 'HIGH' as const, line: 18, description: 'Command injection via subprocess.Popen()' },
            { type: 'VULNERABILITY', severity: 'HIGH' as const, line: 24, description: 'Insecure deserialization via pickle.loads()' }
          ],
          analyzed_at: new Date().toISOString()
        }
      ]);
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

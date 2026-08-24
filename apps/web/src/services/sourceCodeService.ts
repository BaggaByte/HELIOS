import { apiClient } from './apiClient';

export interface CodeFinding {
  type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  line: number;
  description: string;
}

export interface CodeFunction {
  name: string;
  line: number;
  decorators: string[];
}

export interface AnalyzedFile {
  id: string;
  filename: string;
  language: string;
  code: string; // The raw source code
  imports: string[];
  functions: CodeFunction[];
  classes: string[];
  security_findings: CodeFinding[];
  analyzed_at: string;
}

export const sourceCodeService = {
  /**
   * Fetches all analyzed files for a given project.
   */
  async getAnalyzedFiles(projectId: string): Promise<AnalyzedFile[]> {
    return await apiClient.get<AnalyzedFile[]>(`/source-code/files?project_id=${projectId}`);
  },

  /**
   * Submits raw code for static analysis.
   */
  async analyzeSnippet(code: string, language: string, filename: string = 'snippet.py'): Promise<AnalyzedFile> {
    return await apiClient.post<AnalyzedFile>(`/source-code/analyze`, {
      code,
      language_hint: language,
      filename
    });
  }
};

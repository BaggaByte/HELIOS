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
    const findings = await apiClient.get<Array<{ id: string; title: string; severity: string; cwe_id?: string; created_at?: string }>>(`/projects/${projectId}/source-code/findings`);
    return findings.map(finding => ({
      id: finding.id,
      filename: finding.title,
      language: 'finding',
      code: '',
      imports: [],
      functions: [],
      classes: [],
      security_findings: [{ type: 'VULNERABILITY', severity: finding.severity.toUpperCase() as CodeFinding['severity'], line: 0, description: finding.title }],
      analyzed_at: finding.created_at ?? '',
    }));
  },

  /**
   * Submits raw code for static analysis.
   */
  async analyzeSnippet(projectId: string, code: string, language: string, filename: string = 'snippet.py'): Promise<AnalyzedFile> {
    const result = await apiClient.post<Omit<AnalyzedFile, 'code' | 'imports' | 'functions' | 'classes'>>(`/projects/${projectId}/source-code/analyze`, {
      code,
      language_hint: language,
      filename
    });
    return { ...result, code, imports: [], functions: [], classes: [] };
  }
};

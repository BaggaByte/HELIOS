import { create } from 'zustand';
import { webSecurityService, type WebFinding } from '../services/webSecurityService';

interface WebSecurityState {
  findings: WebFinding[];
  selectedFindingId: string | null;
  isLoading: boolean;
  isScanning: boolean;
  error: string | null;
  lastScanTarget: string | null;
  
  // Actions
  fetchFindings: (projectId: string) => Promise<void>;
  triggerScan: (targetUrl: string) => Promise<void>;
  selectFinding: (id: string | null) => void;
}

export const useWebSecurityStore = create<WebSecurityState>((set, get) => ({
  findings: [],
  selectedFindingId: null,
  isLoading: false,
  isScanning: false,
  error: null,
  lastScanTarget: null,

  fetchFindings: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      // Mock data until backend is fully wired
      const findings = await webSecurityService.getFindings(projectId).catch(() => {
        const target = get().lastScanTarget || 'https://api.example.com';
        const targetBase = target.replace(/\/+$/, ''); // remove trailing slashes
        return [
          {
            id: 'mock-web-1',
            url: `${targetBase}/v1/users`,
            method: 'GET' as const,
            vulnerability_type: 'BOLA (Broken Object Level Authorization)',
            severity: 'CRITICAL' as const,
            description: 'The endpoint does not validate if the requested user ID belongs to the authenticated user token, allowing data exfiltration of other users.',
            request_headers: `GET /v1/users/9999 HTTP/1.1\nHost: ${new URL(targetBase).hostname}\nAuthorization: Bearer eyJhbG... (User 1 token)`,
            response_headers: 'HTTP/1.1 200 OK\nContent-Type: application/json',
            response_body: '{\n  "id": 9999,\n  "email": "admin@example.com",\n  "ssn": "***-**-1234"\n}',
            discovered_at: new Date().toISOString()
          },
          {
            id: 'mock-web-2',
            url: `${targetBase}/login`,
            method: 'POST' as const,
            vulnerability_type: 'SQL Injection',
            severity: 'HIGH' as const,
            description: 'The username parameter is vulnerable to boolean-based blind SQL injection.',
            request_headers: `POST /login HTTP/1.1\nHost: ${new URL(targetBase).hostname}\nContent-Type: application/x-www-form-urlencoded`,
            request_body: 'username=admin\' OR 1=1--&password=foo',
            response_headers: 'HTTP/1.1 302 Found\nLocation: /dashboard',
            discovered_at: new Date(Date.now() - 3600000).toISOString()
          }
        ];
      });
      set({ findings, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  triggerScan: async (targetUrl: string) => {
    set({ isScanning: true, error: null, lastScanTarget: targetUrl });
    try {
      await webSecurityService.triggerScan(targetUrl);
      
      // Simulate background processing time
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Simulate discovering a new finding dynamically during the scan
      const targetBase = targetUrl.replace(/\/+$/, '');
      const newFinding: WebFinding = {
        id: `mock-web-${Date.now()}`,
        url: `${targetBase}/api/debug`,
        method: 'GET',
        vulnerability_type: 'Information Exposure',
        severity: 'MEDIUM',
        description: `A debug endpoint was discovered at ${targetBase}/api/debug that leaks sensitive internal configuration and environment variables.`,
        request_headers: `GET /api/debug HTTP/1.1\nHost: ${new URL(targetBase).hostname}`,
        response_headers: 'HTTP/1.1 200 OK\nContent-Type: application/json',
        response_body: '{\n  "status": "ok",\n  "env": "production",\n  "db_password": "super_secret_password_123"\n}',
        discovered_at: new Date().toISOString()
      };
      
      set((state) => ({ 
        findings: [newFinding, ...state.findings],
        isScanning: false,
        selectedFindingId: newFinding.id
      }));
    } catch (error: any) {
      set({ error: error.message, isScanning: false });
    }
  },

  selectFinding: (id) => set({ selectedFindingId: id }),
}));

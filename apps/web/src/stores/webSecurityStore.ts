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
      const findings = await webSecurityService.getFindings(projectId);
      set({ findings, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  triggerScan: async (targetUrl: string) => {
    set({ isScanning: true, error: null, lastScanTarget: targetUrl });
    try {
      await webSecurityService.triggerScan(targetUrl);
      set({ isScanning: false });
    } catch (error: any) {
      set({ error: error.message, isScanning: false });
    }
  },

  selectFinding: (id) => set({ selectedFindingId: id }),
}));

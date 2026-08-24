import { create } from 'zustand';
import { reconService, type ReconHost } from '../services/reconService';

interface ReconState {
  hosts: ReconHost[];
  isLoading: boolean;
  isScanning: boolean;
  error: string | null;
  activeProjectId: string | null;
  
  // Actions
  fetchHosts: (projectId: string) => Promise<void>;
  triggerScan: (plugin: string, target: string, args?: string) => Promise<void>;
}

export const useReconStore = create<ReconState>((set, get) => ({
  hosts: [],
  isLoading: false,
  isScanning: false,
  error: null,
  activeProjectId: null,

  fetchHosts: async (projectId: string) => {
    set({ isLoading: true, error: null, activeProjectId: projectId });
    try {
      const hosts = await reconService.getHosts(projectId);
      set({ hosts, isLoading: false });
    } catch (error: any) {
      set({ error: error.message, isLoading: false });
    }
  },

  triggerScan: async (plugin: string, target: string, args: string = "-sV -O") => {
    const projectId = get().activeProjectId;
    if (!projectId) {
      set({ error: "No active project selected", isScanning: false });
      return;
    }
    
    set({ isScanning: true, error: null });
    try {
      await reconService.triggerPlugin(projectId, plugin, {
        target,
        args
      });
      
      await get().fetchHosts(projectId);
      set({ isScanning: false });
    } catch (error: any) {
      set({ error: error.message, isScanning: false });
    }
  }
}));

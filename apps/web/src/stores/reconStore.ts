import { create } from 'zustand';
import { reconService, type ReconHost } from '../services/reconService';

interface ReconState {
  hosts: ReconHost[];
  isLoading: boolean;
  isScanning: boolean;
  isImporting: boolean;
  error: string | null;
  activeProjectId: string | null;
  lastMessage: string | null;
  fetchHosts: (projectId: string) => Promise<void>;
  triggerScan: (plugin: string, target: string) => Promise<void>;
  importNmapFile: (file: File) => Promise<void>;
}

export const useReconStore = create<ReconState>((set, get) => ({
  hosts: [],
  isLoading: false,
  isScanning: false,
  isImporting: false,
  error: null,
  activeProjectId: null,
  lastMessage: null,

  fetchHosts: async (projectId) => {
    if (get().activeProjectId !== projectId) set({ hosts: [], activeProjectId: projectId });
    set({ isLoading: true, error: null });
    try {
      const hosts = await reconService.getHosts(projectId);
      if (get().activeProjectId === projectId) set({ hosts, isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Could not load hosts', isLoading: false });
    }
  },

  triggerScan: async (plugin, target) => {
    const projectId = get().activeProjectId;
    if (!projectId) {
      set({ error: 'Create or select a project before scanning.', isScanning: false });
      return;
    }
    set({ isScanning: true, error: null, lastMessage: null });
    try {
      const response = await reconService.triggerPlugin(projectId, plugin, target);
      await get().fetchHosts(projectId);
      set({ lastMessage: `Scan completed. ${response.result.hosts_found ?? 0} host(s) found.` });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Scan failed' });
    } finally {
      set({ isScanning: false });
    }
  },

  importNmapFile: async (file) => {
    const projectId = get().activeProjectId;
    if (!projectId) {
      set({ error: 'Create or select a project before importing scan results.' });
      return;
    }
    set({ isImporting: true, error: null, lastMessage: null });
    try {
      const result = await reconService.ingestNmapXml(projectId, file);
      await get().fetchHosts(projectId);
      set({ lastMessage: result.message });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Nmap import failed' });
    } finally {
      set({ isImporting: false });
    }
  },
}));

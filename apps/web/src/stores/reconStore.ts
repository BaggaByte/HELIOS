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
      // Temporary mock data until the backend GET /hosts endpoint is implemented
      const hosts = await reconService.getHosts(projectId).catch(() => [
        {
          id: 'mock-1',
          ip: '192.168.1.10',
          hostname: 'prod-db.internal',
          os: 'Linux 5.4',
          status: 'up',
          last_seen: new Date().toISOString(),
          services: [
            { port: 22, protocol: 'tcp', state: 'open', name: 'ssh', version: 'OpenSSH 8.2p1' },
            { port: 5432, protocol: 'tcp', state: 'open', name: 'postgresql', version: 'PostgreSQL 12' }
          ],
          _enriched: {
            attack_surface: {
              exposed_high_value_ports: [22, 5432],
              potential_web_services: [],
              outdated_services: []
            },
            risk: {
              risk_score: 3.5,
              severity: 'Low'
            }
          }
        },
        {
          id: 'mock-2',
          ip: '192.168.1.15',
          hostname: 'web-front',
          os: 'Windows Server',
          status: 'up',
          last_seen: new Date().toISOString(),
          services: [
            { port: 80, protocol: 'tcp', state: 'open', name: 'http', version: 'IIS 6' },
            { port: 443, protocol: 'tcp', state: 'open', name: 'https' },
            { port: 3389, protocol: 'tcp', state: 'open', name: 'ms-wbt-server' }
          ],
          _enriched: {
            attack_surface: {
              exposed_high_value_ports: [3389],
              potential_web_services: [80, 443],
              outdated_services: ['http (iis 6)']
            },
            risk: {
              risk_score: 9.0,
              severity: 'Critical'
            }
          }
        }
      ]);
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
      
      // Simulate background processing time
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Simulate discovering the target dynamically during the scan
      const newHost: ReconHost = {
        id: `mock-${Date.now()}`,
        ip: target.replace(/[^0-9.]/g, '') || '10.0.0.42',
        hostname: `scanned-${target.replace(/[^a-zA-Z0-9-]/g, '') || 'target'}`,
        os: 'Unknown Linux',
        status: 'up',
        last_seen: new Date().toISOString(),
        services: [
          { port: 8080, protocol: 'tcp', state: 'open', name: 'http', version: 'nginx/1.21.0' },
          { port: 22, protocol: 'tcp', state: 'open', name: 'ssh', version: 'OpenSSH 8.4' }
        ],
        _enriched: {
          attack_surface: {
            exposed_high_value_ports: [22],
            potential_web_services: [8080],
            outdated_services: []
          },
          risk: {
            risk_score: 4.5,
            severity: 'Medium'
          }
        }
      };
      
      set((state) => ({ 
        hosts: [newHost, ...state.hosts],
        isScanning: false 
      }));
    } catch (error: any) {
      set({ error: error.message, isScanning: false });
    }
  }
}));

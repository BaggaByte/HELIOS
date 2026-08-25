import { create } from 'zustand';
import { apiClient } from '../services/apiClient';

interface Project {
  id: string;
  name: string;
  description: string;
  scope: string;
  out_of_scope: string;
  status: string;
  created_at: string;
}

interface ProjectStore {
  projectId: string | null;
  isInitializing: boolean;
  error: string | null;
  initialize: () => Promise<void>;
  setProjectId: (id: string) => void;
}

export const useProjectStore = create<ProjectStore>((set, get) => ({
  projectId: null,
  isInitializing: true,
  error: null,
  
  setProjectId: (id: string) => set({ projectId: id }),

  initialize: async () => {
    // If already initialized and we have a project, skip
    if (get().projectId) {
      set({ isInitializing: false });
      return;
    }

    set({ isInitializing: true, error: null });
    
    try {
      // 1. Fetch existing projects
      const projects = await apiClient.get<Project[]>('/projects');
      
      if (projects && projects.length > 0) {
        // 2a. Use the first one
        set({ projectId: projects[0].id, isInitializing: false });
      } else {
        // 2b. If no projects, create a default one
        const defaultProject = await apiClient.post<Project>('/projects', {
          name: 'Default Project',
          description: 'Auto-generated default project',
          scope: '*',
          out_of_scope: ''
        });
        set({ projectId: defaultProject.id, isInitializing: false });
      }
    } catch (err: any) {
      console.error('Failed to initialize project:', err);
      set({ error: err.message || 'Failed to initialize project', isInitializing: false });
    }
  }
}));

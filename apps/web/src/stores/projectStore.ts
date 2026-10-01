import { create } from 'zustand';
import { projectService, type CreateProjectInput, type Project } from '../services/projectService';

const ACTIVE_PROJECT_KEY = 'helios.activeProjectId';

interface ProjectState {
  projects: Project[];
  activeProjectId: string | null;
  isLoading: boolean;
  error: string | null;
  loadProjects: () => Promise<void>;
  createProject: (input: CreateProjectInput) => Promise<Project>;
  setActiveProject: (projectId: string) => void;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  activeProjectId: localStorage.getItem(ACTIVE_PROJECT_KEY),
  isLoading: false,
  error: null,

  loadProjects: async () => {
    set({ isLoading: true, error: null });
    try {
      const projects = await projectService.list();
      const selected = projects.some(project => project.id === get().activeProjectId)
        ? get().activeProjectId
        : projects[0]?.id ?? null;
      if (selected) localStorage.setItem(ACTIVE_PROJECT_KEY, selected);
      else localStorage.removeItem(ACTIVE_PROJECT_KEY);
      set({ projects, activeProjectId: selected, isLoading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Could not load projects', isLoading: false });
    }
  },

  createProject: async (input) => {
    const project = await projectService.create(input);
    localStorage.setItem(ACTIVE_PROJECT_KEY, project.id);
    set(state => ({ projects: [project, ...state.projects], activeProjectId: project.id, error: null }));
    return project;
  },

  setActiveProject: (projectId) => {
    localStorage.setItem(ACTIVE_PROJECT_KEY, projectId);
    set({ activeProjectId: projectId });
  },
}));

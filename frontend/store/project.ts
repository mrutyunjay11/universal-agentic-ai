import { create } from "zustand";

export interface Project {
  project_id: string;
  name: string;
  root_path: string;
  language?: string;
  framework?: string;
  indexed: boolean;
  file_count: number;
}

export interface FileEntry {
  name: string;
  path: string;
  type: "file" | "directory";
  size: number;
  modified: string;
}

interface ProjectState {
  projects: Project[];
  activeProjectId: string | null;
  activeFile: { path: string; content: string } | null;
  openFiles: string[];
  fileTree: FileEntry[];
  setProjects: (projects: Project[]) => void;
  setActiveProject: (id: string | null) => void;
  setActiveFile: (file: { path: string; content: string } | null) => void;
  addOpenFile: (path: string) => void;
  removeOpenFile: (path: string) => void;
  setFileTree: (entries: FileEntry[]) => void;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  activeProjectId: null,
  activeFile: null,
  openFiles: [],
  fileTree: [],

  setProjects: (projects) => set({ projects }),

  setActiveProject: (id) => {
    set({ activeProjectId: id });
  },

  setActiveFile: (file) => {
    if (file) {
      const { openFiles } = get();
      if (!openFiles.includes(file.path)) {
        set({ openFiles: [...openFiles, file.path] });
      }
    }
    set({ activeFile: file });
  },

  addOpenFile: (path) => {
    const { openFiles } = get();
    if (!openFiles.includes(path)) {
      set({ openFiles: [...openFiles, path] });
    }
  },

  removeOpenFile: (path) => {
    set((state) => ({
      openFiles: state.openFiles.filter((p) => p !== path),
      activeFile: state.activeFile?.path === path ? null : state.activeFile,
    }));
  },

  setFileTree: (entries) => set({ fileTree: entries }),
}));

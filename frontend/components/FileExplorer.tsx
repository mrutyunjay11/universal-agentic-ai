"use client";

import { useEffect, useState, useCallback } from "react";
import { useProjectStore, FileEntry } from "@/store/project";
import { useUIStore } from "@/store/ui";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function FileExplorer() {
  const fileTree = useProjectStore((s) => s.fileTree);
  const setFileTree = useProjectStore((s) => s.setFileTree);
  const setActiveFile = useProjectStore((s) => s.setActiveFile);
  const projects = useProjectStore((s) => s.projects);
  const activeProjectId = useProjectStore((s) => s.activeProjectId);
  const setActiveProject = useProjectStore((s) => s.setActiveProject);
  const setShowDiffViewer = useUIStore((s) => s.setShowDiffViewer);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);

  const activeProject = projects.find((p) => p.project_id === activeProjectId);

  useEffect(() => {
    fetch(`${API}/api/projects`)
      .then((r) => r.json())
      .then((data) => {
        const projects = Array.isArray(data) ? data : [];
        useProjectStore.getState().setProjects(projects);
        if (projects.length > 0 && !activeProjectId) {
          useProjectStore.getState().setActiveProject(projects[0].project_id);
        }
      })
      .catch(() => {});
  }, [activeProjectId]);

  const loadDirectory = useCallback(
    async (dirPath: string) => {
      if (!activeProject) return;
      setLoading(true);
      try {
        const res = await fetch(
          `${API}/api/files/list?dir_path=${encodeURIComponent(dirPath)}&project_root=${encodeURIComponent(activeProject.root_path)}`
        );
        if (res.ok) {
          const data = await res.json();
          setFileTree(data.entries || []);
        }
      } catch {
        // ignore
      }
      setLoading(false);
    },
    [activeProject, setFileTree]
  );

  useEffect(() => {
    if (activeProject) {
      loadDirectory(".");
    }
  }, [activeProject, loadDirectory]);

  const handleFileClick = async (entry: FileEntry) => {
    if (entry.type === "directory") {
      const newExpanded = new Set(expandedDirs);
      if (newExpanded.has(entry.path)) {
        newExpanded.delete(entry.path);
      } else {
        newExpanded.add(entry.path);
      }
      setExpandedDirs(newExpanded);
      return;
    }

    if (!activeProject) return;

    try {
      const res = await fetch(
        `${API}/api/files/read?file_path=${encodeURIComponent(entry.path)}&project_root=${encodeURIComponent(activeProject.root_path)}`
      );
      if (res.ok) {
        const data = await res.json();
        setActiveFile({ path: entry.path, content: data.content });
        setShowDiffViewer(false);
      }
    } catch {
      // ignore
    }
  };

  const renderTree = (entries: FileEntry[], depth: number = 0) => {
    const dirs = entries.filter((e) => e.type === "directory");
    const files = entries.filter((e) => e.type === "file");
    const sorted = [...dirs, ...files];

    return sorted.map((entry) => (
      <div key={entry.path}>
        <button
          className="flex items-center gap-1 w-full px-2 py-0.5 text-left text-sm hover:bg-[var(--surface-secondary)] transition-colors"
          style={{ paddingLeft: 8 + depth * 16 }}
          onClick={() => handleFileClick(entry)}
        >
          <span className="text-xs text-[var(--text-tertiary)] shrink-0">
            {entry.type === "directory" ? (expandedDirs.has(entry.path) ? "▾" : "▸") : " "}
          </span>
          <span className="shrink-0 mr-1">
            {entry.type === "directory" ? "📁" : "📄"}
          </span>
          <span className="truncate text-[var(--text-primary)]">{entry.name}</span>
        </button>
      </div>
    ));
  };

  return (
    <div className="py-1">
      {projects.length === 0 && (
        <p className="px-3 text-xs text-[var(--text-tertiary)]">No projects loaded</p>
      )}
      {activeProject && (
        <div className="px-3 py-1 mb-1">
          <select
            className="input text-xs py-1"
            value={activeProjectId || ""}
            onChange={(e) => setActiveProject(e.target.value || null)}
          >
            {projects.map((p) => (
              <option key={p.project_id} value={p.project_id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      )}
      {loading ? (
        <p className="px-3 text-xs text-[var(--text-tertiary)]">Loading...</p>
      ) : (
        renderTree(fileTree)
      )}
    </div>
  );
}

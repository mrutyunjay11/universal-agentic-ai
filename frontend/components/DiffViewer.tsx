"use client";

import dynamic from "next/dynamic";
import { useUIStore } from "@/store/ui";

const DiffEditor = dynamic(
  () => import("@monaco-editor/react").then((mod) => ({ default: mod.DiffEditor })),
  { ssr: false }
);

export function DiffViewer() {
  const diffContent = useUIStore((s) => s.diffContent);
  const setShowDiffViewer = useUIStore((s) => s.setShowDiffViewer);
  const setDiffContent = useUIStore((s) => s.setDiffContent);

  if (!diffContent) {
    return (
      <div className="flex items-center justify-center h-full text-[var(--text-tertiary)]">
        No diff to display
      </div>
    );
  }

  return (
    <div className="h-full w-full flex flex-col">
      <div className="flex items-center justify-between px-3 py-1 border-b border-[var(--border)] bg-[var(--surface-secondary)]">
        <span className="text-sm font-medium text-[var(--text-primary)]">
          Diff: {diffContent.filePath}
        </span>
        <button
          onClick={() => {
            setShowDiffViewer(false);
            setDiffContent(null);
          }}
          className="btn-ghost p-1 text-xs"
        >
          Close
        </button>
      </div>
      <div className="flex-1">
        <DiffEditor
          height="100%"
          original={diffContent.original}
          modified={diffContent.modified}
          language="typescript"
          theme="vs-dark"
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            renderSideBySide: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            readOnly: true,
          }}
        />
      </div>
    </div>
  );
}

"use client";

import dynamic from "next/dynamic";
import { useCallback, useRef } from "react";
import { useProjectStore } from "@/store/project";
import { useUIStore } from "@/store/ui";
import type { OnMount } from "@monaco-editor/react";

const MonacoEditorInner = dynamic(
  () => import("@monaco-editor/react").then((mod) => mod.default),
  { ssr: false }
);

const LANGUAGE_MAP: Record<string, string> = {
  py: "python",
  ts: "typescript",
  tsx: "typescript",
  js: "javascript",
  jsx: "javascript",
  rs: "rust",
  go: "go",
  java: "java",
  php: "php",
  rb: "ruby",
  c: "c",
  cpp: "cpp",
  h: "c",
  hpp: "cpp",
  swift: "swift",
  kt: "kotlin",
  scala: "scala",
  css: "css",
  scss: "scss",
  html: "html",
  json: "json",
  md: "markdown",
  yaml: "yaml",
  yml: "yaml",
  toml: "plaintext",
  sql: "sql",
  sh: "shell",
  bash: "shell",
  zsh: "shell",
};

function getLanguage(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase() || "";
  return LANGUAGE_MAP[ext] || "plaintext";
}

export function MonacoEditor() {
  const activeFile = useProjectStore((s) => s.activeFile);
  const editorRef = useRef<any>(null);

  const handleMount: OnMount = useCallback((editor) => {
    editorRef.current = editor;
    editor.focus();
  }, []);

  if (!activeFile) {
    return (
      <div className="flex items-center justify-center h-full text-[var(--text-tertiary)]">
        <div className="text-center">
          <div className="text-4xl mb-2 opacity-30">{ }</div>
          <p className="text-sm">Open a file from the explorer to start editing</p>
        </div>
      </div>
    );
  }

  const language = getLanguage(activeFile.path);

  return (
    <div className="h-full w-full">
      <div className="flex items-center px-3 py-1 border-b border-[var(--border)] bg-[var(--surface-secondary)] text-xs text-[var(--text-secondary)]">
        <span className="font-medium text-[var(--text-primary)]">{activeFile.path}</span>
        <span className="ml-2 px-1.5 py-0.5 rounded bg-[var(--surface-tertiary)]">{language}</span>
      </div>
      <div className="h-[calc(100%-28px)]">
        <MonacoEditorInner
          height="100%"
          language={language}
          value={activeFile.content}
          theme="vs-dark"
          onMount={handleMount}
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            minimap: { enabled: true },
            scrollBeyondLastLine: false,
            lineNumbers: "on",
            renderWhitespace: "selection",
            tabSize: 2,
            wordWrap: "on",
            automaticLayout: true,
            bracketPairColorization: { enabled: true },
            smoothScrolling: true,
            cursorBlinking: "smooth",
            cursorSmoothCaretAnimation: "on",
            padding: { top: 8 },
          }}
        />
      </div>
    </div>
  );
}

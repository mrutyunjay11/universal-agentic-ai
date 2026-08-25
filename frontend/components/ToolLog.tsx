"use client";

import { useUIStore } from "@/store/ui";

export function ToolLog() {
  const toolExecutions = useUIStore((s) => s.toolExecutions);

  if (toolExecutions.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-[var(--text-tertiary)]">No tool calls yet</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-2 space-y-1">
      {toolExecutions.map((exec, i) => (
        <details key={i} className="group">
          <summary className="flex items-center gap-2 px-2 py-1 rounded cursor-pointer text-xs hover:bg-[var(--surface-secondary)]">
            <span
              className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                exec.success ? "bg-green-500" : "bg-red-500"
              }`}
            />
            <span className="font-mono text-[var(--accent)]">{exec.tool}</span>
            <span className="text-[var(--text-tertiary)]">
              {exec.duration_ms}ms
            </span>
            {!exec.success && exec.error && (
              <span className="text-red-500 truncate">{exec.error}</span>
            )}
          </summary>
          <div className="ml-4 px-2 py-1 text-xs font-mono bg-[var(--surface-secondary)] rounded whitespace-pre-wrap max-h-40 overflow-y-auto">
            {exec.output || exec.error || "No output"}
          </div>
        </details>
      ))}
    </div>
  );
}

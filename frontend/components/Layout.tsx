"use client";

import { useEffect } from "react";
import { FileExplorer } from "./FileExplorer";
import { ChatPanel } from "./ChatPanel";
import { MonacoEditor } from "./MonacoEditor";
import { TerminalPanel } from "./TerminalPanel";
import { ToolLog } from "./ToolLog";
import { DiffViewer } from "./DiffViewer";
import { ApprovalModal } from "./ApprovalModal";
import { SimpleChatView } from "./SimpleChatView";
import { useUIStore } from "@/store/ui";
import { useProjectStore } from "@/store/project";
import { useTheme } from "./ThemeProvider";
import { Sparkles, Code2, MessageSquare, Sun, Moon, Terminal, FolderTree, Sidebar, ShieldAlert } from "lucide-react";

export function Layout() {
  const { theme, toggleTheme } = useTheme();
  const appMode = useUIStore((s) => s.appMode);
  const toggleAppMode = useUIStore((s) => s.toggleAppMode);
  const leftPanelOpen = useUIStore((s) => s.leftPanelOpen);
  const rightPanelOpen = useUIStore((s) => s.rightPanelOpen);
  const bottomPanelOpen = useUIStore((s) => s.bottomPanelOpen);
  const activeBottomPanel = useUIStore((s) => s.activeBottomPanel);
  const setBottomPanel = useUIStore((s) => s.setBottomPanel);
  const setActiveBottomPanel = useUIStore((s) => s.setActiveBottomPanel);
  const toggleLeftPanel = useUIStore((s) => s.toggleLeftPanel);
  const toggleRightPanel = useUIStore((s) => s.toggleRightPanel);
  const toggleBottomPanel = useUIStore((s) => s.toggleBottomPanel);
  const showDiffViewer = useUIStore((s) => s.showDiffViewer);
  const agentState = useUIStore((s) => s.agentState);
  const approvalPending = useUIStore((s) => s.approvalPending);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "b") {
        e.preventDefault();
        toggleLeftPanel();
      }
      if ((e.metaKey || e.ctrlKey) && e.key === "j") {
        e.preventDefault();
        toggleBottomPanel();
      }
      if ((e.metaKey || e.ctrlKey) && e.key === "'") {
        e.preventDefault();
        toggleRightPanel();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [toggleLeftPanel, toggleRightPanel, toggleBottomPanel]);

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[var(--surface)] text-[var(--text-primary)]">
      {/* Top Global Header with Mode Switcher */}
      <header className="flex items-center justify-between h-12 px-4 bg-[var(--surface-secondary)] border-b border-[var(--border)] shrink-0 z-20">
        {/* Brand & Status */}
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-purple-600 via-indigo-600 to-blue-500 flex items-center justify-center shadow-md">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold tracking-tight text-[var(--text-primary)]">
              Universal Agentic AI
            </span>
            <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-purple-500/10 text-purple-400 border border-purple-500/20">
              Qwen3.8-Max Stack
            </span>
          </div>

          {agentState !== "idle" && (
            <span className="badge bg-purple-600 text-white text-[10px] uppercase font-bold animate-pulse px-2 py-0.5 rounded-full">
              {agentState}
            </span>
          )}
        </div>

        {/* Center / Right Mode Switcher & Tools */}
        <div className="flex items-center gap-2">
          {/* Mode Switcher Button (Antigravity 2 Style) */}
          <button
            onClick={toggleAppMode}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold shadow-sm transition-all duration-200 ${
              appMode === "chat"
                ? "bg-purple-600 hover:bg-purple-500 text-white shadow-purple-500/20"
                : "bg-[var(--surface)] border border-[var(--border)] text-[var(--text-primary)] hover:border-purple-500/50"
            }`}
          >
            {appMode === "chat" ? (
              <>
                <Code2 className="w-3.5 h-3.5 text-purple-200" />
                <span>⚡ Switch to Agent IDE</span>
              </>
            ) : (
              <>
                <MessageSquare className="w-3.5 h-3.5 text-purple-400" />
                <span>💬 Switch to Simple Chat</span>
              </>
            )}
          </button>

          {/* IDE-specific Panel Toggles */}
          {appMode === "ide" && (
            <div className="hidden sm:flex items-center gap-1 border-l border-[var(--border)] pl-2 ml-1">
              <button
                onClick={toggleLeftPanel}
                className={`p-1.5 rounded-lg text-xs hover:bg-[var(--surface)] transition-colors ${
                  leftPanelOpen ? "text-purple-400 bg-[var(--surface)]" : "text-[var(--text-secondary)]"
                }`}
                title="Toggle Explorer (Cmd+B)"
              >
                <FolderTree className="w-4 h-4" />
              </button>
              <button
                onClick={toggleBottomPanel}
                className={`p-1.5 rounded-lg text-xs hover:bg-[var(--surface)] transition-colors ${
                  bottomPanelOpen ? "text-purple-400 bg-[var(--surface)]" : "text-[var(--text-secondary)]"
                }`}
                title="Toggle Terminal & Tool Logs (Cmd+J)"
              >
                <Terminal className="w-4 h-4" />
              </button>
              <button
                onClick={toggleRightPanel}
                className={`p-1.5 rounded-lg text-xs hover:bg-[var(--surface)] transition-colors ${
                  rightPanelOpen ? "text-purple-400 bg-[var(--surface)]" : "text-[var(--text-secondary)]"
                }`}
                title="Toggle Chat Sidebar (Cmd+')"
              >
                <Sidebar className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-1.5 rounded-lg hover:bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            title="Toggle Theme"
          >
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>
      </header>

      {/* Main Viewport Content */}
      {appMode === "chat" ? (
        /* SIMPLE CHAT MODE (DEFAULT) */
        <SimpleChatView />
      ) : (
        /* AGENT IDE MODE */
        <div className="flex flex-1 overflow-hidden">
          {leftPanelOpen && (
            <aside className="w-60 shrink-0 border-r border-[var(--border)] bg-[var(--surface)] flex flex-col">
              <div className="flex items-center justify-between px-3 py-2 border-b border-[var(--border)]">
                <span className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
                  Explorer
                </span>
              </div>
              <div className="flex-1 overflow-y-auto">
                <FileExplorer />
              </div>
            </aside>
          )}

          <main className="flex-1 flex flex-col overflow-hidden">
            {showDiffViewer ? (
              <DiffViewer />
            ) : (
              <div className="flex-1 overflow-hidden">
                <MonacoEditor />
              </div>
            )}
          </main>

          {rightPanelOpen && (
            <aside className="w-96 shrink-0 border-l border-[var(--border)] bg-[var(--surface)] flex flex-col">
              <ChatPanel />
            </aside>
          )}
        </div>
      )}

      {/* Bottom Panel (Terminal & Tool Logs in IDE mode) */}
      {appMode === "ide" && bottomPanelOpen && (
        <div
          className="shrink-0 border-t border-[var(--border)] bg-[var(--surface)] flex flex-col z-10"
          style={{ height: 220 }}
        >
          <div className="flex items-center gap-0 px-2 border-b border-[var(--border)] shrink-0 bg-[var(--surface-secondary)]">
            {(["terminal", "tool-log"] as const).map((panel) => (
              <button
                key={panel}
                className={`px-3 py-1.5 text-xs font-semibold border-b-2 transition-colors ${
                  activeBottomPanel === panel
                    ? "border-purple-500 text-purple-400"
                    : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                }`}
                onClick={() => setActiveBottomPanel(panel)}
              >
                {panel === "terminal" ? "Terminal" : "Tool Execution Logs"}
              </button>
            ))}
          </div>
          <div className="flex-1 overflow-hidden">
            {activeBottomPanel === "terminal" ? <TerminalPanel /> : <ToolLog />}
          </div>
        </div>
      )}

      {/* Human-in-the-Loop Financial / High-Impact Action Approval Modal */}
      {approvalPending && <ApprovalModal />}
    </div>
  );
}


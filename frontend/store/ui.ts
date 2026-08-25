import { create } from "zustand";

type PanelId = "chat" | "terminal" | "explorer" | "tool-log";

interface ToolExecution {
  tool: string;
  success: boolean;
  output?: string;
  error?: string;
  duration_ms: number;
  timestamp: number;
}

type AppMode = "chat" | "ide";

interface UIState {
  appMode: AppMode;
  leftPanelOpen: boolean;
  rightPanelOpen: boolean;
  bottomPanelOpen: boolean;
  bottomPanelHeight: number;
  activeBottomPanel: PanelId;
  showDiffViewer: boolean;
  diffContent: { original: string; modified: string; filePath: string } | null;
  toolExecutions: ToolExecution[];
  agentState: string;
  approvalPending: {
    tool: string;
    args: Record<string, any>;
    description: string;
  } | null;
  setAppMode: (mode: AppMode) => void;
  toggleAppMode: () => void;
  setLeftPanel: (open: boolean) => void;
  setRightPanel: (open: boolean) => void;
  setBottomPanel: (open: boolean) => void;
  toggleLeftPanel: () => void;
  toggleRightPanel: () => void;
  toggleBottomPanel: () => void;
  setBottomPanelHeight: (height: number) => void;
  setActiveBottomPanel: (panel: PanelId) => void;
  setShowDiffViewer: (show: boolean) => void;
  setDiffContent: (content: { original: string; modified: string; filePath: string } | null) => void;
  addToolExecution: (exec: ToolExecution) => void;
  setAgentState: (state: string) => void;
  setApprovalPending: (approval: { tool: string; args: Record<string, any>; description: string } | null) => void;
}

export const useUIStore = create<UIState>((set) => ({
  appMode: "chat", // Default to simple chat mode
  leftPanelOpen: true,
  rightPanelOpen: true,
  bottomPanelOpen: false,
  bottomPanelHeight: 200,
  activeBottomPanel: "terminal",
  showDiffViewer: false,
  diffContent: null,
  toolExecutions: [],
  agentState: "idle",
  approvalPending: null,

  setAppMode: (mode) => set({ appMode: mode }),
  toggleAppMode: () => set((s) => ({ appMode: s.appMode === "chat" ? "ide" : "chat" })),
  setLeftPanel: (open) => set({ leftPanelOpen: open }),
  setRightPanel: (open) => set({ rightPanelOpen: open }),
  setBottomPanel: (open) => set({ bottomPanelOpen: open }),
  toggleLeftPanel: () => set((s) => ({ leftPanelOpen: !s.leftPanelOpen })),
  toggleRightPanel: () => set((s) => ({ rightPanelOpen: !s.rightPanelOpen })),
  toggleBottomPanel: () => set((s) => ({ bottomPanelOpen: !s.bottomPanelOpen })),
  setBottomPanelHeight: (height) => set({ bottomPanelHeight: height }),
  setActiveBottomPanel: (panel) => set({ activeBottomPanel: panel }),
  setShowDiffViewer: (show) => set({ showDiffViewer: show }),
  setDiffContent: (content) => set({ diffContent: content }),
  addToolExecution: (exec) =>
    set((state) => ({
      toolExecutions: [exec, ...state.toolExecutions].slice(0, 100),
    })),
  setAgentState: (state) => set({ agentState: state }),
  setApprovalPending: (approval) => set({ approvalPending: approval }),
}));

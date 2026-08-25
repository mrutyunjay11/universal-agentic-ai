import { create } from "zustand";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  timestamp: number;
  tool_calls?: { tool: string; args: Record<string, any> }[];
  tool_result?: { success: boolean; output?: string; error?: string };
}

interface ChatState {
  messages: ChatMessage[];
  streamingContent: string;
  isStreaming: boolean;
  addMessage: (message: Omit<ChatMessage, "id" | "timestamp">) => void;
  appendStreamToken: (token: string) => void;
  finalizeStream: () => void;
  clearMessages: () => void;
}

let msgCounter = 0;

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  streamingContent: "",
  isStreaming: false,

  addMessage: (message) => {
    const msg: ChatMessage = {
      ...message,
      id: `msg-${++msgCounter}`,
      timestamp: Date.now(),
    };
    set((state) => ({
      messages: [...state.messages, msg],
    }));
  },

  appendStreamToken: (token) => {
    const { isStreaming } = get();
    if (!isStreaming) {
      set({ isStreaming: true });
    }
    set((state) => ({
      streamingContent: state.streamingContent + token,
    }));
  },

  finalizeStream: () => {
    const { streamingContent } = get();
    if (streamingContent) {
      const msg: ChatMessage = {
        id: `msg-${++msgCounter}`,
        role: "assistant",
        content: streamingContent,
        timestamp: Date.now(),
      };
      set((state) => ({
        messages: [...state.messages, msg],
        streamingContent: "",
        isStreaming: false,
      }));
    } else {
      set({ isStreaming: false });
    }
  },

  clearMessages: () => {
    set({ messages: [], streamingContent: "", isStreaming: false });
    msgCounter = 0;
  },
}));

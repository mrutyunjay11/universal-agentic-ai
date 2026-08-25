"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { useChatStore, ChatMessage } from "@/store/chat";
import { useUIStore } from "@/store/ui";
import { useProjectStore } from "@/store/project";
import { useWebSocket } from "@/hooks/useWebSocket";

export function ChatPanel() {
  const messages = useChatStore((s) => s.messages);
  const streamingContent = useChatStore((s) => s.streamingContent);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const addMessage = useChatStore((s) => s.addMessage);
  const appendStreamToken = useChatStore((s) => s.appendStreamToken);
  const finalizeStream = useChatStore((s) => s.finalizeStream);
  const addToolExecution = useUIStore((s) => s.addToolExecution);
  const setAgentState = useUIStore((s) => s.setAgentState);
  const setApprovalPending = useUIStore((s) => s.setApprovalPending);
  const activeProjectId = useProjectStore((s) => s.activeProjectId);

  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const onStream = useCallback(
    (data: any) => {
      if (data?.token) {
        appendStreamToken(data.token);
      }
    },
    [appendStreamToken]
  );

  const onStateChange = useCallback(
    (data: any) => {
      if (data?.to) {
        setAgentState(data.to);
      }
    },
    [setAgentState]
  );

  const onToolExecution = useCallback(
    (data: any) => {
      addToolExecution({
        tool: data.tool,
        success: data.success,
        output: data.output,
        error: data.error,
        duration_ms: data.duration_ms,
        timestamp: Date.now(),
      });
    },
    [addToolExecution]
  );

  const onApproval = useCallback(
    (data: any) => {
      setApprovalPending({
        tool: data.tool,
        args: data.args,
        description: data.description,
      });
    },
    [setApprovalPending]
  );

  const onDone = useCallback(
    (data: any) => {
      finalizeStream();
      setAgentState("idle");
    },
    [finalizeStream, setAgentState]
  );

  const onError = useCallback(
    (data: any) => {
      addMessage({
        role: "system",
        content: `Error: ${data?.error || "Unknown error"}`,
      });
      finalizeStream();
      setAgentState("error");
    },
    [addMessage, finalizeStream, setAgentState]
  );

  const { sendMessage, sendApproval, sendCancel, connected } = useWebSocket({
    onStream,
    onStateChange,
    onToolExecution,
    onApproval,
    onDone,
    onError,
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  const handleSend = useCallback(() => {
    if (!input.trim() || !connected) return;
    const text = input.trim();
    setInput("");

    addMessage({ role: "user", content: text });
    sendMessage(text, activeProjectId || undefined);
  }, [input, connected, addMessage, sendMessage, activeProjectId]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-[var(--border)] shrink-0">
        <span className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">
          Chat
        </span>
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              connected ? "bg-green-500" : "bg-red-500"
            }`}
          />
          {isStreaming && (
            <button onClick={sendCancel} className="btn-ghost p-1 text-xs text-red-500">
              Cancel
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">
        {messages.length === 0 && !isStreaming && (
          <div className="flex items-center justify-center h-full text-center">
            <div>
              <p className="text-sm text-[var(--text-tertiary)] mb-1">
                Ask me to help with your code
              </p>
              <p className="text-xs text-[var(--text-tertiary)]">
                Try: "Explain this file" or "Fix the bug in main.py"
              </p>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {streamingContent && (
          <div className="flex gap-2">
            <div className="flex-1 rounded-lg px-3 py-2 bg-[var(--accent)]/10 text-sm text-[var(--text-primary)]">
              <ReactMarkdown>{streamingContent}</ReactMarkdown>
            </div>
          </div>
        )}

        {isStreaming && !streamingContent && (
          <div className="flex items-center gap-1 px-3 py-2 typing-indicator">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-tertiary)]" />
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-tertiary)]" />
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-tertiary)]" />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="px-3 py-2 border-t border-[var(--border)] shrink-0">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            className="input resize-none text-sm"
            rows={2}
            placeholder={connected ? "Type a message..." : "Connecting..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!connected}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || !connected}
            className="btn-primary self-end"
          >
            Send
          </button>
        </div>
        <p className="mt-1 text-[10px] text-[var(--text-tertiary)]">
          Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <div className="px-3 py-1 rounded-full bg-[var(--surface-tertiary)] text-xs text-[var(--text-tertiary)]">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex gap-2 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex-1 rounded-lg px-3 py-2 text-sm ${
          isUser
            ? "bg-[var(--accent)] text-white"
            : "bg-[var(--surface-secondary)] text-[var(--text-primary)]"
        }`}
      >
        <ReactMarkdown>{message.content}</ReactMarkdown>

        {message.tool_calls && (
          <div className="mt-2 space-y-1 border-t border-[var(--border)] pt-2">
            {message.tool_calls.map((tc, i) => (
              <div
                key={i}
                className="text-xs font-mono text-[var(--accent)]"
              >
                → {tc.tool}({JSON.stringify(tc.args)})
              </div>
            ))}
          </div>
        )}

        {message.tool_result && (
          <div
            className={`mt-1 text-xs ${
              message.tool_result.success
                ? "text-green-600 dark:text-green-400"
                : "text-red-600 dark:text-red-400"
            }`}
          >
            {message.tool_result.success
              ? "✓ Tool completed"
              : `✗ Error: ${message.tool_result.error || "Unknown"}`}
          </div>
        )}
      </div>
    </div>
  );
}

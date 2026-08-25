"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { useChatStore, ChatMessage } from "@/store/chat";
import { useUIStore } from "@/store/ui";
import { useWebSocket } from "@/hooks/useWebSocket";
import {
  Sparkles,
  Search,
  Code,
  LineChart,
  Bot,
  Send,
  Zap,
  CheckCircle2,
  AlertCircle,
  Terminal,
  Globe,
  FileCode,
  ChevronRight,
  RefreshCw,
} from "lucide-react";

export function SimpleChatView() {
  const messages = useChatStore((s) => s.messages);
  const streamingContent = useChatStore((s) => s.streamingContent);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const addMessage = useChatStore((s) => s.addMessage);
  const appendStreamToken = useChatStore((s) => s.appendStreamToken);
  const finalizeStream = useChatStore((s) => s.finalizeStream);
  const clearMessages = useChatStore((s) => s.clearMessages);
  const addToolExecution = useUIStore((s) => s.addToolExecution);
  const setAgentState = useUIStore((s) => s.setAgentState);
  const setApprovalPending = useUIStore((s) => s.setApprovalPending);
  const toggleAppMode = useUIStore((s) => s.toggleAppMode);

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

  const { sendMessage, sendCancel, connected } = useWebSocket({
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

  const handleSend = () => {
    if (!input.trim() || isStreaming) return;
    const text = input.trim();
    setInput("");
    addMessage({ role: "user", content: text });
    sendMessage(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestions = [
    {
      icon: <Globe className="w-5 h-5 text-blue-400" />,
      title: "Search & Scrape Web",
      desc: "Surf live websites, extract structured tables, and scrape articles.",
      prompt: "Search the web for the latest advancements in autonomous AI agents and extract a comparison table.",
    },
    {
      icon: <Code className="w-5 h-5 text-purple-400" />,
      title: "Autonomous Coding",
      desc: "Inspect project files, fix bugs, write unit tests, and refactor code.",
      prompt: "Inspect this project, run unit tests, and identify any architectural bottlenecks or missing features.",
    },
    {
      icon: <LineChart className="w-5 h-5 text-emerald-400" />,
      title: "Data & Calculation",
      desc: "Analyze datasets, run statistical math, and evaluate spreadsheets.",
      prompt: "Generate a sample CSV dataset with 10 rows of metrics and calculate mean, median, and standard deviation.",
    },
    {
      icon: <Bot className="w-5 h-5 text-amber-400" />,
      title: "Multi-Agent Workflow",
      desc: "Coordinate specialized agents to plan, execute, and verify tasks.",
      prompt: "Decompose a multi-step task to research a library, write a test benchmark, and verify the output with AST.",
    },
  ];

  return (
    <div className="flex-1 flex flex-col h-full bg-gradient-to-b from-[var(--surface)] to-[var(--surface-secondary)] overflow-hidden">
      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.length === 0 && !streamingContent ? (
            <div className="py-12 text-center space-y-8 animate-fadeIn">
              {/* Hero Icon & Title */}
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-blue-500 shadow-xl shadow-indigo-500/20 mb-2">
                <Sparkles className="w-10 h-10 text-white animate-pulse" />
              </div>
              <div className="space-y-2">
                <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-[var(--text-primary)]">
                  What can I build or automate for you today?
                </h1>
                <p className="text-base sm:text-lg text-[var(--text-secondary)] max-w-2xl mx-auto">
                  Universal Agentic AI equipped with 169 verified tools, live web browsing, data scraping, autonomous coding, and deterministic verification.
                </p>
              </div>

              {/* Suggestion Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-3xl mx-auto text-left pt-4">
                {suggestions.map((card, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInput(card.prompt);
                      inputRef.current?.focus();
                    }}
                    className="p-4 rounded-2xl border border-[var(--border)] bg-[var(--surface)]/60 backdrop-blur-sm hover:border-purple-500/50 hover:bg-[var(--surface-secondary)] transition-all duration-200 group flex flex-col justify-between"
                  >
                    <div className="flex items-center justify-between w-full mb-2">
                      <div className="p-2 rounded-xl bg-[var(--surface-secondary)] border border-[var(--border)] group-hover:scale-110 transition-transform">
                        {card.icon}
                      </div>
                      <ChevronRight className="w-4 h-4 text-[var(--text-tertiary)] group-hover:text-purple-400 group-hover:translate-x-1 transition-all" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-[var(--text-primary)] group-hover:text-purple-400 transition-colors">
                        {card.title}
                      </h3>
                      <p className="text-xs text-[var(--text-secondary)] mt-1 line-clamp-2">
                        {card.desc}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex gap-4 ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  } animate-fadeIn`}
                >
                  {msg.role !== "user" && (
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center shrink-0 shadow-md">
                      <Sparkles className="w-4 h-4 text-white" />
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] rounded-2xl p-4 sm:p-5 text-sm shadow-sm ${
                      msg.role === "user"
                        ? "bg-purple-600 text-white rounded-tr-sm"
                        : msg.role === "system"
                        ? "bg-red-500/10 border border-red-500/20 text-red-400"
                        : "bg-[var(--surface)] border border-[var(--border)] text-[var(--text-primary)] rounded-tl-sm"
                    }`}
                  >
                    {msg.role === "user" ? (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <div className="prose dark:prose-invert max-w-none text-sm leading-relaxed">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    )}
                  </div>

                  {msg.role === "user" && (
                    <div className="w-8 h-8 rounded-xl bg-slate-700 flex items-center justify-center shrink-0 text-white font-medium text-xs">
                      You
                    </div>
                  )}
                </div>
              ))}

              {/* Active Streaming Response */}
              {streamingContent && (
                <div className="flex gap-4 justify-start animate-fadeIn">
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center shrink-0 shadow-md">
                    <Sparkles className="w-4 h-4 text-white animate-spin" />
                  </div>
                  <div className="max-w-[85%] rounded-2xl p-4 sm:p-5 text-sm bg-[var(--surface)] border border-[var(--border)] text-[var(--text-primary)] rounded-tl-sm">
                    <div className="prose dark:prose-invert max-w-none text-sm leading-relaxed">
                      <ReactMarkdown>{streamingContent}</ReactMarkdown>
                    </div>
                    <div className="flex items-center gap-1.5 mt-2 text-xs text-purple-400 font-mono">
                      <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-ping" />
                      Synthesizing verified response...
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Floating Centered Input Container */}
      <div className="p-4 sm:p-6 bg-gradient-to-t from-[var(--surface)] via-[var(--surface)]/90 to-transparent border-t border-[var(--border)] shrink-0">
        <div className="max-w-4xl mx-auto">
          <div className="relative rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-2xl shadow-purple-500/5 focus-within:border-purple-500 transition-colors p-2.5">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={connected ? "Ask anything (e.g. 'Search web for AI news', 'Inspect code and fix bugs', 'Analyze data')..." : "Connecting to Agent Engine..."}
              disabled={!connected}
              rows={2}
              className="w-full bg-transparent resize-none outline-none text-sm px-2 text-[var(--text-primary)] placeholder-[var(--text-tertiary)]"
            />

            <div className="flex items-center justify-between pt-2 border-t border-[var(--border)]/40 mt-1">
              <div className="flex items-center gap-2 text-xs text-[var(--text-tertiary)]">
                <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-[var(--surface-secondary)] border border-[var(--border)] font-mono text-[11px]">
                  <Zap className="w-3 h-3 text-purple-400" />
                  Qwen3.8-Max • 169 Tools
                </span>
                <span className="hidden sm:inline">Shift+Enter for newline</span>
              </div>

              <div className="flex items-center gap-2">
                {isStreaming ? (
                  <button
                    onClick={sendCancel}
                    className="px-3 py-1.5 rounded-xl bg-red-500/20 hover:bg-red-500/30 text-red-400 text-xs font-medium transition-colors"
                  >
                    Stop Agent
                  </button>
                ) : (
                  <button
                    onClick={handleSend}
                    disabled={!input.trim() || !connected}
                    className="px-4 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-40 text-white text-xs font-medium shadow-md shadow-purple-600/20 flex items-center gap-1.5 transition-all"
                  >
                    <span>Send</span>
                    <Send className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

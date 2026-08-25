"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";

export function TerminalPanel() {
  const terminalRef = useRef<HTMLDivElement>(null);
  const [command, setCommand] = useState("");
  const [output, setOutput] = useState<string[]>([
    "Welcome to Local Coding Agent Terminal",
    "Type a command and press Enter to execute",
    "---",
  ]);
  const [xtermReady, setXtermReady] = useState(false);
  const terminalInstanceRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const initTerminal = async () => {
      try {
        const { Terminal } = await import("xterm");
        const { FitAddon } = await import("xterm-addon-fit");

        const term = new Terminal({
          fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
          fontSize: 13,
          theme: {
            background: "#1e1e1e",
            foreground: "#e0e0e0",
            cursor: "#e0e0e0",
            selectionBackground: "#3b82f640",
          },
          cursorBlink: true,
          cursorStyle: "block",
          allowTransparency: true,
        });

        const fitAddon = new FitAddon();
        term.loadAddon(fitAddon);

        if (terminalRef.current) {
          term.open(terminalRef.current);
          fitAddon.fit();
        }

        term.writeln("Terminal ready. Type commands below.");

        term.onData((data: string) => {
          const ti = terminalInstanceRef.current;
          if (!ti) return;
          if (data === "\r") {
            const cmd = ti._currentLine || "";
            ti._currentLine = "";
            term.writeln("");
            executeCommand(cmd);
          } else if (data === "\x7f") {
            if (ti._currentLine && ti._currentLine.length > 0) {
              ti._currentLine = ti._currentLine.slice(0, -1);
              term.write("\b \b");
            }
          } else {
            if (!ti._currentLine) ti._currentLine = "";
            ti._currentLine += data;
            term.write(data);
          }
        });

        terminalInstanceRef.current = { _currentLine: "" };
        setXtermReady(true);
      } catch {
        setXtermReady(false);
      }
    };

    initTerminal();

    return () => {
      if (terminalInstanceRef.current) {
        terminalInstanceRef.current = null;
      }
    };
  }, []);

  const executeCommand = useCallback(
    async (cmd: string) => {
      setOutput((prev) => [...prev, `$ ${cmd}`]);

      try {
        const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(
          `${API}/api/chat`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              message: `Run command: ${cmd}`,
              stream: false,
            }),
          }
        );
        const data = await res.json();
        setOutput((prev) => [...prev, data.message || "Command executed"]);
      } catch (e: any) {
        setOutput((prev) => [...prev, `Error: ${e.message}`]);
      }

      setOutput((prev) => [...prev, "---"]);
    },
    []
  );

  const handleCommandSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim()) return;
    const cmd = command.trim();
    setCommand("");

    setOutput((prev) => [...prev, `$ ${cmd}`]);

    try {
      const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: `Run command: ${cmd}`,
          stream: false,
        }),
      });
      const data = await res.json();
      setOutput((prev) => [...prev, data.message || "Command executed"]);
    } catch (e: any) {
      setOutput((prev) => [...prev, `Error: ${e.message}`]);
    }

    setOutput((prev) => [...prev, "---"]);
  };

  if (xtermReady) {
    return (
      <div ref={terminalRef} className="h-full w-full" />
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-1 overflow-y-auto p-3 font-mono text-sm bg-[#1e1e1e] text-[#e0e0e0]">
        {output.map((line, i) => (
          <div key={i} className="whitespace-pre-wrap">
            {line}
          </div>
        ))}
      </div>
      <form onSubmit={handleCommandSubmit} className="flex border-t border-[var(--border)]">
        <span className="px-2 py-1.5 text-sm font-mono text-[var(--text-tertiary)] bg-[var(--surface-secondary)]">
          $
        </span>
        <input
          className="flex-1 px-2 py-1.5 text-sm font-mono bg-[var(--surface-secondary)] text-[var(--text-primary)] border-none outline-none"
          placeholder="Type a command..."
          value={command}
          onChange={(e) => setCommand(e.target.value)}
        />
      </form>
    </div>
  );
}

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type MessageHandler = (data: any) => void;

interface UseWebSocketOptions {
  sessionId?: string;
  onMessage?: MessageHandler;
  onStateChange?: MessageHandler;
  onToolExecution?: MessageHandler;
  onStream?: MessageHandler;
  onApproval?: MessageHandler;
  onDone?: MessageHandler;
  onError?: MessageHandler;
  autoReconnect?: boolean;
}

interface UseWebSocketReturn {
  send: (data: any) => void;
  sendMessage: (message: string, projectId?: string, projectRoot?: string) => void;
  sendApproval: (approved: boolean, reason?: string) => void;
  sendCancel: () => void;
  connected: boolean;
  sessionId: string | null;
  reconnect: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    onMessage,
    onStateChange,
    onToolExecution,
    onStream,
    onApproval,
    onDone,
    onError,
    autoReconnect = true,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const [connected, setConnected] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const messageQueueRef = useRef<any[]>([]);

  const connect = useCallback(() => {
    const sid = options.sessionId || sessionIdRef.current;
    if (!sid) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = process.env.NEXT_PUBLIC_WS_URL || `${protocol}//${window.location.host}`;
    const url = `${host}/api/ws/chat/${sid}`;

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        setConnected(true);
        while (messageQueueRef.current.length > 0) {
          const msg = messageQueueRef.current.shift();
          ws.send(JSON.stringify(msg));
        }
      };

      ws.onclose = () => {
        setConnected(false);
        if (autoReconnect) {
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        }
      };

      ws.onerror = () => {
        setConnected(false);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          handleMessage(msg);
        } catch {
          // ignore non-JSON messages
        }
      };

      wsRef.current = ws;
    } catch {
      if (autoReconnect) {
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      }
    }
  }, [options.sessionId, autoReconnect]);

  const handleMessage = useCallback(
    (msg: any) => {
      switch (msg.type) {
        case "session_created":
          sessionIdRef.current = msg.session_id;
          setSessionId(msg.session_id);
          break;
        case "connected":
          sessionIdRef.current = msg.session_id;
          setSessionId(msg.session_id);
          break;
        case "stream":
          onStream?.(msg.data);
          break;
        case "state_change":
          onStateChange?.(msg.data);
          break;
        case "tool_execution":
          onToolExecution?.(msg.data);
          break;
        case "approval_required":
          onApproval?.(msg.data);
          break;
        case "done":
          onDone?.(msg.data);
          break;
        case "error":
          onError?.(msg.data);
          break;
        default:
          onMessage?.(msg);
      }
    },
    [onMessage, onStateChange, onToolExecution, onStream, onApproval, onDone, onError]
  );

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const send = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      messageQueueRef.current.push(data);
    }
  }, []);

  const sendMessage = useCallback(
    (message: string, projectId?: string, projectRoot?: string) => {
      send({
        type: "message",
        message,
        project_id: projectId,
        project_root: projectRoot || "./projects",
      });
    },
    [send]
  );

  const sendApproval = useCallback(
    (approved: boolean, reason?: string) => {
      send({ type: "approval", approved, reason });
    },
    [send]
  );

  const sendCancel = useCallback(() => {
    send({ type: "cancel" });
  }, [send]);

  const reconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    connect();
  }, [connect]);

  return {
    send,
    sendMessage,
    sendApproval,
    sendCancel,
    connected,
    sessionId,
    reconnect,
  };
}

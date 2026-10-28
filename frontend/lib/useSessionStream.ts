"use client";
import { useEffect, useState } from "react";

export type StreamState = "connecting" | "connected" | "reconnecting" | "offline";
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
export function useSessionStream(sessionId: string, onUpdate: () => void): StreamState {
  const [state, setState] = useState<StreamState>("connecting");
  useEffect(() => {
    let disposed = false;
    let socket: WebSocket | undefined;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let attempts = 0;
    function connect() {
      if (disposed) return;
      setState(attempts ? "reconnecting" : "connecting");
      socket = new WebSocket(`${WS_URL.replace(/\/$/, "")}/ws/sessions/${sessionId}/`);
      socket.onopen = () => { attempts = 0; setState("connected"); };
      socket.onmessage = (message) => {
        try {
          const event = JSON.parse(message.data) as { type?: string };
          if (["signal.created", "cluster.updated", "response.created", "feedback.updated", "session.status_changed"].includes(event.type || "")) onUpdate();
        } catch { /* Ignore malformed notification; durable data is loaded from the API. */ }
      };
      socket.onclose = (event) => {
        if (disposed) return;
        if (event.code === 4401 || event.code === 4404) { setState("offline"); return; }
        attempts += 1;
        setState("reconnecting");
        timer = setTimeout(connect, Math.min(1000 * 2 ** Math.min(attempts, 5), 30000));
      };
      socket.onerror = () => socket?.close();
    }
    connect();
    return () => { disposed = true; if (timer) clearTimeout(timer); socket?.close(1000, "Page closed"); };
  }, [sessionId, onUpdate]);
  return state;
}

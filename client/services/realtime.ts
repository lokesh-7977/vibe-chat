import { store } from "../store";

export type RealtimeEvent = {
  type: string;
  channelId?: string;
  channel_id?: string;
  userId?: string;
  user_id?: string;
  message?: string;
};

type RealtimeHandler = (event: RealtimeEvent) => void;

function getSocketUrl() {
  if (process.env.NEXT_PUBLIC_WS_URL) return process.env.NEXT_PUBLIC_WS_URL;
  const apiBaseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
  const token = store.getState().auth.accessToken;
  const base = apiBaseUrl.replace(/^http/, "ws").replace(/\/$/, "") + "/ws";
  return token ? `${base}?token=${token}` : base;
}

class RealtimeClient {
  private socket: WebSocket | null = null;
  private listeners = new Set<RealtimeHandler>();
  private queue: RealtimeEvent[] = [];

  connect() {
    if (typeof window === "undefined") return;
    if (
      this.socket &&
      (this.socket.readyState === WebSocket.CONNECTING ||
        this.socket.readyState === WebSocket.OPEN)
    ) {
      return;
    }

    this.socket = new WebSocket(getSocketUrl());
    this.socket.addEventListener("open", () => {
      for (const ev of this.queue) {
        this.socket?.send(JSON.stringify(ev));
      }
      this.queue = [];
    });
    this.socket.addEventListener("message", (event) => {
      try {
        const parsed = JSON.parse(event.data) as RealtimeEvent;
        this.listeners.forEach((listener) => listener(parsed));
      } catch {
        this.listeners.forEach((listener) =>
          listener({ type: "message", message: String(event.data) }),
        );
      }
    });
  }

  disconnect() {
    this.socket?.close();
    this.socket = null;
    this.queue = [];
  }

  subscribe(listener: RealtimeHandler) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  send(event: RealtimeEvent) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(event));
      return true;
    }
    if (this.socket?.readyState === WebSocket.CONNECTING) {
      this.queue.push(event);
      return true;
    }
    return false;
  }

  join(channelId: string) {
    return this.send({ type: "join", channel_id: channelId });
  }

  leave(channelId: string) {
    return this.send({ type: "leave", channel_id: channelId });
  }

  typingStarted(channelId: string) {
    return this.send({ type: "typing_started", channel_id: channelId });
  }

  typingStopped(channelId: string) {
    return this.send({ type: "typing_stopped", channel_id: channelId });
  }
}

export const realtimeClient = new RealtimeClient();

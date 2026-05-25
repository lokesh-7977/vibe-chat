import axiosInstance, { getAuthHeaders, tryRefreshToken } from "../../services/axios";
import type { AIActionStreamRequest, UUID } from "../../types";
import { aiActionQueryKeys } from "./query.keys";

export * from "./query.keys";

function toServerPayload(payload: AIActionStreamRequest) {
  return {
    action: payload.action ?? "auto",
    message_id: payload.messageId ?? null,
    input: payload.input ?? "",
    target_language: payload.targetLanguage ?? null,
    private_response: payload.privateResponse ?? null,
    history: payload.history ?? null,
  };
}

export async function streamAiAction(
  channelId: UUID,
  payload: AIActionStreamRequest,
  timeoutMs?: number,
) {
  const q = aiActionQueryKeys.stream(channelId);
  const res = await axiosInstance.post<string>(q.url, toServerPayload(payload), {
    responseType: "text",
    timeout: timeoutMs,
  });
  return res.data;
}

export async function streamAiActionBody(
  channelId: UUID,
  payload: AIActionStreamRequest,
) {
  const q = aiActionQueryKeys.stream(channelId);
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  await tryRefreshToken();
  const res = await fetch(`${base}${q.url}`, {
    method: "POST",
    credentials: "include",
    headers: getAuthHeaders(),
    body: JSON.stringify(toServerPayload(payload)),
  });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  if (!res.body) throw new Error("No response body");
  return res.body;
}

export async function streamAiActionStream(
  channelId: UUID,
  payload: AIActionStreamRequest,
) {
  const q = aiActionQueryKeys.stream(channelId);
  await tryRefreshToken();
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}${q.url}`, {
    method: "POST",
    credentials: "include",
    headers: getAuthHeaders(),
    body: JSON.stringify(toServerPayload(payload)),
  });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  if (!res.body) throw new Error("No response body");
  return res.body;
}

export function triggerAiAction(
  channelId: UUID,
  payload: AIActionStreamRequest,
) {
  axiosInstance
    .post(`/channels/${channelId}/ai/actions/stream`, toServerPayload(payload), {
      responseType: "text",
      timeout: 180000,
    })
    .catch((err) => {
      console.error("AI action failed:", err?.message ?? err);
    });
}

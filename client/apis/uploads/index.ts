import axiosInstance, { getAuthHeaders, tryRefreshToken } from "../../services/axios";
import type {
  ApiResponse,
  DocumentResponse,
  PresignUploadRequest,
  PresignUploadResponse,
  ImageUrlResponse,
  ImageSummaryResponse,
  DocumentSummaryResponse,
  UUID,
} from "../../types";
import { uploadQueryKeys } from "./query.keys";

export * from "./query.keys";

export async function presignUpload(payload: PresignUploadRequest) {
  const res = await axiosInstance.post<ApiResponse<PresignUploadResponse>>(
    uploadQueryKeys.presign.url,
    payload,
  );
  return res.data;
}

export async function completeUpload(documentId: UUID) {
  const q = uploadQueryKeys.complete(documentId);
  const res = await axiosInstance.post<ApiResponse<DocumentResponse>>(q.url);
  return res.data;
}

export async function getImageUrl(key: string) {
  const q = uploadQueryKeys.imageUrl(key);
  const res = await axiosInstance.get<ApiResponse<ImageUrlResponse>>(q.url);
  return res.data;
}

export async function summarizeImage(key: string, prompt?: string | null) {
  const q = uploadQueryKeys.imageSummary(key);
  const res = await axiosInstance.post<ApiResponse<ImageSummaryResponse>>(q.url, { prompt: prompt ?? null });
  return res.data;
}

export async function streamSummarizeImage(key: string, prompt?: string | null) {
  const q = uploadQueryKeys.imageSummaryStream(key);
  await tryRefreshToken();
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}${q.url}`, {
    method: "POST",
    credentials: "include",
    headers: getAuthHeaders(),
    body: JSON.stringify({ prompt: prompt ?? null }),
  });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  if (!res.body) throw new Error("No response body");
  return res.body;
}

export async function summarizeDocument(key: string, prompt?: string | null) {
  const q = uploadQueryKeys.documentSummary(key);
  const res = await axiosInstance.post<ApiResponse<DocumentSummaryResponse>>(
    q.url,
    { prompt: prompt ?? null },
    { timeout: 90_000 },
  );
  return res.data;
}

export async function streamSummarizeDocument(key: string, prompt?: string | null) {
  const q = uploadQueryKeys.documentSummaryStream(key);
  await tryRefreshToken();
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}${q.url}`, {
    method: "POST",
    credentials: "include",
    headers: getAuthHeaders(),
    body: JSON.stringify({ prompt: prompt ?? null }),
  });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  if (!res.body) throw new Error("No response body");
  return res.body;
}

export async function streamDocumentQa(key: string, question: string) {
  const q = uploadQueryKeys.documentQaStream(key);
  await tryRefreshToken();
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}${q.url}`, {
    method: "POST",
    credentials: "include",
    headers: getAuthHeaders(),
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  if (!res.body) throw new Error("No response body");
  return res.body;
}

import type { UUID } from "../common";

export type PresignUploadRequest = {
  workspaceId: UUID;
  channelId: UUID;
  fileName: string;
  mimeType: string;
  fileSize: number | null;
};

export type PresignUploadResponse = {
  documentId: UUID;
  objectKey: string;
  uploadUrl: string;
};

export type ImageUrlResponse = {
  key: string;
  url: string;
  mimeType: string;
  fileName: string;
};

export type ImageSummaryResponse = {
  key: string;
  summary: string;
};

export type DocumentSummaryResponse = {
  key: string;
  summary: string;
};

export type DocumentQaResponse = {
  key: string;
  question: string;
  answer: string;
};

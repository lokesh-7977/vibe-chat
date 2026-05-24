import type { DateTimeString, JsonValue, UUID } from "../common";

export type DocumentBase = {
  workspaceId: UUID;
  channelId: UUID | null;
  uploadedById: UUID | null;
  fileName: string;
  fileUrl: string;
  mimeType: string;
  fileSize: number | null;
  status: string;
};

export type DocumentCreate = DocumentBase;

export type DocumentUpdate = {
  status: string | null;
};

export type DocumentResponse = DocumentBase & {
  id: UUID;
  createdAt: DateTimeString;
  updatedAt: DateTimeString;
};

export type DocumentChunkBase = {
  documentId: UUID;
  workspaceId: UUID;
  channelId: UUID | null;
  chunkIndex: number;
  content: string;
  tokenCount: number | null;
  metaData: Record<string, JsonValue> | null;
};

export type DocumentChunkCreate = DocumentChunkBase;

export type DocumentChunkUpdate = {
  content: string | null;
  tokenCount: number | null;
  metaData: Record<string, JsonValue> | null;
};

export type DocumentChunkResponse = DocumentChunkBase & {
  id: UUID;
  createdAt: DateTimeString;
};

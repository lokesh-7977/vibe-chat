import type { DateTimeString, UUID } from "../common";

export type DocumentEmbeddingBase = {
  documentChunkId: UUID;
  embedding: number[];
  embeddingModel: string;
};

export type DocumentEmbeddingCreate = DocumentEmbeddingBase;

export type DocumentEmbeddingUpdate = {
  embedding: number[] | null;
  embeddingModel: string | null;
};

export type DocumentEmbeddingResponse = DocumentEmbeddingBase & {
  id: UUID;
  createdAt: DateTimeString;
};

export type ActivityEmbeddingBase = {
  activityId: UUID;
  workspaceId: UUID;
  channelId: UUID | null;
  embedding: number[];
  embeddingModel: string;
};

export type ActivityEmbeddingCreate = ActivityEmbeddingBase;

export type ActivityEmbeddingUpdate = {
  embedding: number[] | null;
  embeddingModel: string | null;
};

export type ActivityEmbeddingResponse = ActivityEmbeddingBase & {
  id: UUID;
  createdAt: DateTimeString;
};

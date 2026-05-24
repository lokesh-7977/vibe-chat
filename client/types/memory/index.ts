import type { DateTimeString, JsonValue, UUID } from "../common";

export type ContextualMemoryBase = {
  workspaceId: UUID;
  channelId: UUID | null;
  userId: UUID | null;
  scope: string;
  memoryType: string;
  content: string;
  metaData: Record<string, JsonValue> | null;
};

export type ContextualMemoryCreate = ContextualMemoryBase;

export type ContextualMemoryUpdate = {
  scope: string | null;
  memoryType: string | null;
  content: string | null;
  metaData: Record<string, JsonValue> | null;
};

export type ContextualMemoryResponse = ContextualMemoryBase & {
  id: UUID;
  createdAt: DateTimeString;
  updatedAt: DateTimeString;
  deletedAt: DateTimeString | null;
};

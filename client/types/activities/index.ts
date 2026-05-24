import type { DateTimeString, JsonValue, UUID } from "../common";

export type ActivityBase = {
  workspaceId: UUID;
  channelId: UUID;
  actorId: UUID | null;
  activityType: string;
  content: string | null;
  metaData: Record<string, JsonValue> | null;
  parentActivityId: UUID | null;
};

export type ActivityCreate = ActivityBase;

export type ActivityCreateRequest = {
  content: string;
  activityType: string;
  metaData: Record<string, JsonValue> | null;
  parentActivityId: UUID | null;
};

export type ActivityUpdate = {
  content: string | null;
  metaData: Record<string, JsonValue> | null;
};

export type ActivityResponse = ActivityBase & {
  id: UUID;
  createdAt: DateTimeString;
  updatedAt: DateTimeString;
  deletedAt: DateTimeString | null;
  actorName: string | null;
};

import type { DateTimeString, UUID } from "../common";

export type DecisionBase = {
  workspaceId: UUID;
  channelId: UUID | null;
  title: string;
  description: string | null;
  reason: string | null;
  createdById: UUID | null;
  sourceActivityId: UUID | null;
};

export type DecisionCreate = DecisionBase;

export type DecisionUpdate = {
  title: string | null;
  description: string | null;
  reason: string | null;
};

export type DecisionResponse = DecisionBase & {
  id: UUID;
  createdAt: DateTimeString;
};

import type { DateTimeString, UUID } from "../common";

export type TaskBase = {
  workspaceId: UUID;
  channelId: UUID | null;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  assigneeId: UUID | null;
  createdById: UUID | null;
  sourceActivityId: UUID | null;
  dueDate: DateTimeString | null;
};

export type TaskCreate = TaskBase;

export type TaskUpdate = {
  title: string | null;
  description: string | null;
  status: string | null;
  priority: string | null;
  assigneeId: UUID | null;
  dueDate: DateTimeString | null;
};

export type TaskResponse = TaskBase & {
  id: UUID;
  createdAt: DateTimeString;
  updatedAt: DateTimeString;
};

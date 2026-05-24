import type { DateTimeString, UUID } from "../common";

export type WorkspaceBase = {
  name: string;
  description: string | null;
};

export type WorkspaceCreate = WorkspaceBase;

export type WorkspaceUpdate = {
  name: string | null;
  description: string | null;
};

export type WorkspaceResponse = WorkspaceBase & {
  id: UUID;
  slug: string;
  ownerId: UUID;
  createdAt: DateTimeString;
  updatedAt: DateTimeString;
};

export type WorkspaceMemberBase = {
  workspaceId: UUID;
  userId: UUID;
  role: string;
};

export type WorkspaceMemberCreate = WorkspaceMemberBase;

export type WorkspaceMemberUpdate = {
  role: string | null;
};

export type WorkspaceMemberResponse = WorkspaceMemberBase & {
  id: UUID;
  joinedAt: DateTimeString;
};

import type { DateTimeString, UUID } from "../common";

export type ChannelBase = {
  workspaceId: UUID;
  name: string;
  slug: string;
  description: string | null;
  channelType: string;
  createdById: UUID | null;
};

export type ChannelCreate = ChannelBase;

export type ChannelUpdate = {
  name: string | null;
  slug: string | null;
  description: string | null;
  channelType: string | null;
};

export type ChannelResponse = ChannelBase & {
  id: UUID;
  createdAt: DateTimeString;
  updatedAt: DateTimeString;
};

export type ChannelMemberBase = {
  channelId: UUID;
  userId: UUID;
  role: string;
};

export type ChannelMemberCreate = ChannelMemberBase;

export type ChannelMemberUpdate = {
  role: string | null;
};

export type ChannelMemberResponse = ChannelMemberBase & {
  id: UUID;
  joinedAt: DateTimeString;
};

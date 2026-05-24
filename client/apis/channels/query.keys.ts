import type { QueryKey } from "@tanstack/react-query";

export type QueryDef<TKey extends QueryKey = QueryKey> = {
  key: TKey;
  url: string;
};

export const channelQueryKeys = {
  list: (workspaceId: string): QueryDef<readonly ["channels", "list", string]> => ({
    key: ["channels", "list", workspaceId] as const,
    url: "/channels",
  }),
  create: {
    key: ["channels", "create"] as const,
    url: "/channels",
  },
  get: (channelId: string): QueryDef<readonly ["channels", "get", string]> => ({
    key: ["channels", "get", channelId] as const,
    url: `/channels/${channelId}`,
  }),
  update: (channelId: string): QueryDef<readonly ["channels", "update", string]> => ({
    key: ["channels", "update", channelId] as const,
    url: `/channels/${channelId}`,
  }),
  delete: (channelId: string): QueryDef<readonly ["channels", "delete", string]> => ({
    key: ["channels", "delete", channelId] as const,
    url: `/channels/${channelId}`,
  }),
  listMembers: (
    channelId: string,
  ): QueryDef<readonly ["channels", "members", "list", string]> => ({
    key: ["channels", "members", "list", channelId] as const,
    url: `/channels/${channelId}/members`,
  }),
  addMember: {
    key: ["channels", "members", "add"] as const,
    url: "/channels/members",
  },
  removeMember: (
    channelId: string,
    userId: string,
  ): QueryDef<readonly ["channels", "members", "remove", string, string]> => ({
    key: ["channels", "members", "remove", channelId, userId] as const,
    url: `/channels/${channelId}/members/${userId}`,
  }),
  listDocuments: (
    channelId: string,
    limit = 50,
    offset = 0,
  ): QueryDef<readonly ["channels", "documents", "list", string, number, number]> => ({
    key: ["channels", "documents", "list", channelId, limit, offset] as const,
    url: `/channels/${channelId}/documents?limit=${limit}&offset=${offset}`,
  }),
} as const;

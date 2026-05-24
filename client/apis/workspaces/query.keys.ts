import type { QueryKey } from "@tanstack/react-query";

export type QueryDef<TKey extends QueryKey = QueryKey> = {
  key: TKey;
  url: string;
};

export const workspaceQueryKeys = {
  create: {
    key: ["workspaces", "create"] as const,
    url: "/workspaces",
  },
  list: {
    key: ["workspaces", "list"] as const,
    url: "/workspaces",
  },
  get: (workspaceId: string): QueryDef<readonly ["workspaces", "get", string]> => ({
    key: ["workspaces", "get", workspaceId] as const,
    url: `/workspaces/${workspaceId}`,
  }),
  update: (workspaceId: string): QueryDef<readonly ["workspaces", "update", string]> => ({
    key: ["workspaces", "update", workspaceId] as const,
    url: `/workspaces/${workspaceId}`,
  }),
  delete: (workspaceId: string): QueryDef<readonly ["workspaces", "delete", string]> => ({
    key: ["workspaces", "delete", workspaceId] as const,
    url: `/workspaces/${workspaceId}`,
  }),
  listMembers: (workspaceId: string): QueryDef<readonly ["workspaces", "members", "list", string]> => ({
    key: ["workspaces", "members", "list", workspaceId] as const,
    url: `/workspaces/${workspaceId}/members`,
  }),
  addMember: (workspaceId: string): QueryDef<readonly ["workspaces", "members", "add", string]> => ({
    key: ["workspaces", "members", "add", workspaceId] as const,
    url: `/workspaces/${workspaceId}/members`,
  }),
} as const;


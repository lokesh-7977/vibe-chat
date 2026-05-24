import type { QueryKey } from "@tanstack/react-query";

export type QueryDef<TKey extends QueryKey = QueryKey> = {
  key: TKey;
  url: string;
};

export const activityQueryKeys = {
  createForChannel: (
    channelId: string,
  ): QueryDef<readonly ["activities", "create", string]> => ({
    key: ["activities", "create", channelId] as const,
    url: `/channels/${channelId}/activities`,
  }),
  listForChannel: (
    channelId: string,
    limit = 50,
    offset = 0,
  ): QueryDef<readonly ["activities", "list", string]> => ({
    key: ["activities", "list", channelId] as const,
    url: `/channels/${channelId}/activities?limit=${limit}&offset=${offset}`,
  }),
  get: (activityId: string): QueryDef<readonly ["activities", "get", string]> => ({
    key: ["activities", "get", activityId] as const,
    url: `/activities/${activityId}`,
  }),
  update: (activityId: string): QueryDef<readonly ["activities", "update", string]> => ({
    key: ["activities", "update", activityId] as const,
    url: `/activities/${activityId}`,
  }),
  delete: (activityId: string): QueryDef<readonly ["activities", "delete", string]> => ({
    key: ["activities", "delete", activityId] as const,
    url: `/activities/${activityId}`,
  }),
} as const;

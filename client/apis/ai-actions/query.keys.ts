import type { QueryKey } from "@tanstack/react-query";

export type QueryDef<TKey extends QueryKey = QueryKey> = {
  key: TKey;
  url: string;
};

export const aiActionQueryKeys = {
  stream: (channelId: string): QueryDef<readonly ["aiActions", "stream", string]> => ({
    key: ["aiActions", "stream", channelId] as const,
    url: `/channels/${channelId}/ai/actions/stream`,
  }),
} as const;


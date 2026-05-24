import type { QueryKey } from "@tanstack/react-query";

export type QueryDef<TKey extends QueryKey = QueryKey> = {
  key: TKey;
  url: string;
};

export const healthQueryKeys = {
  root: {
    key: ["health", "root"] as const,
    url: "/",
  },
} as const;


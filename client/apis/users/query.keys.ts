import type { QueryKey } from "@tanstack/react-query";

export type QueryDef<TKey extends QueryKey = QueryKey> = {
  key: TKey;
  url: string;
};

export const userQueryKeys = {
  list: {
    key: ["users", "list"] as const,
    url: "/users",
  },
} as const;

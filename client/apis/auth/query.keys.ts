import type { QueryKey } from "@tanstack/react-query";

export type QueryDef<TKey extends QueryKey = QueryKey> = {
  key: TKey;
  url: string;
};

export const authQueryKeys = {
  register: {
    key: ["auth", "register"] as const,
    url: "/auth/register",
  },
  login: {
    key: ["auth", "login"] as const,
    url: "/auth/login",
  },
  refresh: {
    key: ["auth", "refresh"] as const,
    url: "/auth/refresh",
  },
  getProfile: {
    key: ["auth", "getProfile"] as const,
    url: "/auth/get-profile",
  },
  deleteAccount: {
    key: ["auth", "deleteAccount"] as const,
    url: "/auth/delete-account",
  },
  logout: {
    key: ["auth", "logout"] as const,
    url: "/auth/logout",
  },
  updateProfile: {
    key: ["auth", "updateProfile"] as const,
    url: "/auth/update-profile",
  },
} as const;


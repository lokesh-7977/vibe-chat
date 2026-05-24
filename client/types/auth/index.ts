import type { UserResponse } from "../user";

export type AuthTokensResponse = {
  accessToken: string;
  user: UserResponse;
};

export type RefreshTokenResponse = {
  accessToken: string;
};

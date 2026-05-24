import axiosInstance from "../../services/axios";
import type {
  ApiResponse,
  AuthTokensResponse,
  RefreshTokenResponse,
  UserCreate,
  UserLogin,
  UserResponse,
  UserUpdate,
} from "../../types";
import { authQueryKeys } from "./query.keys";

export * from "./query.keys";

export async function registerUser(payload: UserCreate) {
  const res = await axiosInstance.post<ApiResponse<AuthTokensResponse>>(
    authQueryKeys.register.url,
    payload,
  );
  return res.data;
}

export async function loginUser(payload: UserLogin) {
  const res = await axiosInstance.post<ApiResponse<AuthTokensResponse>>(
    authQueryKeys.login.url,
    payload,
  );
  return res.data;
}

export async function refreshToken() {
  const res = await axiosInstance.post<ApiResponse<RefreshTokenResponse>>(
    authQueryKeys.refresh.url,
  );
  return res.data;
}

export async function getProfile() {
  const res = await axiosInstance.get<ApiResponse<UserResponse>>(
    authQueryKeys.getProfile.url,
  );
  return res.data;
}

export async function deleteAccount() {
  const res = await axiosInstance.delete<ApiResponse<null>>(
    authQueryKeys.deleteAccount.url,
  );
  return res.data;
}

export async function logoutUser() {
  const res = await axiosInstance.post<ApiResponse<null>>(
    authQueryKeys.logout.url,
  );
  return res.data;
}

export async function updateProfile(payload: UserUpdate) {
  const res = await axiosInstance.put<ApiResponse<UserResponse>>(
    authQueryKeys.updateProfile.url,
    payload,
  );
  return res.data;
}

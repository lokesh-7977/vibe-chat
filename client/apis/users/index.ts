import axiosInstance from "../../services/axios";
import type { ApiResponse, UserResponse } from "../../types";
import { userQueryKeys } from "./query.keys";

export * from "./query.keys";

export async function listUsers() {
  const res = await axiosInstance.get<ApiResponse<UserResponse[]>>(
    userQueryKeys.list.url,
  );
  return res.data;
}

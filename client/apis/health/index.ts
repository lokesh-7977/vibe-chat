import axiosInstance from "../../services/axios";
import type { HealthResponse } from "../../types";
import { healthQueryKeys } from "./query.keys";

export * from "./query.keys";

export async function getHealth() {
  const res = await axiosInstance.get<HealthResponse>(healthQueryKeys.root.url);
  return res.data;
}

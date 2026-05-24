import axiosInstance from "../../services/axios";
import type {
  ActivityCreateRequest,
  ActivityResponse,
  ActivityUpdate,
  ApiResponse,
  UUID,
} from "../../types";
import { activityQueryKeys } from "./query.keys";

export * from "./query.keys";

export async function createChannelActivity(
  channelId: UUID,
  payload: ActivityCreateRequest,
) {
  const q = activityQueryKeys.createForChannel(channelId);
  const res = await axiosInstance.post<ApiResponse<ActivityResponse>>(
    q.url,
    payload,
  );
  return res.data;
}

export async function listChannelActivities(
  channelId: UUID,
  limit = 50,
  offset = 0,
) {
  const q = activityQueryKeys.listForChannel(channelId, limit, offset);
  const res = await axiosInstance.get<ApiResponse<ActivityResponse[]>>(q.url, {
    params: { limit, offset },
  });
  return res.data;
}

export async function getActivity(activityId: UUID) {
  const q = activityQueryKeys.get(activityId);
  const res = await axiosInstance.get<ApiResponse<ActivityResponse>>(q.url);
  return res.data;
}

export async function updateActivity(
  activityId: UUID,
  payload: ActivityUpdate,
) {
  const q = activityQueryKeys.update(activityId);
  const res = await axiosInstance.patch<ApiResponse<ActivityResponse>>(
    q.url,
    payload,
  );
  return res.data;
}

export async function deleteActivity(activityId: UUID) {
  const q = activityQueryKeys.delete(activityId);
  const res = await axiosInstance.delete<ApiResponse<null>>(q.url);
  return res.data;
}

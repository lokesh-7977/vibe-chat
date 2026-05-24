import axiosInstance from "../../services/axios";
import type {
  ApiResponse,
  ChannelCreate,
  ChannelMemberCreate,
  ChannelMemberResponse,
  ChannelResponse,
  ChannelUpdate,
  DocumentResponse,
  UUID,
} from "../../types";
import { channelQueryKeys } from "./query.keys";

export * from "./query.keys";

export async function listChannels(workspaceId: UUID) {
  const q = channelQueryKeys.list(workspaceId);
  const res = await axiosInstance.get<ApiResponse<ChannelResponse[]>>(q.url, {
    params: { workspaceId },
  });
  return res.data;
}

export async function createChannel(payload: ChannelCreate) {
  const res = await axiosInstance.post<ApiResponse<ChannelResponse>>(
    channelQueryKeys.create.url,
    payload,
  );
  return res.data;
}

export async function getChannel(channelId: UUID) {
  const q = channelQueryKeys.get(channelId);
  const res = await axiosInstance.get<ApiResponse<ChannelResponse>>(q.url);
  return res.data;
}

export async function updateChannel(channelId: UUID, payload: ChannelUpdate) {
  const q = channelQueryKeys.update(channelId);
  const res = await axiosInstance.patch<ApiResponse<ChannelResponse>>(
    q.url,
    payload,
  );
  return res.data;
}

export async function deleteChannel(channelId: UUID) {
  const q = channelQueryKeys.delete(channelId);
  const res = await axiosInstance.delete<ApiResponse<null>>(q.url);
  return res.data;
}

export async function listChannelMembers(channelId: UUID) {
  const q = channelQueryKeys.listMembers(channelId);
  const res = await axiosInstance.get<ApiResponse<ChannelMemberResponse[]>>(
    q.url,
  );
  return res.data;
}

export async function addChannelMember(payload: ChannelMemberCreate) {
  const res = await axiosInstance.post<ApiResponse<ChannelMemberResponse>>(
    channelQueryKeys.addMember.url,
    payload,
  );
  return res.data;
}

export async function removeChannelMember(channelId: UUID, userId: UUID) {
  const q = channelQueryKeys.removeMember(channelId, userId);
  const res = await axiosInstance.delete<ApiResponse<null>>(q.url);
  return res.data;
}

export async function listChannelDocuments(
  channelId: UUID,
  limit = 50,
  offset = 0,
) {
  const q = channelQueryKeys.listDocuments(channelId, limit, offset);
  const res = await axiosInstance.get<ApiResponse<DocumentResponse[]>>(q.url, {
    params: { limit, offset },
  });
  return res.data;
}

import axiosInstance from "../../services/axios";
import type {
  ApiResponse,
  UUID,
  WorkspaceCreate,
  WorkspaceMemberCreate,
  WorkspaceMemberResponse,
  WorkspaceResponse,
  WorkspaceUpdate,
} from "../../types";
import { workspaceQueryKeys } from "./query.keys";

export * from "./query.keys";

export async function createWorkspace(payload: WorkspaceCreate) {
  const res = await axiosInstance.post<ApiResponse<WorkspaceResponse>>(
    workspaceQueryKeys.create.url,
    payload,
  );
  return res.data;
}

export async function listWorkspaces() {
  const res = await axiosInstance.get<ApiResponse<WorkspaceResponse[]>>(
    workspaceQueryKeys.list.url,
  );
  return res.data;
}

export async function getWorkspace(workspaceId: UUID) {
  const q = workspaceQueryKeys.get(workspaceId);
  const res = await axiosInstance.get<ApiResponse<WorkspaceResponse>>(q.url);
  return res.data;
}

export async function updateWorkspace(
  workspaceId: UUID,
  payload: WorkspaceUpdate,
) {
  const q = workspaceQueryKeys.update(workspaceId);
  const res = await axiosInstance.patch<ApiResponse<WorkspaceResponse>>(
    q.url,
    payload,
  );
  return res.data;
}

export async function deleteWorkspace(workspaceId: UUID) {
  const q = workspaceQueryKeys.delete(workspaceId);
  const res = await axiosInstance.delete<ApiResponse<null>>(q.url);
  return res.data;
}

export async function listWorkspaceMembers(workspaceId: UUID) {
  const q = workspaceQueryKeys.listMembers(workspaceId);
  const res = await axiosInstance.get<ApiResponse<WorkspaceMemberResponse[]>>(
    q.url,
  );
  return res.data;
}

export async function addWorkspaceMember(
  workspaceId: UUID,
  payload: WorkspaceMemberCreate,
) {
  const q = workspaceQueryKeys.addMember(workspaceId);
  const res = await axiosInstance.post<ApiResponse<WorkspaceMemberResponse>>(
    q.url,
    payload,
  );
  return res.data;
}

export async function removeWorkspaceMember(workspaceId: UUID, userId: UUID) {
  const q = workspaceQueryKeys.removeMember(workspaceId, userId);
  const res = await axiosInstance.delete<ApiResponse<null>>(q.url);
  return res.data;
}

"use client";

import { useCallback, useEffect, useState } from "react";
import { LoaderCircle, Plus, UserRound, X, Crown } from "lucide-react";

import { listUsers } from "@/apis/users";
import { addWorkspaceMember, listWorkspaceMembers, removeWorkspaceMember } from "@/apis/workspaces";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useToast } from "@/providers/toast-provider";
import { useAppSelector } from "@/store/hooks";
import type { UUID, UserResponse, WorkspaceMemberResponse } from "@/types";

export function AddMemberDialog({
  open,
  onClose,
  workspaceId,
}: {
  open: boolean;
  onClose: () => void;
  workspaceId: UUID;
}) {
  const { toast } = useToast();
  const currentUserId = useAppSelector((s) => s.auth.user?.id);
  const workspaceOwnerId = useAppSelector((s) => {
    const ws = s.chats.workspaces.find((w) => w.id === workspaceId);
    return ws?.ownerId;
  });
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [members, setMembers] = useState<WorkspaceMemberResponse[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [actionId, setActionId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [userRes, memberRes] = await Promise.all([
        listUsers(),
        listWorkspaceMembers(workspaceId),
      ]);
      setUsers(userRes.data ?? []);
      setMembers(memberRes.data ?? []);
    } catch {
      toast({ title: "Failed to load users", kind: "error" });
    } finally {
      setLoading(false);
    }
  }, [workspaceId, toast]);

  useEffect(() => {
    if (open) load();
  }, [open, load]);

  async function handleAdd(userId: UUID) {
    setActionId(userId);
    try {
      await addWorkspaceMember(workspaceId, {
        workspaceId,
        userId,
        role: "member",
      });
      setMembers((prev) => [
        ...prev,
        { id: crypto.randomUUID(), workspaceId, userId, role: "member", joinedAt: new Date().toISOString() },
      ]);
      toast({ title: "Member added", kind: "success" });
    } catch {
      toast({ title: "Failed to add member", kind: "error" });
    } finally {
      setActionId(null);
    }
  }

  async function handleRemove(userId: UUID) {
    setActionId(userId);
    try {
      await removeWorkspaceMember(workspaceId, userId);
      setMembers((prev) => prev.filter((m) => m.userId !== userId));
      toast({ title: "Member removed", kind: "success" });
    } catch {
      toast({ title: "Failed to remove member", kind: "error" });
    } finally {
      setActionId(null);
    }
  }

  const memberUserIds = new Set(members.map((m) => m.userId));

  const userMap = new Map(users.map((u) => [u.id, u]));

  const filteredMembers = members.filter((m) => {
    const user = userMap.get(m.userId);
    if (!user) return false;
    const q = search.toLowerCase();
    return user.fullName.toLowerCase().includes(q) || user.email.toLowerCase().includes(q);
  });

  const filteredOthers = users.filter(
    (u) =>
      !memberUserIds.has(u.id) &&
      (u.fullName.toLowerCase().includes(search.toLowerCase()) ||
        u.email.toLowerCase().includes(search.toLowerCase())),
  );

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add members</DialogTitle>
          <DialogDescription>
            Select users to add to this workspace.
          </DialogDescription>
        </DialogHeader>

        <Input
          className="h-10"
          placeholder="Search users..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          autoFocus
        />

        <div className="max-h-72 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <LoaderCircle className="size-5 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              {filteredMembers.length > 0 && (
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground uppercase tracking-wider px-1 mt-2">
                    Current members ({filteredMembers.length})
                  </p>
                  <div className="space-y-1">
                    {filteredMembers.map((m) => {
                      const user = userMap.get(m.userId);
                      if (!user) return null;
                      const isOwner = m.userId === workspaceOwnerId;
                      const isSelf = m.userId === currentUserId;
                      return (
                        <div
                          key={m.id}
                          className="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-whatsapp-surface transition-colors"
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-whatsapp-muted">
                              <UserRound className="size-4 text-muted-foreground" />
                            </span>
                            <div className="min-w-0">
                              <p className="truncate text-sm font-medium">
                                {user.fullName}
                              </p>
                              <p className="truncate text-xs text-muted-foreground">
                                {user.email}
                              </p>
                            </div>
                          </div>
                          {isOwner ? (
                            <span className="flex shrink-0 items-center gap-1 text-xs text-muted-foreground ml-2">
                              <Crown className="size-3.5" />
                              Owner
                            </span>
                          ) : isSelf ? (
                            <span className="text-xs text-muted-foreground ml-2">You</span>
                          ) : (
                            <Button
                              size="sm"
                              variant="ghost"
                              className="shrink-0 ml-2 text-muted-foreground hover:text-destructive"
                              disabled={actionId === m.userId}
                              onClick={() => handleRemove(m.userId)}
                            >
                              {actionId === m.userId ? (
                                <LoaderCircle className="size-3.5 animate-spin" />
                              ) : (
                                <X className="size-3.5" />
                              )}
                            </Button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {filteredOthers.length > 0 && (
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground uppercase tracking-wider px-1 mt-2">
                    Add members
                  </p>
                  <div className="space-y-1">
                    {filteredOthers.map((user) => (
                      <div
                        key={user.id}
                        className="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-whatsapp-surface transition-colors"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-whatsapp-muted">
                            <UserRound className="size-4 text-muted-foreground" />
                          </span>
                          <div className="min-w-0">
                            <p className="truncate text-sm font-medium">
                              {user.fullName}
                            </p>
                            <p className="truncate text-xs text-muted-foreground">
                              {user.email}
                            </p>
                          </div>
                        </div>
                        <Button
                          size="sm"
                          className="gap-1.5 shrink-0 ml-2"
                          disabled={actionId === user.id}
                          onClick={() => handleAdd(user.id)}
                        >
                          {actionId === user.id ? (
                            <LoaderCircle className="size-3.5 animate-spin" />
                          ) : (
                            <Plus className="size-3.5" />
                          )}
                          Add
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {filteredMembers.length === 0 && filteredOthers.length === 0 && (
                <p className="py-8 text-center text-sm text-muted-foreground">
                  No users found.
                </p>
              )}
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

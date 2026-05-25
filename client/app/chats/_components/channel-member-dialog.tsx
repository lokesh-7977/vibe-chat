"use client";

import { useCallback, useEffect, useState } from "react";
import { Crown, LoaderCircle, Plus, UserRound, X } from "lucide-react";

import { addChannelMember, listChannelMembers, removeChannelMember } from "@/apis/channels";
import { listUsers } from "@/apis/users";
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
import type { ChannelMemberResponse, UUID, UserResponse } from "@/types";

export function ChannelMemberDialog({
  open,
  onClose,
  channelId,
  channelName,
}: {
  open: boolean;
  onClose: () => void;
  channelId: UUID;
  channelName: string;
}) {
  const { toast } = useToast();
  const currentUserId = useAppSelector((s) => s.auth.user?.id);
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [channelMembers, setChannelMembers] = useState<ChannelMemberResponse[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [actionId, setActionId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [userRes, memberRes] = await Promise.all([
        listUsers(),
        listChannelMembers(channelId),
      ]);
      setUsers(userRes.data ?? []);
      setChannelMembers(memberRes.data ?? []);
    } catch {
      toast({ title: "Failed to load", kind: "error" });
    } finally {
      setLoading(false);
    }
  }, [channelId, toast]);

  useEffect(() => {
    if (open) load();
  }, [open, load]);

  const memberUserIds = new Set(channelMembers.map((m) => m.userId));

  async function handleAdd(userId: UUID) {
    setActionId(userId);
    try {
      await addChannelMember({ channelId, userId, role: "member" });
      setChannelMembers((prev) => [
        ...prev,
        { id: crypto.randomUUID(), channelId, userId, role: "member", joinedAt: new Date().toISOString() },
      ]);
      toast({ title: "Member added to channel", kind: "success" });
    } catch {
      toast({ title: "Failed to add member", kind: "error" });
    } finally {
      setActionId(null);
    }
  }

  async function handleRemove(userId: UUID) {
    setActionId(userId);
    try {
      await removeChannelMember(channelId, userId);
      setChannelMembers((prev) => prev.filter((m) => m.userId !== userId));
      toast({ title: "Member removed from channel", kind: "success" });
    } catch {
      toast({ title: "Failed to remove member", kind: "error" });
    } finally {
      setActionId(null);
    }
  }

  const userMap = new Map(users.map((u) => [u.id, u]));

  const filteredMembers = channelMembers.filter((m) => {
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
          <DialogTitle>Channel members</DialogTitle>
          <DialogDescription>
            Manage members for <span className="font-medium">#{channelName}</span>
          </DialogDescription>
        </DialogHeader>

        <Input
          className="h-10"
          placeholder="Search members..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          autoFocus
        />

        <div className="max-h-80 overflow-y-auto space-y-3">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <LoaderCircle className="size-5 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              {filteredMembers.length > 0 && (
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground uppercase tracking-wider px-1">
                    Current members ({filteredMembers.length})
                  </p>
                  <div className="space-y-0.5">
                    {filteredMembers.map((m) => {
                      const user = userMap.get(m.userId);
                      if (!user) return null;
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
                          {m.role === "owner" ? (
                            <span className="flex shrink-0 items-center gap-1 text-xs text-muted-foreground ml-2">
                              <Crown className="size-3.5" />
                              Owner
                            </span>
                          ) : m.userId === currentUserId ? (
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
                  <p className="mb-1 text-xs font-medium text-muted-foreground uppercase tracking-wider px-1">
                    Add members
                  </p>
                  <div className="space-y-0.5">
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

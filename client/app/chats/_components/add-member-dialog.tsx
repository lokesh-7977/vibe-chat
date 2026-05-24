"use client";

import { useCallback, useEffect, useState } from "react";
import { LoaderCircle, Plus, UserRound } from "lucide-react";

import { listUsers } from "@/apis/users";
import { addWorkspaceMember, listWorkspaceMembers } from "@/apis/workspaces";
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
import type { UUID, UserResponse } from "@/types";

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
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [memberIds, setMemberIds] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [adding, setAdding] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [userRes, memberRes] = await Promise.all([
        listUsers(),
        listWorkspaceMembers(workspaceId),
      ]);
      setUsers(userRes.data ?? []);
      setMemberIds(new Set((memberRes.data ?? []).map((m) => m.userId)));
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
    setAdding(userId);
    try {
      await addWorkspaceMember(workspaceId, {
        workspaceId,
        userId,
        role: "member",
      });
      setMemberIds((prev) => new Set(prev).add(userId));
      toast({ title: "Member added", kind: "success" });
    } catch {
      toast({ title: "Failed to add member", kind: "error" });
    } finally {
      setAdding(null);
    }
  }

  const filtered = users.filter(
    (u) =>
      u.fullName.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase()),
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
          ) : filtered.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No users found.
            </p>
          ) : (
            <div className="mt-2 space-y-1">
              {filtered.map((user) => {
                const isMember = memberIds.has(user.id);
                return (
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
                      disabled={isMember || adding === user.id}
                      onClick={() => handleAdd(user.id)}
                    >
                      {adding === user.id ? (
                        <LoaderCircle className="size-3.5 animate-spin" />
                      ) : (
                        <Plus className="size-3.5" />
                      )}
                      {isMember ? "Added" : "Add"}
                    </Button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

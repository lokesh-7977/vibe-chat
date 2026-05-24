"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import {
  Check,
  ChevronDown,
  Hash,
  MessageCircle,
  MoreVertical,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Settings,
  Trash2,
  UserPlus,
} from "lucide-react";

import { getProfile } from "@/apis/auth";
import type { Room } from "@/types/chats";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import {
  deleteChannelThunk,
  selectRoom,
  switchWorkspace,
  updateChannelThunk,
} from "@/store/slices/chats-slice";
import { updateUser } from "@/store/slices/auth-slice";
import { AddMemberDialog } from "./add-member-dialog";
import { useToast } from "@/providers/toast-provider";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

export function RoomList({
  rooms,
  onCreateWorkspace,
  onCreateChannel,
  onRefresh,
  onOpenSettings,
}: {
  rooms: Room[];
  onCreateWorkspace: () => void;
  onCreateChannel: () => void;
  onRefresh: () => void;
  onOpenSettings: () => void;
}) {
  const { toast } = useToast();
  const [showAddMember, setShowAddMember] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedSearch = useDebounce(searchQuery, 200);
  const dispatch = useAppDispatch();
  const selectedRoomId = useAppSelector((s) => s.chats.selectedRoomId);
  const workspaces = useAppSelector((s) => s.chats.workspaces);
  const currentWorkspaceId = useAppSelector((s) => s.chats.currentWorkspaceId);
  const isLoading = useAppSelector((s) => s.chats.status === "loading");
  const user = useAppSelector((s) => s.auth.user);
  const [wsOpen, setWsOpen] = useState(false);
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [deleteDialog, setDeleteDialog] = useState<{
    id: string;
    name: string;
  } | null>(null);
  const [editDialog, setEditDialog] = useState<{
    id: string;
    name: string;
    description: string;
  } | null>(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);

  useEffect(() => {
    if (!user) {
      getProfile()
        .then((res) => {
          if (res.data) dispatch(updateUser(res.data));
        })
        .catch(() => {});
    }
  }, [user, dispatch]);
  const wsRef = useRef<HTMLDivElement>(null);

  const currentWs = workspaces.find((w) => w.id === currentWorkspaceId);

  const filteredRooms = useMemo(() => {
    if (!debouncedSearch) return rooms;
    const q = debouncedSearch.toLowerCase();
    return rooms.filter(
      (r) =>
        r.name.toLowerCase().includes(q) ||
        r.description.toLowerCase().includes(q),
    );
  }, [rooms, debouncedSearch]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (wsRef.current && !wsRef.current.contains(e.target as Node))
        setWsOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  async function confirmDelete() {
    if (!deleteDialog) return;
    const { id, name } = deleteDialog;
    try {
      await dispatch(deleteChannelThunk(id)).unwrap();
      toast({ title: `Deleted #${name}`, kind: "success" });
    } catch (err) {
      toast({
        title: "Failed to delete channel",
        description: err instanceof Error ? err.message : "Unknown error",
        kind: "error",
      });
    } finally {
      setDeleteDialog(null);
      setMenuOpenId(null);
    }
  }

  async function confirmEdit() {
    if (!editDialog) return;
    const nextName = editName.trim();
    const nextDesc = editDescription.trim();
    if (!nextName) {
      toast({ title: "Channel name required", kind: "error" });
      return;
    }
    setSavingEdit(true);
    try {
      await dispatch(
        updateChannelThunk({
          channelId: editDialog.id,
          name: nextName,
          description: nextDesc,
        }),
      ).unwrap();
      toast({ title: `Updated #${nextName}`, kind: "success" });
      setEditDialog(null);
      setMenuOpenId(null);
    } catch (err) {
      toast({
        title: "Failed to update channel",
        description: err instanceof Error ? err.message : "Unknown error",
        kind: "error",
      });
    } finally {
      setSavingEdit(false);
    }
  }

  return (
    <>
      {currentWorkspaceId && (
        <AddMemberDialog
          open={showAddMember}
          onClose={() => setShowAddMember(false)}
          workspaceId={currentWorkspaceId}
        />
      )}
      <Dialog
        open={Boolean(deleteDialog)}
        onOpenChange={(open) => {
          if (!open) setDeleteDialog(null);
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Delete channel?</DialogTitle>
            <DialogDescription>
              This will permanently delete{" "}
              <span className="font-medium text-foreground">
                #{deleteDialog?.name ?? ""}
              </span>{" "}
              and its messages.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <button
              type="button"
              className="inline-flex h-9 items-center justify-center rounded-lg border border-whatsapp-border bg-card px-4 text-sm font-medium hover:bg-whatsapp-muted"
              onClick={() => setDeleteDialog(null)}
            >
              Cancel
            </button>
            <button
              type="button"
              className="inline-flex h-9 items-center justify-center rounded-lg bg-red-600 px-4 text-sm font-medium text-white hover:bg-red-600/90"
              onClick={confirmDelete}
            >
              Yes, delete
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={Boolean(editDialog)}
        onOpenChange={(open) => {
          if (!open) setEditDialog(null);
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Edit channel</DialogTitle>
            <DialogDescription>
              Update the channel name and description.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">
                Name
              </label>
              <Input
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                placeholder="Channel name"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-muted-foreground">
                Description
              </label>
              <Input
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                placeholder="What is this channel for?"
              />
            </div>
          </div>

          <DialogFooter>
            <button
              type="button"
              className="inline-flex h-9 items-center justify-center rounded-lg border border-whatsapp-border bg-card px-4 text-sm font-medium hover:bg-whatsapp-muted"
              onClick={() => setEditDialog(null)}
              disabled={savingEdit}
            >
              Cancel
            </button>
            <button
              type="button"
              className="inline-flex h-9 items-center justify-center rounded-lg bg-whatsapp px-4 text-sm font-medium text-whatsapp-foreground hover:bg-whatsapp/90 disabled:opacity-60"
              onClick={confirmEdit}
              disabled={savingEdit}
            >
              Save
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <aside className="flex h-full w-full min-w-0 flex-col border-r border-whatsapp-border bg-card">
        <header className="flex h-14 items-center justify-between border-b border-whatsapp-border bg-whatsapp px-4">
          <div className="flex items-center gap-2">
            <MessageCircle className="size-4 text-whatsapp-foreground" />
            <h1 className="text-xl font-semibold text-whatsapp-foreground">
              Aura Chat
            </h1>
          </div>
          <div className="flex gap-1">
            <Button
              aria-label="Create workspace"
              size="icon-sm"
              variant="ghost"
              className="text-whatsapp-foreground hover:bg-white/20"
              onClick={onCreateWorkspace}
            >
              <Plus className="size-4" />
            </Button>
            <Button
              aria-label="Refresh"
              size="icon-sm"
              variant="ghost"
              className="text-whatsapp-foreground hover:bg-white/20"
              onClick={onRefresh}
              disabled={isLoading}
            >
              <RefreshCw
                className={`size-4 ${isLoading ? "animate-spin" : ""}`}
              />
            </Button>
          </div>
        </header>

        <div
          ref={wsRef}
          className="relative border-b border-whatsapp-border px-3 py-2"
        >
          <button
            type="button"
            className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm font-medium hover:bg-whatsapp-surface transition-colors"
            onClick={() => setWsOpen(!wsOpen)}
          >
            <Hash className="size-3.5 text-whatsapp-deep shrink-0" />
            <span className="truncate flex-1">
              {currentWs?.name ?? "Workspace"}
            </span>
            <ChevronDown
              className={`size-3.5 text-muted-foreground transition-transform ${wsOpen ? "rotate-180" : ""}`}
            />
          </button>

          {wsOpen && (
            <div className="absolute left-2 right-2 top-full z-10 mt-1 rounded-lg border border-whatsapp-border bg-popover p-1 shadow-lg">
              {workspaces.map((ws) => (
                <button
                  key={ws.id}
                  type="button"
                  className="flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm hover:bg-whatsapp-muted transition-colors"
                  onClick={() => {
                    if (ws.id !== currentWorkspaceId)
                      dispatch(switchWorkspace(ws.id));
                    setWsOpen(false);
                  }}
                >
                  <span className="flex size-6 items-center justify-center rounded-full bg-whatsapp text-[10px] font-semibold text-whatsapp-foreground shrink-0">
                    {ws.name.charAt(0).toUpperCase()}
                  </span>
                  <span className="truncate flex-1">{ws.name}</span>
                  {ws.id === currentWorkspaceId && (
                    <Check className="size-3.5 text-whatsapp-deep shrink-0" />
                  )}
                </button>
              ))}
              <div className="border-t border-whatsapp-border mt-1 pt-1 space-y-0.5">
                <button
                  type="button"
                  className="flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm text-muted-foreground hover:bg-whatsapp-muted transition-colors"
                  onClick={() => {
                    setWsOpen(false);
                    onCreateWorkspace();
                  }}
                >
                  <Plus className="size-3.5" />
                  New workspace
                </button>
                {currentWorkspaceId && (
                  <button
                    type="button"
                    className="flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm text-muted-foreground hover:bg-whatsapp-muted transition-colors"
                    onClick={() => {
                      setWsOpen(false);
                      setShowAddMember(true);
                    }}
                  >
                    <UserPlus className="size-3.5" />
                    Add members
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="border-b border-whatsapp-border p-3">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="h-10 border-whatsapp-border bg-whatsapp-surface pl-10"
              placeholder="Search channels..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        <nav className="min-h-0 flex-1 overflow-y-auto p-2">
          <div className="mb-2 flex items-center justify-between px-1">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Channels
            </span>
            <Button
              aria-label="Create channel"
              size="icon-sm"
              variant="ghost"
              className="size-6"
              onClick={onCreateChannel}
            >
              <Hash className="size-3.5" />
            </Button>
          </div>

          {isLoading && filteredRooms.length === 0 ? (
            <div className="space-y-2 px-1">
              {[1, 2, 3, 4, 5].map((i) => (
                <div
                  key={i}
                  className="flex animate-pulse items-center gap-3 rounded-lg p-3"
                >
                  <div className="size-10 shrink-0 rounded-full bg-whatsapp-muted" />
                  <div className="min-w-0 flex-1 space-y-2">
                    <div className="h-3 w-3/4 rounded bg-whatsapp-muted" />
                    <div className="h-2 w-1/2 rounded bg-whatsapp-muted" />
                  </div>
                </div>
              ))}
            </div>
          ) : filteredRooms.length === 0 ? (
            <div className="flex flex-col items-center gap-3 px-4 py-8 text-center">
              {debouncedSearch ? (
                <p className="text-xs text-muted-foreground">
                  No channels match &quot;{debouncedSearch}&quot;
                </p>
              ) : (
                <>
                  <div className="flex flex-col gap-2 w-full max-w-36">
                    <Button
                      size="sm"
                      className="gap-1.5 bg-whatsapp text-whatsapp-foreground hover:bg-whatsapp/90 text-xs w-full"
                      onClick={onCreateWorkspace}
                    >
                      <Plus className="size-3.5" />
                      New workspace
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="gap-1.5 text-xs w-full"
                      onClick={onCreateChannel}
                    >
                      <Hash className="size-3.5" />
                      New channel
                    </Button>
                  </div>
                </>
              )}
            </div>
          ) : (
            filteredRooms.map((room) => {
              const active = room.id === selectedRoomId;

              return (
                <button
                  key={room.id}
                  className={
                    active
                      ? "group flex w-full items-center gap-3 rounded-lg bg-whatsapp-muted p-3 text-left transition-colors"
                      : "group flex w-full items-center gap-3 rounded-lg p-3 text-left transition-colors hover:bg-whatsapp-surface"
                  }
                  type="button"
                  onClick={() => dispatch(selectRoom(room.id))}
                >
                  <span className="relative flex size-10 shrink-0 items-center justify-center rounded-full bg-whatsapp text-xs font-semibold text-whatsapp-foreground">
                    <Hash className="size-4" />
                  </span>
                  <span className="min-w-0 flex-1 border-b border-whatsapp-border/70 pb-2">
                    <span className="flex items-center justify-between gap-3">
                      <span className="truncate text-sm font-semibold">
                        {room.name}
                      </span>
                      <span className="flex items-center gap-2 shrink-0">
                        {room.unread > 0 && (
                          <span className="inline-flex min-w-5 items-center justify-center rounded-full bg-whatsapp px-1.5 text-[10px] font-semibold leading-5 text-whatsapp-foreground">
                            {room.unread > 99 ? "99+" : room.unread}
                          </span>
                        )}
                        <span className="text-xs text-muted-foreground">
                          {room.time}
                        </span>
                        <span className="relative">
                          <button
                            type="button"
                            className={`flex size-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-whatsapp-surface hover:text-foreground ${active || menuOpenId === room.id ? "opacity-100" : "opacity-0 group-hover:opacity-100"}`}
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              setMenuOpenId((v) =>
                                v === room.id ? null : room.id,
                              );
                            }}
                            aria-label="Channel actions"
                            title="Actions"
                          >
                            <MoreVertical className="size-4" />
                          </button>
                          {menuOpenId === room.id && (
                            <>
                              <div
                                className="fixed inset-0 z-10"
                                onClick={() => setMenuOpenId(null)}
                              />
                              <div className="absolute right-0 top-full z-20 mt-1 min-w-40 rounded-lg border border-whatsapp-border bg-popover p-1 shadow-lg">
                                <button
                                  type="button"
                                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-xs hover:bg-whatsapp-muted"
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    setEditDialog({
                                      id: room.id,
                                      name: room.name,
                                      description: room.description,
                                    });
                                    setEditName(room.name);
                                    setEditDescription(room.description);
                                  }}
                                >
                                  <Pencil className="size-3.5" />
                                  Edit channel
                                </button>
                                <button
                                  type="button"
                                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-xs text-red-600 hover:bg-whatsapp-muted"
                                  onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    setDeleteDialog({
                                      id: room.id,
                                      name: room.name,
                                    });
                                  }}
                                >
                                  <Trash2 className="size-3.5" />
                                  Delete channel
                                </button>
                              </div>
                            </>
                          )}
                        </span>
                      </span>
                    </span>
                    <span className="mt-0.5 flex items-center justify-between gap-3">
                      <span className="truncate text-xs text-muted-foreground">
                        {room.description}
                      </span>
                    </span>
                  </span>
                </button>
              );
            })
          )}
        </nav>

        <div className="flex items-center justify-between border-t border-whatsapp-border bg-whatsapp-surface px-3 py-2">
          <div className="flex items-center gap-2 min-w-0">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-whatsapp text-xs font-semibold text-whatsapp-foreground">
              {(user?.fullName ?? "?")[0].toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">
                {user?.fullName ?? user?.email ?? "User"}
              </p>
              {user?.username && (
                <p className="truncate text-xs text-muted-foreground">
                  @{user.username}
                </p>
              )}
            </div>
          </div>
          <div className="flex gap-1">
            <button
              type="button"
              className="flex size-8 items-center justify-center rounded-md text-muted-foreground hover:bg-whatsapp-muted transition-colors"
              onClick={onOpenSettings}
              title="Settings"
            >
              <Settings className="size-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}

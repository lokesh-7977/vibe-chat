"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Hash, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

import { realtimeClient } from "@/services/realtime";
import { store } from "@/store";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { clearTyping, loadChats, receiveRealtimeEvent, setTyping, silentRefreshChats } from "@/store/slices/chats-slice";
import { _translatedContents } from "./translate-dialog";
import { ChatWindow } from "./chat-window";
import { CreateChannelDialog } from "./create-channel-dialog";
import { CreateWorkspaceDialog } from "./create-workspace-dialog";
import { RoomList } from "./room-list";
import { SettingsDialog } from "./settings-dialog";

export default function ChatsShell() {
  const dispatch = useAppDispatch();
  const selectedRoomId = useAppSelector((s) => s.chats.selectedRoomId);
  const rooms = useAppSelector((s) => s.chats.rooms);
  const currentWorkspaceId = useAppSelector((s) => s.chats.currentWorkspaceId);
  const [showWorkspaceDialog, setShowWorkspaceDialog] = useState(false);
  const [showChannelDialog, setShowChannelDialog] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const previousRoomId = useRef<string | null>(null);

  const refresh = useCallback(() => {
    dispatch(loadChats());
  }, [dispatch]);

  useEffect(() => {
    refresh();
    realtimeClient.connect();

    const typingTimeouts = new Map<string, ReturnType<typeof setTimeout>>();
    let silentRefreshTimer: ReturnType<typeof setTimeout> | null = null;

    const unsubscribe = realtimeClient.subscribe((event) => {
      if (event.type === "error") return;
      const channelId = event.channelId ?? event.channel_id;
      if (!channelId) return;

      const state = store.getState();
      const currentUserId = state.auth.user?.id;
      const eventUserId = event.userId ?? event.user_id;

      // typing events — skip own
      if (event.type === "typing_started" && eventUserId) {
        if (eventUserId === currentUserId) return;
        dispatch(setTyping({ channelId, userId: eventUserId }));
        const key = `${channelId}:${eventUserId}`;
        if (typingTimeouts.has(key)) clearTimeout(typingTimeouts.get(key)!);
        typingTimeouts.set(key, setTimeout(() => {
          dispatch(clearTyping({ channelId, userId: eventUserId }));
          typingTimeouts.delete(key);
        }, 4000));
        return;
      }

      if (event.type === "typing_stopped" && eventUserId) {
        if (eventUserId === currentUserId) return;
        dispatch(clearTyping({ channelId, userId: eventUserId }));
        const key = `${channelId}:${eventUserId}`;
        if (typingTimeouts.has(key)) {
          clearTimeout(typingTimeouts.get(key)!);
          typingTimeouts.delete(key);
        }
        return;
      }

      // activity_created — new message from another user or AI
      if (event.type === "activity_created") {
        const activity = (event as unknown as Record<string, unknown>).activity as Record<string, string> | undefined;
        if (!activity?.content) return;
        const actorId = activity.actor_id ?? activity.actorId;
        const activityType = activity.activity_type ?? activity.activityType;
        const isAi = activityType === "ai_message";

        if (isAi) {
          // Never show AI responses inside member chats.
          // TranslateDialog renders results in the dialog itself.
          if (_translatedContents.has(activity.content)) _translatedContents.delete(activity.content);
          return;
        }

        if (actorId && actorId === currentUserId) return; // skip own (already added by sendChatMessage)

        dispatch(
          receiveRealtimeEvent({
            channelId,
            message: {
              id: activity.id ?? crypto.randomUUID(),
              userId: actorId ?? null,
              author: isAi ? "AI Assistant" : (activity.actor_name ?? activity.actorName ?? "Member"),
              role: "member",
              content: activity.content,
              isAi,
              time: new Date().toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              }),
            },
          }),
        );

        // Debounced silent refresh to keep room list in sync
        if (silentRefreshTimer) clearTimeout(silentRefreshTimer);
        silentRefreshTimer = setTimeout(() => {
          store.dispatch(silentRefreshChats());
        }, 2000);

        return;
      }
    });

    return () => {
      unsubscribe();
      realtimeClient.disconnect();
      if (silentRefreshTimer) clearTimeout(silentRefreshTimer);
    };
  }, [dispatch, refresh]);

  useEffect(() => {
    if (!selectedRoomId) return;
    if (previousRoomId.current && previousRoomId.current !== selectedRoomId) {
      realtimeClient.leave(previousRoomId.current);
    }
    realtimeClient.join(selectedRoomId);
    previousRoomId.current = selectedRoomId;
    setSidebarOpen(false);
  }, [selectedRoomId]);

  return (
    <main className="h-screen overflow-hidden bg-whatsapp-surface text-foreground">
      <SettingsDialog
        open={showSettingsDialog}
        onOpenChange={setShowSettingsDialog}
      />

      <CreateWorkspaceDialog
        open={showWorkspaceDialog}
        onClose={() => setShowWorkspaceDialog(false)}
      />

      {currentWorkspaceId && (
        <CreateChannelDialog
          open={showChannelDialog}
          onClose={() => setShowChannelDialog(false)}
          workspaceId={currentWorkspaceId}
        />
      )}

      <div className="flex h-full w-full overflow-hidden bg-whatsapp-surface">
        {/* Mobile sidebar overlay */}
        {sidebarOpen && (
          <div className="fixed inset-0 z-40 bg-black/30 md:hidden" onClick={() => setSidebarOpen(false)} />
        )}
        <div className={`h-full w-80 shrink-0 ${sidebarOpen ? "fixed inset-y-0 left-0 z-50 shadow-xl md:static md:inset-auto md:left-auto md:z-auto md:shadow-none" : "hidden md:static md:flex"} md:flex`}>
          <RoomList
            rooms={rooms}
            onCreateWorkspace={() => setShowWorkspaceDialog(true)}
            onCreateChannel={() => {
              if (currentWorkspaceId) setShowChannelDialog(true);
            }}
            onRefresh={refresh}
            onOpenSettings={() => setShowSettingsDialog(true)}
          />
        </div>
        <div className="min-w-0 flex-1">
          {rooms.length > 0 ? <ChatWindow onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} /> : (
            <div className="flex h-full items-center justify-center">
              <div className="flex flex-col items-center gap-4 text-center">
                <div className="flex size-14 items-center justify-center rounded-2xl bg-whatsapp-muted">
                  <div className="size-6 rounded-lg bg-whatsapp text-whatsapp-foreground flex items-center justify-center">
                    <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium">No channels yet</p>
                  <p className="text-xs text-muted-foreground">Create a workspace or channel to start chatting.</p>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    className="gap-1.5 bg-whatsapp text-whatsapp-foreground hover:bg-whatsapp/90 text-xs"
                    onClick={() => setShowWorkspaceDialog(true)}
                  >
                    <Sparkles className="size-3.5" />
                    New workspace
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="gap-1.5 text-xs"
                    onClick={() => currentWorkspaceId ? setShowChannelDialog(true) : setShowWorkspaceDialog(true)}
                  >
                    <Hash className="size-3.5" />
                    New channel
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

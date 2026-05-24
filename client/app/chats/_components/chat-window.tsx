"use client";

import { useRef, useState } from "react";
import { Menu, MoreVertical, Search, Sparkles, Trash2, Users } from "lucide-react";

import { Button } from "@/components/ui/button";
import axiosInstance from "@/services/axios";
import { useToast } from "@/providers/toast-provider";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { selectRoom, silentRefreshChats } from "@/store/slices/chats-slice";
import { ChannelMemberDialog } from "./channel-member-dialog";
import { ChannelSummarySheet } from "./channel-summary-sheet";
import { ChatComposer } from "./chat-composer";
import { MessageThread } from "./message-thread";
import { SearchDialog } from "./search-dialog";

export function ChatWindow({ onToggleSidebar }: { onToggleSidebar?: () => void }) {
  const dispatch = useAppDispatch();
  const { toast } = useToast();
  const selectedRoomId = useAppSelector((state) => state.chats.selectedRoomId);
  const rooms = useAppSelector((state) => state.chats.rooms);
  const messagesByRoom = useAppSelector((state) => state.chats.messagesByRoom);
  const typingByChannel = useAppSelector((state) => state.chats.typingByChannel);
  const usersById = useAppSelector((state) => state.chats.usersById);
  const [showMembers, setShowMembers] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const room = rooms.find((r) => r.id === selectedRoomId);
  if (!room) return null;
  const messages = messagesByRoom[room.id] ?? [];

  const typingIds = selectedRoomId ? typingByChannel[selectedRoomId] ?? [] : [];
  const typingNames = typingIds
    .map((id) => usersById[id]?.fullName)
    .filter(Boolean);

  async function deleteAllMessages() {
    if (!selectedRoomId) return;
    if (!window.confirm("Delete all messages in this channel? This cannot be undone.")) return;
    setMenuOpen(false);
    try {
      await axiosInstance.delete(`/channels/${selectedRoomId}/messages`);
      dispatch(silentRefreshChats());
      toast({ title: "All messages deleted", kind: "success" });
    } catch {
      toast({ title: "Failed to delete messages", kind: "error" });
    }
  }

  return (
    <section className="flex h-full w-full min-w-0 flex-col bg-whatsapp-surface">
      {selectedRoomId && (
        <ChannelMemberDialog
          open={showMembers}
          onClose={() => setShowMembers(false)}
          channelId={selectedRoomId}
          channelName={room.name}
        />
      )}
      {selectedRoomId && (
        <ChannelSummarySheet
          open={showSummary}
          onOpenChange={setShowSummary}
          channelId={selectedRoomId}
          channelName={room.name}
        />
      )}
      <SearchDialog
        open={showSearch}
        onOpenChange={setShowSearch}
        onSelectChannel={(id) => dispatch(selectRoom(id))}
      />
      <header className="flex h-14 items-center justify-between border-b border-whatsapp-border bg-whatsapp px-4">
        <div className="flex min-w-0 items-center gap-3">
          {onToggleSidebar && (
            <button type="button" className="flex size-8 items-center justify-center rounded-md text-whatsapp-foreground hover:bg-white/20 md:hidden" onClick={onToggleSidebar} aria-label="Open sidebar">
              <Menu className="size-5" />
            </button>
          )}
          <div className="relative flex size-10 shrink-0 items-center justify-center rounded-full bg-whatsapp-soft text-sm font-semibold text-whatsapp-deep">
            {room.avatar}
            {room.online && (
              <span className="absolute bottom-0 right-0 size-3 rounded-full border-2 border-card bg-whatsapp" />
            )}
          </div>
          <div className="min-w-0">
            <h2 className="truncate text-base font-semibold text-whatsapp-foreground">{room.name}</h2>
            <p className="truncate text-sm text-whatsapp-foreground/80">
              {room.online ? "online" : room.description}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button
            aria-label="Manage members"
            size="icon-sm"
            variant="ghost"
            className="text-whatsapp-foreground hover:bg-white/20"
            onClick={() => setShowMembers(true)}
          >
            <Users className="size-4" />
          </Button>
          <Button
            aria-label="Summarize chat"
            className="h-8 gap-1.5 rounded-full border border-white/35 bg-white/15 px-3 text-xs text-whatsapp-foreground hover:border-white/55 hover:bg-white/25 focus-visible:border-white/60 focus-visible:ring-3 focus-visible:ring-white/30"
            size="sm"
            variant="ghost"
            onClick={() => setShowSummary(true)}
          >
            <Sparkles className="size-3.5" />
            Summarize
          </Button>
          <Button aria-label="Search in chat" size="icon-sm" variant="ghost" className="text-whatsapp-foreground hover:bg-white/20" onClick={() => setShowSearch(true)}>
            <Search className="size-4" />
          </Button>
          <div ref={menuRef} className="relative">
            <Button
              aria-label="More actions"
              size="icon-sm"
              variant="ghost"
              className="text-whatsapp-foreground hover:bg-white/20"
              onClick={() => setMenuOpen(!menuOpen)}
            >
              <MoreVertical className="size-4" />
            </Button>
            {menuOpen && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                <div className="absolute right-0 top-full z-20 mt-1 min-w-44 rounded-lg border border-whatsapp-border bg-popover p-1 shadow-lg">
                  <button
                    type="button"
                    className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-xs text-red-600 hover:bg-whatsapp-muted"
                    onClick={deleteAllMessages}
                  >
                    <Trash2 className="size-3.5" />
                    Delete all messages
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </header>

      <MessageThread messages={messages} channelId={selectedRoomId} loading={rooms.length === 0} />
      {typingNames.length > 0 && (
        <div className="flex items-center gap-2 px-4 py-1.5 text-xs text-muted-foreground">
          <span className="flex gap-0.5">
            <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:0ms]" />
            <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:150ms]" />
            <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:300ms]" />
          </span>
          <span>{typingNames.join(", ")} typing{typingNames.length === 1 ? "s" : ""}...</span>
        </div>
      )}
      <ChatComposer roomName={room.name} />
    </section>
  );
}

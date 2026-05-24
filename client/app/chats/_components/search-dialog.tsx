"use client";

import { useMemo, useState } from "react";
import { Hash, Loader2, Search, X } from "lucide-react";

import { useAppSelector } from "@/store/hooks";
import { Input } from "@/components/ui/input";
import type { Room } from "@/types/chats";

export function SearchDialog({
  open,
  onOpenChange,
  onSelectChannel,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelectChannel: (channelId: string) => void;
}) {
  const [query, setQuery] = useState("");
  const rooms = useAppSelector((s) => s.chats.rooms);
  const messagesByRoom = useAppSelector((s) => s.chats.messagesByRoom);

  const results = useMemo<{ channels: Room[]; messages: { channelId: string; channelName: string; content: string; time: string }[] }>(() => {
    if (!query.trim()) return { channels: [], messages: [] };
    const q = query.toLowerCase();

    const channelMatches = rooms.filter(
      (r) => r.name.toLowerCase().includes(q) || r.description.toLowerCase().includes(q),
    );

    const messageMatches: { channelId: string; channelName: string; content: string; time: string }[] = [];
    for (const room of rooms) {
      const msgs = messagesByRoom[room.id] ?? [];
      for (const msg of msgs) {
        if (msg.content.toLowerCase().includes(q)) {
          messageMatches.push({
            channelId: room.id,
            channelName: room.name,
            content: msg.content.slice(0, 200),
            time: msg.time,
          });
        }
      }
    }

    return { channels: channelMatches, messages: messageMatches };
  }, [query, rooms, messagesByRoom]);

  function handleSelect(id: string) {
    onSelectChannel(id);
    onOpenChange(false);
    setQuery("");
  }

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/20" onClick={() => onOpenChange(false)} />
      <div className="fixed inset-x-0 top-0 z-50 mx-auto mt-16 w-full max-w-lg">
        <div className="rounded-xl border border-whatsapp-border bg-card shadow-2xl">
          <div className="relative flex items-center gap-2 border-b border-whatsapp-border px-4 py-3">
            <Search className="size-4 shrink-0 text-muted-foreground" />
            <Input
              className="h-8 border-0 bg-transparent p-0 text-sm focus-visible:ring-0"
              placeholder="Search channels and messages..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              autoFocus
            />
            <button
              type="button"
              className="flex size-6 items-center justify-center rounded-md text-muted-foreground hover:bg-whatsapp-muted transition-colors"
              onClick={() => onOpenChange(false)}
            >
              <X className="size-4" />
            </button>
          </div>

          <div className="max-h-96 overflow-y-auto p-2">
            {!query.trim() && (
              <p className="p-3 text-center text-xs text-muted-foreground">Type to search channels and messages</p>
            )}

            {query.trim() && results.channels.length === 0 && results.messages.length === 0 && (
              <p className="p-3 text-center text-xs text-muted-foreground">No results for &quot;{query}&quot;</p>
            )}

            {results.channels.length > 0 && (
              <div className="mb-2">
                <p className="px-2 py-1 text-xs font-semibold text-muted-foreground uppercase">Channels</p>
                {results.channels.map((ch) => (
                  <button
                    key={ch.id}
                    type="button"
                    className="flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-sm hover:bg-whatsapp-muted transition-colors"
                    onClick={() => handleSelect(ch.id)}
                  >
                    <Hash className="size-3.5 shrink-0 text-muted-foreground" />
                    <span className="truncate font-medium">{ch.name}</span>
                    <span className="truncate text-xs text-muted-foreground">{ch.description}</span>
                  </button>
                ))}
              </div>
            )}

            {results.messages.length > 0 && (
              <div>
                <p className="px-2 py-1 text-xs font-semibold text-muted-foreground uppercase">Messages</p>
                {results.messages.slice(0, 20).map((msg, i) => (
                  <button
                    key={i}
                    type="button"
                    className="flex w-full flex-col gap-0.5 rounded-lg px-2 py-2 text-left text-sm hover:bg-whatsapp-muted transition-colors"
                    onClick={() => handleSelect(msg.channelId)}
                  >
                    <span className="flex items-center gap-2">
                      <Hash className="size-3 shrink-0 text-muted-foreground" />
                      <span className="truncate text-xs font-medium text-whatsapp-deep">{msg.channelName}</span>
                      <span className="shrink-0 text-xs text-muted-foreground">{msg.time}</span>
                    </span>
                    <p className="line-clamp-2 text-xs text-muted-foreground">{msg.content}</p>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

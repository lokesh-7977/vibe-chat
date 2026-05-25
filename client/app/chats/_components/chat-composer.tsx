"use client";

import { useRef, useState, useEffect } from "react";
import { Paperclip, SendHorizontal, SmilePlus, Sparkles, Bot } from "lucide-react";

import { listChannelMembers } from "@/apis/channels";
import { presignUpload, completeUpload } from "@/apis/uploads";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/providers/toast-provider";
import { realtimeClient } from "@/services/realtime";
import axiosInstance from "@/services/axios";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { sendChatMessage, sendPrivateAiMessage } from "@/store/slices/chats-slice";
import type { ChannelMemberResponse } from "@/types";

const EMOJIS = [
  "😀", "😂", "🤣", "❤️", "😍", "🤩", "😎", "🙌",
  "🔥", "💯", "✨", "🎉", "👍", "👏", "🙏", "💪",
  "😢", "😤", "🤔", "😴", "🥺", "😅", "😊", "🤗",
  "🎶", "💀", "☀️", "🌙", "⭐", "🌈", "🍕", "🚀",
];

type UploadState = {
  uploading: boolean;
  fileName: string;
};

export function ChatComposer({ roomName }: { roomName: string }) {
  const dispatch = useAppDispatch();
  const { toast } = useToast();
  const selectedRoomId = useAppSelector((state) => state.chats.selectedRoomId);
  const currentWorkspaceId = useAppSelector((state) => state.chats.currentWorkspaceId);
  const usersById = useAppSelector((state) => state.chats.usersById);
  const [message, setMessage] = useState("");
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [showMentionMenu, setShowMentionMenu] = useState(false);
  const [mentionStart, setMentionStart] = useState<number | null>(null);
  const [mentionQuery, setMentionQuery] = useState("");
  const [uploadState, setUploadState] = useState<UploadState | null>(null);
  const [channelMembers, setChannelMembers] = useState<ChannelMemberResponse[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);
  const docInputRef = useRef<HTMLInputElement>(null);
  const emojiRef = useRef<HTMLDivElement>(null);
  const mentionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (emojiRef.current && !emojiRef.current.contains(e.target as Node)) {
        setShowEmojiPicker(false);
      }
      if (mentionRef.current && !mentionRef.current.contains(e.target as Node)) {
        setShowMentionMenu(false);
        setMentionStart(null);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  useEffect(() => {
    if (!selectedRoomId) return;
    listChannelMembers(selectedRoomId)
      .then((res) => setChannelMembers(res.data ?? []))
      .catch(() => {});
  }, [selectedRoomId]);

  function submitMessage() {
    const trimmed = message.trim();
    if (!trimmed) return;

    if (trimmed.toLowerCase().startsWith("@aura-chat")) {
      dispatch(sendPrivateAiMessage({ channelId: selectedRoomId, content: trimmed }));
    } else {
      dispatch(sendChatMessage({ channelId: selectedRoomId, content: trimmed }));
    }
    realtimeClient.typingStopped(selectedRoomId);
    setMessage("");
    setShowMentionMenu(false);
    setMentionStart(null);
  }

  async function submitAiQuery() {
    const trimmed = message.trim();
    if (!trimmed) return;

    try {
      const res = await axiosInstance.post("/ai/grammar-check", { text: trimmed });
      const data = res.data;
      if (data.language === "other") {
        toast({ title: data.message ?? "Only English is supported.", kind: "error" });
      } else if (data.hasErrors && data.correctedText) {
        setMessage(data.correctedText);
      }
    } catch {
      toast({ title: "Grammar check failed", kind: "error" });
    }
  }

  async function uploadAndSend(file: File, kind: "file" | "image" | "audio") {
    if (!currentWorkspaceId) {
      toast({ title: "No workspace selected", kind: "error" });
      return;
    }
    setUploadState({ uploading: true, fileName: file.name });
    try {
      const presign = await presignUpload({
        workspaceId: currentWorkspaceId,
        channelId: selectedRoomId,
        fileName: file.name,
        mimeType: file.type,
        fileSize: file.size,
      });
      if (!presign.data) throw new Error("No presign data");

      await fetch(presign.data.uploadUrl, {
        method: "PUT",
        body: file,
        headers: { "Content-Type": file.type },
      });

      await completeUpload(presign.data.documentId);
      const objectKey = encodeURIComponent(presign.data.objectKey).replace(/%2F/g, "/");

      let content = "";
      if (kind === "image") {
        content = `![${file.name}](r2://${objectKey})`;
      } else if (kind === "audio") {
        content = `🎵 Audio uploaded: r2://${objectKey}`;
      } else {
        content = `📎 ${file.name}\nr2://${objectKey}`;
      }

      dispatch(sendChatMessage({ channelId: selectedRoomId, content }));
      toast({ title: `${kind === "image" ? "Image" : kind === "audio" ? "Audio" : "File"} uploaded`, kind: "success" });
    } catch (err) {
      toast({ title: "Upload failed", description: (err as Error)?.message ?? "Unknown error", kind: "error" });
    } finally {
      setUploadState(null);
    }
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const isImage = file.type.startsWith("image/");
    uploadAndSend(file, isImage ? "image" : "file");
    e.target.value = "";
  }

  function handleImageSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    uploadAndSend(file, "image");
    e.target.value = "";
  }

  function handleVideoSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    uploadAndSend(file, "file");
    e.target.value = "";
  }

  function handleDocSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    uploadAndSend(file, "file");
    e.target.value = "";
  }

  const emojiPicker = showEmojiPicker && (
    <div
      ref={emojiRef}
      className="absolute bottom-full left-0 z-20 mb-2 grid w-72 grid-cols-8 gap-1 rounded-lg border border-whatsapp-border bg-popover p-2 shadow-lg"
    >
      {EMOJIS.map((emoji) => (
        <button
          key={emoji}
          type="button"
          className="flex size-8 items-center justify-center rounded-md text-lg transition-colors hover:bg-whatsapp-muted"
          onClick={() => {
            setMessage((prev) => prev + emoji);
            setShowEmojiPicker(false);
          }}
        >
          {emoji}
        </button>
      ))}
    </div>
  );

  return (
    <footer className="border-t border-whatsapp-border bg-card p-3">
      <input
        ref={fileInputRef}
        type="file"
        className="hidden"
        onChange={handleFileSelect}
      />
      <input
        ref={imageInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleImageSelect}
      />
      <input
        ref={videoInputRef}
        type="file"
        accept="video/*"
        className="hidden"
        onChange={handleVideoSelect}
      />
      <input
        ref={docInputRef}
        type="file"
        accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        className="hidden"
        onChange={handleDocSelect}
      />
      <form
        className="flex items-center gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          submitMessage();
        }}
      >
        <div className="relative">
          <Button
            aria-label="Add reaction"
            size="icon-lg"
            type="button"
            variant="ghost"
            onClick={() => setShowEmojiPicker(!showEmojiPicker)}
          >
            <SmilePlus className="size-5" />
          </Button>
          {emojiPicker}
        </div>
        <div className="relative">
          <Button
            aria-label="Attach"
            size="icon-lg"
            type="button"
            variant="ghost"
            disabled={!!uploadState}
            onClick={() => {
              setShowEmojiPicker(false);
              setShowAttachMenu((v) => !v);
            }}
          >
            <Paperclip className="size-5" />
          </Button>
          {showAttachMenu && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowAttachMenu(false)} />
              <div className="absolute bottom-full left-0 z-20 mb-2 flex w-44 flex-col gap-1 rounded-lg border border-whatsapp-border bg-popover p-1 shadow-lg">
                <button
                  type="button"
                  className="flex items-center gap-2 rounded-md px-3 py-2 text-left text-xs hover:bg-whatsapp-muted"
                  onClick={() => {
                    setShowAttachMenu(false);
                    imageInputRef.current?.click();
                  }}
                >
                  <span className="inline-flex size-6 items-center justify-center rounded-md bg-whatsapp-muted">🖼️</span>
                  Photo
                </button>
                <button
                  type="button"
                  className="flex items-center gap-2 rounded-md px-3 py-2 text-left text-xs hover:bg-whatsapp-muted"
                  onClick={() => {
                    setShowAttachMenu(false);
                    videoInputRef.current?.click();
                  }}
                >
                  <span className="inline-flex size-6 items-center justify-center rounded-md bg-whatsapp-muted">🎥</span>
                  Video
                </button>
                <button
                  type="button"
                  className="flex items-center gap-2 rounded-md px-3 py-2 text-left text-xs hover:bg-whatsapp-muted"
                  onClick={() => {
                    setShowAttachMenu(false);
                    docInputRef.current?.click();
                  }}
                >
                  <span className="inline-flex size-6 items-center justify-center rounded-md bg-whatsapp-muted">📄</span>
                  Document
                </button>
              </div>
            </>
          )}
        </div>
        <div className="relative flex-1" ref={mentionRef}>
          <Input
            className="h-11 w-full border-whatsapp-border bg-whatsapp-surface"
            placeholder={uploadState ? `Uploading ${uploadState.fileName}...` : `Message ${roomName}`}
            value={message}
            disabled={!!uploadState}
            onBlur={() => realtimeClient.typingStopped(selectedRoomId)}
            onChange={(event) => {
              const next = event.target.value;
              setMessage(next);
              realtimeClient.typingStarted(selectedRoomId);

              // Basic mention suggestion: if the user is typing a token that starts with "@", suggest channel members and @aura-chat.
              const caret = event.target.selectionStart ?? next.length;
              const upto = next.slice(0, caret);
              const match = upto.match(/(^|\s)(@[^\s@]*)$/);
              const token = match?.[2] ?? null;
              if (token && token.toLowerCase().startsWith("@")) {
                const start = caret - token.length;
                setMentionStart(start);
                const q = token.slice(1).toLowerCase();
                setMentionQuery(q);
                setShowMentionMenu(true);
              } else {
                setShowMentionMenu(false);
                setMentionStart(null);
                setMentionQuery("");
              }
            }}
          />
          {showMentionMenu && (
            <div className="absolute bottom-full left-0 z-30 mb-2">
              <div className="w-64 rounded-lg border border-whatsapp-border bg-popover p-1 shadow-lg max-h-48 overflow-y-auto">
                {(!mentionQuery || "aura-chat".startsWith(mentionQuery)) && (
                  <button
                    type="button"
                    className="flex w-full items-center justify-between gap-2 rounded-md px-3 py-2 text-left text-xs hover:bg-whatsapp-muted"
                    onClick={() => {
                      const start = mentionStart ?? 0;
                      const before = message.slice(0, start);
                      const after = message.slice(start).replace(/^@[^\s@]*/, "");
                      const next = `${before}@aura-chat ${after}`;
                      setMessage(next);
                      setShowMentionMenu(false);
                      setMentionStart(null);
                    }}
                  >
                    <span className="flex items-center gap-2">
                      <Bot className="size-4 text-whatsapp-deep" />
                      <span className="font-semibold text-foreground">@aura-chat</span>
                    </span>
                    <span className="text-[10px] text-muted-foreground">Private AI</span>
                  </button>
                )}
                {channelMembers
                  .filter((m) => {
                    const user = usersById[m.userId];
                    if (!user) return false;
                    return !mentionQuery || user.username.toLowerCase().startsWith(mentionQuery) || user.fullName.toLowerCase().startsWith(mentionQuery);
                  })
                  .slice(0, 10)
                  .map((m) => {
                    const user = usersById[m.userId];
                    if (!user) return null;
                    return (
                      <button
                        key={m.userId}
                        type="button"
                        className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-xs hover:bg-whatsapp-muted"
                        onClick={() => {
                          const start = mentionStart ?? 0;
                          const before = message.slice(0, start);
                          const after = message.slice(start).replace(/^@[^\s@]*/, "");
                          const next = `${before}@${user.username} ${after}`;
                          setMessage(next);
                          setShowMentionMenu(false);
                          setMentionStart(null);
                        }}
                      >
                        <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-whatsapp-muted text-[10px] font-medium">
                          {user.fullName.charAt(0).toUpperCase()}
                        </span>
                        <span className="font-medium">@{user.username}</span>
                        <span className="text-muted-foreground truncate">{user.fullName}</span>
                      </button>
                    );
                  })}
                {channelMembers.filter((m) => {
                  const user = usersById[m.userId];
                  if (!user) return false;
                  return !mentionQuery || user.username.toLowerCase().startsWith(mentionQuery) || user.fullName.toLowerCase().startsWith(mentionQuery);
                }).length === 0 && mentionQuery && !"aura-chat".startsWith(mentionQuery) && (
                  <p className="px-3 py-2 text-xs text-muted-foreground">No users found</p>
                )}
              </div>
            </div>
          )}
        </div>
        <Button
          aria-label="Ask AI"
          className="text-whatsapp-deep hover:text-whatsapp-deep/80"
          size="icon-lg"
          type="button"
          variant="ghost"
          onClick={submitAiQuery}
          disabled={!!uploadState}
        >
          <Sparkles className="size-5" />
        </Button>
        <Button
          aria-label="Send"
          className="bg-whatsapp text-whatsapp-foreground hover:bg-whatsapp/90"
          size="icon-lg"
          type="submit"
          disabled={!!uploadState}
        >
          <SendHorizontal className="size-5" />
        </Button>
      </form>
    </footer>
  );
}

/* eslint-disable @next/next/no-img-element */
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { CheckCheck, Languages, FileText, Video, Hash } from "lucide-react";
import type { Message } from "@/types/chats";
import { TranslateDialog } from "./translate-dialog";
import { SummarizeDialog } from "./summarize-dialog";
import { ImageSummarizeDialog } from "./image-summarize-dialog";
import { FilePreviewDialog } from "./file-preview-dialog";
import { DocumentSummarizeDialog } from "./document-summarize-dialog";
import { DocumentQaDialog } from "./document-qa-dialog";
import { useAppSelector } from "@/store/hooks";
import { getImageUrl } from "@/apis/uploads";

const LANGUAGES = [
  { label: "Telugu", code: "Telugu" },
  { label: "English", code: "English" },
  { label: "Hindi", code: "Hindi" },
];

const urlPattern = /(https?:\/\/[^\s]+)/;
const urlExtractPattern = /(https?:\/\/[^\s]+)/g;
const ytPattern = /(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)/;
const markdownImagePattern = /!\[([^\]]*)\]\(([^)\s]+)\)/g;
const r2KeyPattern = /(r2:\/\/[^\n]+)/g;
const attachmentLabelLinePattern = /^[ \t]*(?:\u{1F4CE}|\u{1F3B5})\s[^\n]*$/gmu;

function extractUrls(text: string): string[] {
  return Array.from(text.matchAll(urlExtractPattern))
    .map((m) => m[1])
    .filter(Boolean);
}

function isOnlyLinks(text: string): boolean {
  const stripped = text.replace(urlExtractPattern, "").trim();
  return stripped.length === 0;
}

function isYouTubeUrl(url: string): boolean {
  return ytPattern.test(url);
}

function normalizeDisplayUrl(url: string): string {
  try {
    const trimmed = url.trim();
    const parsed = new URL(trimmed);

    // Only strip SigV4 params for URLs that are likely presigned PUT URLs.
    // A presigned GET URL is safe to render as-is and typically has SignedHeaders=host.
    const signedHeaders = parsed.searchParams.get("X-Amz-SignedHeaders") ?? "";
    const isLikelyPresignedPut = signedHeaders.includes("content-type");

    if (isLikelyPresignedPut) {
      parsed.search = "";
      return parsed.toString().trim();
    }
    return trimmed;
  } catch {
    const trimmed = url.trim();
    // Fallback: strip SigV4 query string only for likely PUT presigns.
    const idx = trimmed.indexOf("?X-Amz-");
    if (idx !== -1) {
      const qs = trimmed.slice(idx);
      if (
        qs.includes("X-Amz-SignedHeaders=content-type%3Bhost") ||
        qs.includes("X-Amz-SignedHeaders=content-type;host")
      ) {
        return trimmed.slice(0, idx);
      }
    }
    return trimmed;
  }
}

function tryExtractObjectKeyFromR2Url(url: string): string | null {
  try {
    const parsed = new URL(url.trim());
    if (!parsed.hostname.endsWith(".r2.cloudflarestorage.com")) return null;
    const parts = parsed.pathname.split("/").filter(Boolean);
    // Path is typically: /<bucket>/<object_key...>
    if (parts.length < 2) return null;
    const objectKey = parts.slice(1).join("/");
    return objectKey || null;
  } catch {
    return null;
  }
}

function normalizeR2ObjectKey(raw: string): string {
  // Chat text may include keys inside markdown-like wrappers or with trailing punctuation.
  let current = raw.trim().replace(/[)\],.>"']+$/g, "");
  // Some older messages may have keys that are already URL-encoded (or even double-encoded).
  // Decode a couple of times (bounded) so `%2520` -> `%20` -> space.
  for (let i = 0; i < 2; i++) {
    if (!current.includes("%")) break;
    try {
      const next = decodeURIComponent(current);
      if (next === current) break;
      current = next;
    } catch {
      break;
    }
  }
  return current;
}

function TranslateButton({
  channelId,
  message,
}: {
  channelId: string;
  message: Message;
}) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedLang, setSelectedLang] = useState("");
  return (
    <>
      <div className="relative">
        <button
          type="button"
          className="flex items-center gap-0.5 rounded px-1 py-0.5 transition-colors hover:bg-whatsapp-surface hover:text-foreground"
          onClick={() => setPickerOpen(!pickerOpen)}
          title="Translate"
        >
          <Languages className="size-3" />
          <span>Translate</span>
        </button>
        {pickerOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setPickerOpen(false)}
            />
            <div className="absolute bottom-full left-0 z-20 mb-1 max-h-48 w-36 overflow-y-auto rounded-lg border border-whatsapp-border bg-popover p-1 shadow-lg">
              {LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  type="button"
                  className="flex w-full items-center rounded-md px-2.5 py-1.5 text-left text-xs transition-colors hover:bg-whatsapp-muted"
                  onClick={() => {
                    setPickerOpen(false);
                    setSelectedLang(lang.code);
                    setDialogOpen(true);
                  }}
                >
                  {lang.label}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
      {dialogOpen && (
        <TranslateDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          channelId={channelId}
          message={message}
          language={selectedLang}
        />
      )}
    </>
  );
}

function SummarizeButton({
  channelId,
  url,
  isVideo,
}: {
  channelId: string;
  url: string;
  isVideo: boolean;
}) {
  const [dialogOpen, setDialogOpen] = useState(false);
  return (
    <>
      <button
        type="button"
        className="flex items-center gap-0.5 rounded px-1 py-0.5 transition-colors hover:bg-whatsapp-surface hover:text-foreground"
        onClick={() => setDialogOpen(true)}
        title={isVideo ? "Summarize video" : "Summarize link"}
      >
        {isVideo ? (
          <Video className="size-3" />
        ) : (
          <FileText className="size-3" />
        )}
        <span>{isVideo ? "Summarize video" : "Summarize"}</span>
      </button>
      {dialogOpen && (
        <SummarizeDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          channelId={channelId}
          url={url}
        />
      )}
    </>
  );
}

type SignedMeta = { url: string; mimeType: string; fileName: string };

function MessageText({
  text,
  signedMetaByKey,
  onRefreshKey,
}: {
  text: string;
  signedMetaByKey: Record<string, SignedMeta>;
  onRefreshKey: (key: string) => void;
}) {
  const [imgDialogKey, setImgDialogKey] = useState<string | null>(null);
  const [docDialog, setDocDialog] = useState<{
    key: string;
    title: string;
  } | null>(null);
  const [qaDialog, setQaDialog] = useState<{
    key: string;
    title: string;
  } | null>(null);
  const [preview, setPreview] = useState<{
    title: string;
    url: string;
    kind: "pdf" | "video";
  } | null>(null);
  const images = Array.from(text.matchAll(markdownImagePattern))
    .map((m) => ({ alt: m[1] ?? "", url: m[2] ?? "" }))
    .filter((i) => Boolean(i.url));

  const r2Keys = Array.from(text.matchAll(r2KeyPattern))
    .map((m) => (m[1] ?? "").trim())
    .filter((v) => v.startsWith("r2://"))
    .map((v) => normalizeR2ObjectKey(v.slice("r2://".length)));

  const imageKeys = new Set<string>();
  for (const img of images) {
    const key = img.url.startsWith("r2://")
      ? normalizeR2ObjectKey(img.url.slice("r2://".length))
      : null;
    if (key) imageKeys.add(key);
  }
  const r2KeysToRender = r2Keys.filter((key) => !imageKeys.has(key));

  const stripped = text
    .replace(markdownImagePattern, "")
    .replace(r2KeyPattern, "")
    .replace(attachmentLabelLinePattern, "")
    .trim();
  const parts = stripped.split(urlPattern);

  return (
    <div className="space-y-2">
      {imgDialogKey && (
        <ImageSummarizeDialog
          open={Boolean(imgDialogKey)}
          onOpenChange={(o) => setImgDialogKey(o ? imgDialogKey : null)}
          objectKey={imgDialogKey}
        />
      )}
      {docDialog && (
        <DocumentSummarizeDialog
          open={Boolean(docDialog)}
          onOpenChange={(o) => setDocDialog(o ? docDialog : null)}
          objectKey={docDialog.key}
          title={docDialog.title}
        />
      )}
      {qaDialog && (
        <DocumentQaDialog
          open={Boolean(qaDialog)}
          onOpenChange={(o) => setQaDialog(o ? qaDialog : null)}
          objectKey={qaDialog.key}
          title={qaDialog.title}
        />
      )}
      {preview && (
        <FilePreviewDialog
          open={Boolean(preview)}
          onOpenChange={(o) => setPreview(o ? preview : null)}
          title={preview.title}
          url={preview.url}
          kind={preview.kind}
        />
      )}
      {images.length > 0 && (
        <div className="space-y-2">
          {images.map((img) =>
            (() => {
              const objectKey = img.url.startsWith("r2://")
                ? img.url.slice("r2://".length)
                : tryExtractObjectKeyFromR2Url(img.url);
              const normalizedObjectKey = objectKey
                ? normalizeR2ObjectKey(objectKey)
                : null;
              const meta = normalizedObjectKey
                ? signedMetaByKey[normalizedObjectKey]
                : undefined;
              const resolvedUrl = meta?.url ?? img.url;
              const displayUrl = normalizeDisplayUrl(resolvedUrl);
              const mimeType = meta?.mimeType ?? "";
              const title = meta?.fileName ?? img.alt ?? "Attachment";
              return (
                <a
                  key={img.url}
                  href={displayUrl}
                  rel="noreferrer"
                  target="_blank"
                  className="block"
                  title="Open image"
                >
                  {mimeType.startsWith("video/") ? (
                    <video
                      src={displayUrl}
                      controls
                      className="max-h-80 w-auto max-w-full rounded-md border border-whatsapp-border/50 bg-black object-contain"
                      onError={() => {
                        if (normalizedObjectKey)
                          onRefreshKey(normalizedObjectKey);
                      }}
                    />
                  ) : mimeType.startsWith("audio/") ? (
                    <audio
                      src={displayUrl}
                      controls
                      className="w-full"
                      onError={() => {
                        if (normalizedObjectKey)
                          onRefreshKey(normalizedObjectKey);
                      }}
                    />
                  ) : mimeType === "application/pdf" ? (
                    <div className="rounded-md border border-whatsapp-border/50 bg-whatsapp-surface p-3">
                      <div className="flex items-center justify-between gap-3">
                        <div className="min-w-0">
                          <div className="truncate text-sm font-medium">
                            {title}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            PDF document
                          </div>
                        </div>
                        <button
                          type="button"
                          className="shrink-0 rounded-md border border-whatsapp-border bg-card px-3 py-1.5 text-xs font-semibold hover:bg-whatsapp-muted"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            setPreview({ title, url: displayUrl, kind: "pdf" });
                          }}
                        >
                          Open
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-1">
                      <img
                        src={displayUrl}
                        alt={img.alt || meta?.fileName || "Image"}
                        className="max-h-80 w-auto max-w-full rounded-none object-contain"
                        loading="lazy"
                        onError={() => {
                          if (normalizedObjectKey)
                            onRefreshKey(normalizedObjectKey);
                        }}
                      />
                      {normalizedObjectKey && (
                        <div className="flex justify-end">
                          <button
                            type="button"
                            className="rounded px-2 py-1 text-xs text-muted-foreground hover:bg-whatsapp-muted hover:text-foreground"
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              setImgDialogKey(normalizedObjectKey);
                            }}
                          >
                            Summarize image
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </a>
              );
            })(),
          )}
        </div>
      )}

      {r2KeysToRender.length > 0 && (
        <div className="space-y-2">
          {r2KeysToRender.map((key) => {
            const meta = signedMetaByKey[key];
            const mimeType = meta?.mimeType ?? "";
            const title =
              meta?.fileName ?? key.split("/").pop() ?? "Attachment";
            const displayUrl = normalizeDisplayUrl(meta?.url ?? `r2://${key}`);

            const open = (kind: "pdf" | "video") =>
              setPreview({ title, url: displayUrl, kind });

            if (mimeType.startsWith("image/")) {
              return (
                <a
                  key={key}
                  href={displayUrl}
                  rel="noreferrer"
                  target="_blank"
                  className="block"
                  title="Open image"
                >
                  <div className="space-y-1">
                    <img
                      src={displayUrl}
                      alt={title}
                      className="max-h-80 w-auto max-w-full rounded-none object-contain"
                      loading="lazy"
                      onError={() => onRefreshKey(key)}
                    />
                    <div className="flex justify-end">
                      <button
                        type="button"
                        className="rounded px-2 py-1 text-xs text-muted-foreground hover:bg-whatsapp-muted hover:text-foreground"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          setImgDialogKey(key);
                        }}
                      >
                        Summarize image
                      </button>
                    </div>
                  </div>
                </a>
              );
            }

            return (
              <div
                key={key}
                className="rounded-md border border-whatsapp-border/50 bg-whatsapp-surface p-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium">{title}</div>
                    <div className="text-xs text-muted-foreground">
                      {mimeType || "file"}
                    </div>
                  </div>
                  <div className="flex shrink-0 gap-2">
                    {mimeType === "application/pdf" ? (
                      <button
                        type="button"
                        className="rounded-md border border-whatsapp-border bg-card px-3 py-1.5 text-xs font-semibold hover:bg-whatsapp-muted"
                        onClick={() => open("pdf")}
                      >
                        Open
                      </button>
                    ) : mimeType.startsWith("video/") ? (
                      <button
                        type="button"
                        className="rounded-md border border-whatsapp-border bg-card px-3 py-1.5 text-xs font-semibold hover:bg-whatsapp-muted"
                        onClick={() => open("video")}
                      >
                        Open
                      </button>
                    ) : (
                      <a
                        className="rounded-md border border-whatsapp-border bg-card px-3 py-1.5 text-xs font-semibold hover:bg-whatsapp-muted"
                        href={displayUrl}
                        rel="noreferrer"
                        target="_blank"
                        onClick={(e) => {
                          if (!meta?.url) {
                            e.preventDefault();
                            onRefreshKey(key);
                          }
                        }}
                      >
                        Download
                      </a>
                    )}

                    {(mimeType === "application/pdf" ||
                      mimeType ===
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document") && (
                      <button
                        type="button"
                        className="rounded-md border border-whatsapp-border bg-card px-3 py-1.5 text-xs font-semibold hover:bg-whatsapp-muted"
                        onClick={() => setDocDialog({ key, title })}
                      >
                        Summarize
                      </button>
                    )}
                    {(mimeType === "application/pdf" ||
                      mimeType ===
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document") && (
                      <button
                        type="button"
                        className="rounded-md border border-whatsapp-border bg-card px-3 py-1.5 text-xs font-semibold hover:bg-whatsapp-muted"
                        onClick={() => setQaDialog({ key, title })}
                      >
                        Q&A
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {stripped.length > 0 && (
        <p className="whitespace-pre-wrap wrap-break text-sm leading-6">
          {parts.map((part) =>
            urlPattern.test(part) ? (
              <a
                key={part}
                className="font-medium text-whatsapp-deep underline underline-offset-4"
                href={normalizeDisplayUrl(part)}
                rel="noreferrer"
                target="_blank"
              >
                {normalizeDisplayUrl(part)}
              </a>
            ) : (
              part
            ),
          )}
        </p>
      )}
    </div>
  );
}

export function MessageThread({
  messages,
  channelId,
  loading,
}: {
  messages: Message[];
  channelId: string;
  loading?: boolean;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const currentUserId = useAppSelector((s) => s.auth.user?.id);
  const [signedMetaByKey, setSignedMetaByKey] = useState<
    Record<string, SignedMeta>
  >({});

  const docIdsInThread = useMemo(() => {
    const ids = new Set<string>();
    for (const m of messages) {
      for (const match of m.content?.matchAll(r2KeyPattern) ?? []) {
        const raw = (match[1] ?? "").trim();
        if (raw.startsWith("r2://"))
          ids.add(normalizeR2ObjectKey(raw.slice("r2://".length)));
      }
      for (const match of m.content?.matchAll(markdownImagePattern) ?? []) {
        const raw = match[2] ?? "";
        if (raw.startsWith("r2://")) {
          ids.add(normalizeR2ObjectKey(raw.slice("r2://".length)));
        } else {
          const extracted = tryExtractObjectKeyFromR2Url(raw);
          if (extracted) ids.add(extracted);
        }
      }
    }
    return Array.from(ids);
  }, [messages]);

  useEffect(() => {
    let cancelled = false;
    async function loadMissing() {
      const missing = docIdsInThread.filter((id) => !signedMetaByKey[id]);
      if (!missing.length) return;
      const next: Record<string, SignedMeta> = {};
      await Promise.all(
        missing.map(async (id) => {
          try {
            const res = await getImageUrl(id);
            const data = res.data;
            if (data?.url)
              next[id] = {
                url: data.url,
                mimeType: data.mimeType,
                fileName: data.fileName,
              };
          } catch {
            // ignore (will fall back to showing doc:// link text)
          }
        }),
      );
      if (!cancelled && Object.keys(next).length) {
        setSignedMetaByKey((prev) => ({ ...prev, ...next }));
      }
    }
    loadMissing();
    return () => {
      cancelled = true;
    };
  }, [docIdsInThread, signedMetaByKey]);

  const refreshKey = async (key: string) => {
    try {
      const res = await getImageUrl(key);
      const data = res.data;
      if (data?.url) {
        setSignedMetaByKey((prev) => ({
          ...prev,
          [key]: {
            url: data.url,
            mimeType: data.mimeType,
            fileName: data.fileName,
          },
        }));
      }
    } catch {
      // ignore
    }
  };

  const chatMessages = useMemo(
    () => messages.filter((m) => !m.isAi || m.isPrivate),
    [messages],
  );

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto bg-whatsapp-surface px-3 py-3 sm:px-4 sm:py-4">
      <div className="mx-auto rounded-full bg-card px-3 py-1 text-xs text-muted-foreground shadow-sm">
        Today
      </div>
      {loading ? (
        <div className="space-y-4 px-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className={`flex animate-pulse gap-3 ${i % 2 === 0 ? "justify-end" : "justify-start"}`}
            >
              <div className={`space-y-2 ${i % 2 === 0 ? "order-1" : ""}`}>
                <div
                  className={`flex gap-3 ${i % 2 === 0 ? "flex-row-reverse" : ""}`}
                >
                  <div className="size-8 rounded-full bg-whatsapp-muted" />
                  <div
                    className={`space-y-2 rounded-lg p-3 ${i % 2 === 0 ? "bg-whatsapp-bubble/50" : "bg-whatsapp-muted/50"}`}
                  >
                    <div className="h-2 w-24 rounded bg-whatsapp-muted" />
                    <div className="h-2 w-48 rounded bg-whatsapp-muted" />
                    <div className="h-2 w-32 rounded bg-whatsapp-muted" />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : chatMessages.length === 0 ? (
        <div className="flex flex-1 items-center justify-center">
          <div className="flex flex-col items-center gap-2 text-center">
            <div className="flex size-12 items-center justify-center rounded-2xl bg-whatsapp-muted">
              <Hash className="size-5 text-muted-foreground" />
            </div>
            <p className="text-sm font-medium">No messages yet</p>
            <p className="text-xs text-muted-foreground">
              Start the conversation.
            </p>
          </div>
        </div>
      ) : (
        chatMessages.map((message) => {
          const isMe = Boolean(
            (currentUserId &&
              message.userId &&
              currentUserId === message.userId) ||
            (!message.userId && message.role === "me"),
          );
          const urls = extractUrls(message.content || "");
          const firstUrl = urls[0] ?? null;
          const firstUrlIsVideo = firstUrl ? isYouTubeUrl(firstUrl) : false;
          const messageIsOnlyLinks = isOnlyLinks(message.content || "");
          const hasInlineAttachments = markdownImagePattern.test(
            message.content || "",
          );
          // eslint-disable-next-line react-hooks/immutability
          markdownImagePattern.lastIndex = 0;
          const showTranslate =
            !messageIsOnlyLinks && !firstUrlIsVideo && !hasInlineAttachments;
          const showSummarize = Boolean(firstUrl);

          return (
            <div
              key={message.id}
              className={`group flex ${isMe ? "justify-end" : "justify-start"}`}
            >
              <div
                className={
                  isMe
                    ? "max-w-xl rounded-lg rounded-br-sm bg-whatsapp-bubble px-3 py-2 shadow-sm"
                    : "max-w-xl rounded-lg rounded-bl-sm border border-whatsapp-border/50 bg-card px-3 py-2 shadow-sm"
                }
              >
                <p className="mb-1 text-xs font-semibold text-whatsapp-deep">
                  {message.author}
                </p>
                {message.isPrivate &&
                  message.isAi &&
                  message.isStreaming &&
                  !(message.content || "").trim() && (
                    <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
                      <span className="flex gap-0.5">
                        <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:0ms]" />
                        <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:150ms]" />
                        <span className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:300ms]" />
                      </span>
                      <span>Aura Chat is typing...</span>
                    </div>
                  )}
                {message.replyTo && (
                  <div className="mb-2 rounded-md border-l-4 border-whatsapp bg-whatsapp-surface px-3 py-2">
                    <p className="text-xs font-semibold text-whatsapp-deep">
                      {message.replyTo.author}
                    </p>
                    <p className="max-h-10 overflow-hidden text-xs leading-5 text-muted-foreground">
                      {message.replyTo.content}
                    </p>
                  </div>
                )}
                <MessageText
                  text={message.content}
                  signedMetaByKey={signedMetaByKey}
                  onRefreshKey={refreshKey}
                />
                <div className="mt-1 flex items-center justify-end gap-2 text-xs text-muted-foreground">
                  {!isMe && (
                    <div className="flex items-center gap-2">
                      {showSummarize && (
                        <SummarizeButton
                          channelId={channelId}
                          url={firstUrl!}
                          isVideo={firstUrlIsVideo}
                        />
                      )}
                      {showTranslate && (
                        <TranslateButton
                          channelId={channelId}
                          message={message}
                        />
                      )}
                    </div>
                  )}
                  <span>{message.time}</span>
                  {isMe && <CheckCheck className="size-4 text-whatsapp-deep" />}
                </div>
              </div>
            </div>
          );
        })
      )}
      <div ref={bottomRef} />
    </div>
  );
}

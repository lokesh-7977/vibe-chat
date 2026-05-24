"use client";

import { startTransition, useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Sparkles, X } from "lucide-react";

import { streamAiActionStream } from "@/apis/ai-actions";
import { Markdown } from "@/components/markdown";

export function ChannelSummarySheet({
  open,
  onOpenChange,
  channelId,
  channelName,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  channelId: string;
  channelName: string;
}) {
  const [result, setResult] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortedRef = useRef(false);

  const run = useCallback(async () => {
    abortedRef.current = false;
    setLoading(true);
    setError(null);
    setResult("");

    try {
      const body = await streamAiActionStream(channelId, {
        action: "auto",
        messageId: null,
        input: "Summarize the recent conversations in this channel",
        targetLanguage: null,
      });
      const reader = body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let text = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (abortedRef.current) { reader.cancel(); break; }

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const block of parts) {
          const eventLine = block.split("\n").find((l) => l.startsWith("event: "));
          const dataLine = block.split("\n").find((l) => l.startsWith("data: "));
          if (!dataLine) continue;
          const evt = eventLine?.slice(7).trim() ?? "";
          try {
            const data = JSON.parse(dataLine.slice(6));
            if (evt === "token" && data.content) {
              text += String(data.content);
              setResult(text);
            }
            if (evt === "error" && data.message) {
              throw new Error(data.message);
            }
          } catch (e) {
            if (e instanceof Error) throw e;
          }
        }
      }
      if (!abortedRef.current && !text) setError("Could not parse summary");
    } catch (err) {
      if (!abortedRef.current) setError(err instanceof Error ? err.message : "Summarization failed");
    } finally {
      if (!abortedRef.current) setLoading(false);
    }
  }, [channelId]);

  useEffect(() => {
    if (!open) return;
    startTransition(() => { run(); });
    return () => {
      setResult("");
      setError(null);
      setLoading(false);
    };
  }, [open, run]);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [result]);

  return (
    <>
      {open && (
        <div className="fixed inset-0 z-40 bg-black/20" onClick={() => onOpenChange(false)} />
      )}
      <div
        className={
          "fixed right-0 top-0 z-50 flex h-full w-full max-w-lg flex-col border-l border-whatsapp-border bg-card shadow-xl transition-transform duration-300 " +
          (open ? "translate-x-0" : "translate-x-full")
        }
      >
        <div className="flex items-center justify-between border-b border-whatsapp-border px-4 py-3">
          <div className="flex items-center gap-2">
            <Sparkles className="size-4 text-whatsapp-deep" />
            <h2 className="text-sm font-semibold">Channel Summary</h2>
          </div>
          <button
            type="button"
            className="flex size-8 items-center justify-center rounded-md text-muted-foreground hover:bg-whatsapp-muted transition-colors"
            onClick={() => onOpenChange(false)}
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="mb-3 rounded-lg bg-whatsapp-muted/50 p-3 text-sm text-muted-foreground">
            <p className="mb-1 text-xs font-semibold text-foreground">Channel</p>
            <p className="break-words leading-6">#{channelName}</p>
          </div>

          {loading && !result && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              <span>Summarizing conversations...</span>
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          {result && (
            <div className="rounded-lg border border-whatsapp-border bg-whatsapp-surface p-3">
              <Markdown content={result} />
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>
    </>
  );
}

"use client";

import { useRef, useState } from "react";
import { streamSummarizeImage } from "@/apis/uploads";
import { useToast } from "@/providers/toast-provider";
import { Markdown } from "@/components/markdown";

export function ImageSummarizeDialog({
  open,
  onOpenChange,
  objectKey,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  objectKey: string;
}) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortedRef = useRef(false);

  async function run() {
    setLoading(true);
    setError(null);
    setResult(null);
    abortedRef.current = false;

    try {
      const body = await streamSummarizeImage(objectKey);
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
          const evt = eventLine?.slice(7).trim() ?? "";
          const data = JSON.parse(dataLine?.slice(6) ?? "{}");

          if (evt === "token" && data.content) {
            text += String(data.content);
            setResult(text);
          }
          if (evt === "error" && data.message) {
            throw new Error(data.message);
          }
        }
      }
    } catch (e) {
      if (abortedRef.current) return;
      const msg = e instanceof Error ? e.message : "Failed to summarize image";
      setError(msg);
      toast({ title: "Image summary failed", description: msg, kind: "error" });
    } finally {
      if (!abortedRef.current) setLoading(false);
    }
  }

  function handleClose() {
    abortedRef.current = true;
    setLoading(false);
    setResult(null);
    setError(null);
    onOpenChange(false);
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={handleClose} />
      <div className="relative z-10 flex w-full max-w-xl max-h-[80vh] flex-col overflow-hidden rounded-xl border border-whatsapp-border bg-card shadow-xl">
        <div className="flex items-center justify-between gap-4">
          <div className="p-4 text-sm font-semibold">Summarize image</div>
          <button
            type="button"
            className="m-4 rounded-md px-2 py-1 text-xs hover:bg-whatsapp-muted"
            onClick={handleClose}
          >
            Close
          </button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-4">
          <div className="space-y-3">
            {!result && (
            <button
              type="button"
              className="inline-flex items-center justify-center rounded-md bg-whatsapp px-3 py-2 text-xs font-semibold text-whatsapp-foreground hover:bg-whatsapp/90 disabled:opacity-50"
            onClick={run}
            disabled={loading}
          >
            {loading ? "Summarizing..." : "Generate summary"}
          </button>
            )}

          {error && <div className="text-xs text-red-600">{error}</div>}

          {result && (
            <div className="rounded-lg border border-whatsapp-border bg-whatsapp-surface p-3">
              <Markdown content={result} />
            </div>
          )}
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import { Languages } from "lucide-react";

import { streamAiActionStream } from "@/apis/ai-actions";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import type { Message } from "@/types/chats";

export const _translatedContents = new Set<string>();

export function TranslateDialog({
  open,
  onOpenChange,
  channelId,
  message,
  language,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  channelId: string;
  message: Message;
  language: string;
}) {
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortedRef = useRef(false);

  useEffect(() => {
    if (!open) return;

    abortedRef.current = false;
    let cancelled = false;

    (async () => {
      try {
        const body = await streamAiActionStream(channelId, {
          action: "auto",
          messageId: message.id,
          input: `Translate this message to ${language}: ${message.content}`,
          targetLanguage: language,
        });
        const reader = body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let text = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          if (cancelled || abortedRef.current) { reader.cancel(); break; }

          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop() ?? "";

          for (const block of parts) {
            const eventLine = block.split("\n").find((l) => l.startsWith("event: "));
            const dataLine = block.split("\n").find((l) => l.startsWith("data: "));
            if (!dataLine) continue;
            const evt = eventLine?.slice(7).trim() ?? "";
            const data = JSON.parse(dataLine.slice(6));
            if (evt === "token" && data.content) {
              text += String(data.content);
              setResult(text);
            }
            if (evt === "error" && data.message) {
              throw new Error(data.message);
            }
          }
        }

        if (!cancelled && text) {
          _translatedContents.add(text);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Translation failed");
      }
    })();

    return () => { cancelled = true; setResult(null); setError(null); };
  }, [open, channelId, message.id, message.content, language]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[80vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Languages className="size-4 text-whatsapp-deep" />
            Translate to {language}
          </DialogTitle>
        </DialogHeader>

        <div className="scroll-smooth flex-1 space-y-3 overflow-y-auto pr-1" style={{ maxHeight: "calc(80vh - 10rem)" }}>
          <div className="rounded-lg bg-whatsapp-muted/50 p-3 text-sm text-muted-foreground">
            <p className="mb-1 text-xs font-semibold text-foreground">Original</p>
            <p className="whitespace-pre-wrap break-words leading-6">{message.content}</p>
          </div>

          <div className="rounded-lg bg-whatsapp-bubble/20 p-3 text-sm">
            <p className="mb-1 text-xs font-semibold text-foreground">Translation</p>
            {result ? (
              <p className="whitespace-pre-wrap break-words leading-6">{result}</p>
            ) : error ? (
              <p className="text-red-500">{error}</p>
            ) : (
              <div className="flex items-center gap-2 text-muted-foreground">
                <span className="inline-block size-2 animate-pulse rounded-full bg-whatsapp-deep" />
                <span>Translating...</span>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

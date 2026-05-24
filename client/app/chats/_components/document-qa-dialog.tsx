"use client";

import { useState } from "react";
import { streamDocumentQa } from "@/apis/uploads";
import { useToast } from "@/providers/toast-provider";
import { Markdown } from "@/components/markdown";

function parseSseBlocks(buffer: string): { blocks: string[]; rest: string } {
  const parts = buffer.split("\n\n");
  const rest = parts.pop() ?? "";
  return { blocks: parts, rest };
}

export function DocumentQaDialog({
  open,
  onOpenChange,
  objectKey,
  title,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  objectKey: string;
  title: string;
}) {
  const { toast } = useToast();
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  async function run() {
    const q = question.trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    setAnswer("");
    try {
      const body = await streamDocumentQa(objectKey, q);
      const reader = body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let text = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parsed = parseSseBlocks(buffer);
        buffer = parsed.rest;
        for (const block of parsed.blocks) {
          const eventLine = block.split("\n").find((l) => l.startsWith("event: "));
          const dataLine = block.split("\n").find((l) => l.startsWith("data: "));
          if (!dataLine) continue;
          const evt = eventLine?.slice(7).trim() ?? "";
          const raw = dataLine.slice(6);
          try {
            const data = JSON.parse(raw);
            if (evt === "token" && data.content) {
              text += String(data.content);
              setAnswer(text);
            }
            if (evt === "error" && data.message) throw new Error(String(data.message));
          } catch (e) {
            if (e instanceof Error) throw e;
          }
        }
      }
      // If the model couldn't answer from the document, don't show a generic "answer".
      if (text.trim().toLowerCase() === "insufficient information in the document.") {
        setAnswer("");
        setError("Not found in this document. Ask something that’s explicitly covered in the PDF/DOCX.");
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to answer question";
      setError(msg);
      toast({ title: "Q&A failed", description: msg, kind: "error" });
    } finally {
      setLoading(false);
    }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={() => onOpenChange(false)} />
      <div className="relative z-10 flex w-full max-w-2xl max-h-[80vh] flex-col overflow-hidden rounded-xl border border-whatsapp-border bg-card shadow-xl">
        <div className="flex items-center justify-between gap-4">
          <div className="min-w-0">
            <div className="truncate p-4 pb-0 text-sm font-semibold">Ask a question</div>
            <div className="truncate px-4 pb-3 text-xs text-muted-foreground">{title}</div>
          </div>
          <button
            type="button"
            className="m-4 rounded-md px-2 py-1 text-xs hover:bg-whatsapp-muted"
            onClick={() => {
              setLoading(false);
              setError(null);
              setAnswer("");
              onOpenChange(false);
            }}
          >
            Close
          </button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-4 space-y-3">
          <textarea
            className="min-h-20 w-full resize-none rounded-md border border-whatsapp-border bg-whatsapp-surface p-3 text-sm outline-none focus:ring-2 focus:ring-whatsapp/40"
            placeholder="Ask about this PDF/DOCX..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-md bg-whatsapp px-3 py-2 text-xs font-semibold text-whatsapp-foreground hover:bg-whatsapp/90 disabled:opacity-50"
            onClick={run}
            disabled={loading || !question.trim()}
          >
            {loading ? "Answering..." : "Ask"}
          </button>

          {error && <div className="text-xs text-red-600">{error}</div>}

          {answer && (
            <div className="rounded-lg border border-whatsapp-border bg-whatsapp-surface p-3">
              <Markdown content={answer} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

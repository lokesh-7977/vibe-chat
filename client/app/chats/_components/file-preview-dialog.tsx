"use client";

import { useEffect } from "react";

export function FilePreviewDialog({
  open,
  onOpenChange,
  title,
  url,
  kind,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  url: string;
  kind: "pdf" | "video";
}) {
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onOpenChange(false);
    }
    if (open) window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40" onClick={() => onOpenChange(false)} />
      <div className="relative z-10 flex w-full max-w-5xl max-h-[90vh] flex-col overflow-hidden rounded-xl border border-whatsapp-border bg-card shadow-xl">
        <div className="flex items-center justify-between gap-4 border-b border-whatsapp-border px-4 py-3">
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold">{title}</div>
            <div className="truncate text-xs text-muted-foreground">{kind.toUpperCase()}</div>
          </div>
          <button
            type="button"
            className="rounded-md px-2 py-1 text-xs hover:bg-whatsapp-muted"
            onClick={() => onOpenChange(false)}
          >
            Close
          </button>
        </div>

        <div className="min-h-0 flex-1 bg-whatsapp-surface">
          {kind === "pdf" ? (
            <iframe title={title} src={url} className="h-full w-full" />
          ) : (
            <video src={url} controls className="h-full w-full bg-black object-contain" />
          )}
        </div>
      </div>
    </div>
  );
}

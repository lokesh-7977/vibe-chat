"use client";

import type { ReactNode } from "react";
import { Fragment } from "react";

function renderInline(text: string): Array<string | ReactNode> {
  // Very small Markdown subset:
  // - **bold**
  // - *italic*
  // - `code`
  const out: Array<string | ReactNode> = [];
  let i = 0;
  const pushText = (t: string) => {
    if (t) out.push(t);
  };

  while (i < text.length) {
    const rest = text.slice(i);
    const bold = rest.match(/^\*\*([^*]+)\*\*/);
    if (bold) {
      pushText("");
      out.push(<strong key={`b-${i}`}>{bold[1]}</strong>);
      i += bold[0].length;
      continue;
    }
    const code = rest.match(/^`([^`]+)`/);
    if (code) {
      out.push(
        <code key={`c-${i}`} className="rounded bg-whatsapp-muted px-1 py-0.5 text-[0.85em]">
          {code[1]}
        </code>,
      );
      i += code[0].length;
      continue;
    }
    const italic = rest.match(/^\*([^*]+)\*/);
    if (italic) {
      out.push(<em key={`i-${i}`}>{italic[1]}</em>);
      i += italic[0].length;
      continue;
    }

    // default: emit one char
    const ch = text[i]!;
    // merge consecutive plain text
    const last = out[out.length - 1];
    if (typeof last === "string") out[out.length - 1] = last + ch;
    else out.push(ch);
    i += 1;
  }

  return out;
}

export function Markdown({ content }: { content: string }) {
  const lines = (content || "").split(/\r?\n/);

  return (
    <div className="text-sm leading-6">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={idx} className="h-2" />;

        if (trimmed.startsWith("### ")) {
          return (
            <div key={idx} className="mt-2 text-sm font-semibold">
              {renderInline(trimmed.slice(4)).map((n, i) => (
                <Fragment key={i}>{n}</Fragment>
              ))}
            </div>
          );
        }
        if (trimmed.startsWith("## ")) {
          return (
            <div key={idx} className="mt-2 text-base font-semibold">
              {renderInline(trimmed.slice(3)).map((n, i) => (
                <Fragment key={i}>{n}</Fragment>
              ))}
            </div>
          );
        }
        if (trimmed.startsWith("# ")) {
          return (
            <div key={idx} className="mt-2 text-base font-semibold">
              {renderInline(trimmed.slice(2)).map((n, i) => (
                <Fragment key={i}>{n}</Fragment>
              ))}
            </div>
          );
        }

        const bullet = trimmed.match(/^[-*]\s+(.*)$/);
        if (bullet) {
          return (
            <div key={idx} className="flex gap-2">
              <div className="mt-2 size-1.5 shrink-0 rounded-full bg-muted-foreground" />
              <div className="min-w-0">
                {renderInline(bullet[1] ?? "").map((n, i) => (
                  <Fragment key={i}>{n}</Fragment>
                ))}
              </div>
            </div>
          );
        }

        return (
          <div key={idx}>
            {renderInline(line).map((n, i) => (
              <Fragment key={i}>{n}</Fragment>
            ))}
          </div>
        );
      })}
    </div>
  );
}

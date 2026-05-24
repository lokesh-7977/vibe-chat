"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { CheckCircle, X, XCircle, Info } from "lucide-react";

type ToastKind = "default" | "error" | "success" | "info";

type Toast = {
  id: string;
  title: string;
  description?: string;
  kind: ToastKind;
  exiting?: boolean;
};

type ToastInput = {
  title: string;
  description?: string;
  kind?: ToastKind;
};

type ToastContextValue = {
  toast: (input: ToastInput) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

const ICONS: Record<ToastKind, ReactNode> = {
  success: <CheckCircle className="size-4 text-green-500" />,
  error: <XCircle className="size-4 text-red-500" />,
  info: <Info className="size-4 text-blue-500" />,
  default: <Info className="size-4 text-muted-foreground" />,
};

const BORDER_COLORS: Record<ToastKind, string> = {
  success: "border-l-green-500",
  error: "border-l-red-500",
  info: "border-l-blue-500",
  default: "border-l-muted-foreground",
};

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: (id: string) => void }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
  }, []);

  return (
    <div
      className={`flex items-start gap-3 rounded-lg border border-whatsapp-border bg-card p-4 text-card-foreground shadow-lg shadow-whatsapp-deep/10 transition-all duration-300 ${
        BORDER_COLORS[toast.kind]} border-l-4 ${
        visible ? "translate-x-0 opacity-100" : "translate-x-4 opacity-0"
      } ${toast.exiting ? "translate-x-full opacity-0" : ""}`}
      role="status"
    >
      <div className="mt-0.5 shrink-0">{ICONS[toast.kind]}</div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium">{toast.title}</p>
        {toast.description && (
          <p className="mt-0.5 text-xs text-muted-foreground">{toast.description}</p>
        )}
      </div>
      <button
        aria-label="Dismiss"
        className="-mr-1 -mt-1 shrink-0 rounded-md p-1 text-muted-foreground transition-colors hover:bg-whatsapp-muted hover:text-foreground"
        onClick={() => onDismiss(toast.id)}
      >
        <X className="size-3.5" />
      </button>
    </div>
  );
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const dismiss = useCallback((id: string) => {
    setToasts((current) =>
      current.map((t) => (t.id === id ? { ...t, exiting: true } : t)),
    );
    setTimeout(() => {
      setToasts((current) => current.filter((t) => t.id !== id));
    }, 300);
  }, []);

  const toast = useCallback(
    (input: ToastInput) => {
      const id = crypto.randomUUID();
      setToasts((current) => [
        ...current,
        {
          id,
          title: input.title,
          description: input.description,
          kind: input.kind ?? "default",
        },
      ]);
      const timer = setTimeout(() => dismiss(id), 4000);
      timersRef.current.set(id, timer);
    },
    [dismiss],
  );

  useEffect(() => {
    return () => {
      for (const timer of timersRef.current.values()) clearTimeout(timer);
    };
  }, []);

  const value = useMemo(() => ({ toast }), [toast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed right-4 top-4 z-50 flex w-full max-w-sm flex-col gap-2">
        {toasts.map((item) => (
          <ToastItem key={item.id} toast={item} onDismiss={dismiss} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used within ToastProvider");
  return context;
}

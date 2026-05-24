"use client";

import { useEffect, useState } from "react";
import { Settings, Loader2 } from "lucide-react";

import { getProfile, updateProfile, logoutUser } from "@/apis/auth";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { updateUser, clearAuth } from "@/store/slices/auth-slice";

export function SettingsDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const dispatch = useAppDispatch();
  const user = useAppSelector((s) => s.auth.user);
  const [fullName, setFullName] = useState(user?.fullName ?? "");
  const [username, setUsername] = useState(user?.username ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setLoading(true);
    getProfile()
      .then((res) => {
        if (cancelled || !res.data) return;
        setFullName(res.data.fullName);
        setUsername(res.data.username);
        setEmail(res.data.email);
        dispatch(updateUser(res.data));
      })
      .catch(() => {
        if (!cancelled) setSaveError("Failed to load profile");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [open, dispatch]);

  async function handleSave() {
    setSaving(true);
    setSaveError(null);
    try {
      const res = await updateProfile({ fullName, username, email });
      if (res.success && res.data) {
        dispatch(updateUser(res.data));
        onOpenChange(false);
      } else {
        setSaveError(res.message ?? "Failed to update profile");
      }
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to update profile");
    } finally {
      setSaving(false);
    }
  }

  async function handleLogout() {
    try {
      await logoutUser();
    } catch {
      // ignore server error
    }
    dispatch(clearAuth());
    if (typeof window !== "undefined") {
      window.location.href = "/auth";
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="size-4" />
            Settings
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">Full name</label>
            <input
              className="w-full rounded-lg border border-whatsapp-border bg-whatsapp-surface px-3 py-2 text-sm outline-none focus:border-whatsapp focus:ring-1 focus:ring-whatsapp"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">Username</label>
            <input
              className="w-full rounded-lg border border-whatsapp-border bg-whatsapp-surface px-3 py-2 text-sm outline-none focus:border-whatsapp focus:ring-1 focus:ring-whatsapp"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">Email</label>
            <input
              className="w-full rounded-lg border border-whatsapp-border bg-whatsapp-surface px-3 py-2 text-sm outline-none focus:border-whatsapp focus:ring-1 focus:ring-whatsapp"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          {saveError && (
            <p className="text-xs text-red-500">{saveError}</p>
          )}

          <div className="flex items-center justify-between gap-3 pt-2">
            <button
              type="button"
              className="rounded-md px-3 py-2 text-xs font-medium text-red-500 hover:bg-red-50 transition-colors"
              onClick={handleLogout}
            >
              Log out
            </button>

            <div className="flex items-center gap-2">
              <button
                type="button"
                className="rounded-md px-3 py-2 text-xs font-medium text-muted-foreground hover:bg-whatsapp-muted transition-colors"
                onClick={() => onOpenChange(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="inline-flex items-center gap-1.5 rounded-md bg-whatsapp px-4 py-2 text-xs font-semibold text-whatsapp-foreground hover:bg-whatsapp/90 disabled:opacity-50 transition-colors"
                onClick={handleSave}
                disabled={saving}
              >
                {saving && <Loader2 className="size-3.5 animate-spin" />}
                Save
              </button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

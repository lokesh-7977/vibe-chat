"use client";

import { useState } from "react";
import { Hash, LoaderCircle, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Field, FieldContent, FieldGroup, FieldLabel, FieldSet } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { createChannelThunk } from "@/store/slices/chats-slice";

export function CreateChannelDialog({
  open,
  onClose,
  workspaceId,
}: {
  open: boolean;
  onClose: () => void;
  workspaceId: string;
}) {
  const dispatch = useAppDispatch();
  const isLoading = useAppSelector((s) => s.chats.status === "loading");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || isLoading) return;
    dispatch(
      createChannelThunk({
        workspaceId,
        name: name.trim(),
        slug: name.trim().toLowerCase().replace(/\s+/g, "-"),
        description: description.trim() || null,
        channelType: "chat",
        createdById: null,
      }),
    );
    setName("");
    setDescription("");
    onClose();
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="flex size-8 items-center justify-center rounded-lg bg-whatsapp text-whatsapp-foreground">
              <Hash className="size-4" />
            </div>
            <DialogTitle>New channel</DialogTitle>
          </div>
          <DialogDescription>
            Create a channel for focused conversations.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <FieldSet>
            <FieldGroup className="gap-4">
              <Field>
                <FieldLabel>Channel name</FieldLabel>
                <FieldContent>
                  <Input
                    className="h-10"
                    placeholder="e.g. design-review"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    autoFocus
                    required
                  />
                </FieldContent>
              </Field>
              <Field>
                <FieldLabel>Description</FieldLabel>
                <FieldContent>
                  <Input
                    className="h-10"
                    placeholder="What is this channel for?"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                  />
                </FieldContent>
                <p className="mt-1 text-xs text-muted-foreground">
                  AI uses channel context to summarize and surface relevant messages.
                </p>
              </Field>
            </FieldGroup>
          </FieldSet>

          <DialogFooter className="mt-6">
            <Button
              type="button"
              variant="outline"
              onClick={() => { setName(""); setDescription(""); onClose(); }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="gap-2 bg-whatsapp text-whatsapp-foreground hover:bg-whatsapp/90"
              disabled={isLoading || !name.trim()}
            >
              {isLoading ? (
                <LoaderCircle className="size-4 animate-spin" />
              ) : (
                <Sparkles className="size-4" />
              )}
              {isLoading ? "Creating..." : "Create channel"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

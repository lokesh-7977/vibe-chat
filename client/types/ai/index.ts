import type { DateTimeString, JsonValue, UUID } from "../common";

export type AIInteractionBase = {
  workspaceId: UUID;
  channelId: UUID | null;
  userId: UUID | null;
  input: string;
  output: string | null;
  status: string;
  model: string | null;
  provider: string | null;
  tokensInput: number | null;
  tokensOutput: number | null;
  cost: number | null;
  latencyMs: number | null;
};

export type AIInteractionCreate = AIInteractionBase;

export type AIInteractionUpdate = {
  output: string | null;
  status: string | null;
  model: string | null;
  provider: string | null;
  tokensInput: number | null;
  tokensOutput: number | null;
  cost: number | null;
  latencyMs: number | null;
};

export type AIInteractionResponse = AIInteractionBase & {
  id: UUID;
  createdAt: DateTimeString;
};

export type AIRunBase = {
  interactionId: UUID;
  workflowName: string;
  status: string;
  state: Record<string, JsonValue> | null;
};

export type AIRunCreate = AIRunBase;

export type AIRunUpdate = {
  status: string | null;
  state: Record<string, JsonValue> | null;
  completedAt: DateTimeString | null;
};

export type AIRunResponse = AIRunBase & {
  id: UUID;
  startedAt: DateTimeString;
  completedAt: DateTimeString | null;
};

export type AIRunStepBase = {
  aiRunId: UUID;
  stepName: string;
  stepType: string;
  input: Record<string, JsonValue> | null;
  output: Record<string, JsonValue> | null;
  status: string;
};

export type AIRunStepCreate = AIRunStepBase;

export type AIRunStepUpdate = {
  output: Record<string, JsonValue> | null;
  status: string | null;
  completedAt: DateTimeString | null;
};

export type AIRunStepResponse = AIRunStepBase & {
  id: UUID;
  startedAt: DateTimeString;
  completedAt: DateTimeString | null;
};

export type AIActionStreamRequest = {
  action: string;
  messageId: UUID | null;
  input: string;
  targetLanguage: string | null;
  privateResponse?: boolean | null;
  history?: { role: "user" | "assistant"; content: string }[] | null;
};

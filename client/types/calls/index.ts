import type { DateTimeString, JsonValue, UUID } from "../common";

export type CallBase = {
  workspaceId: UUID;
  channelId: UUID | null;
  startedById: UUID | null;
  title: string | null;
  status: string;
  startedAt: DateTimeString | null;
  endedAt: DateTimeString | null;
};

export type CallCreate = CallBase;

export type CallUpdate = {
  status: string | null;
  title: string | null;
  startedAt: DateTimeString | null;
  endedAt: DateTimeString | null;
};

export type CallResponse = CallBase & {
  id: UUID;
};

export type CallParticipantBase = {
  callId: UUID;
  userId: UUID;
  joinedAt: DateTimeString;
  leftAt: DateTimeString | null;
  isMuted: boolean;
  isCameraOn: boolean;
  isScreenSharing: boolean;
};

export type CallParticipantCreate = CallParticipantBase;

export type CallParticipantUpdate = {
  leftAt: DateTimeString | null;
  isMuted: boolean | null;
  isCameraOn: boolean | null;
  isScreenSharing: boolean | null;
};

export type CallParticipantResponse = CallParticipantBase & {
  id: UUID;
};

export type CallTranscriptBase = {
  callId: UUID;
  speakerId: UUID | null;
  content: string;
  startedAt: DateTimeString | null;
  endedAt: DateTimeString | null;
};

export type CallTranscriptCreate = CallTranscriptBase;

export type CallTranscriptUpdate = {
  content: string | null;
  startedAt: DateTimeString | null;
  endedAt: DateTimeString | null;
};

export type CallTranscriptResponse = CallTranscriptBase & {
  id: UUID;
};

export type CallSummaryBase = {
  callId: UUID;
  summary: string;
  decisions: Record<string, JsonValue> | null;
  actionItems: Record<string, JsonValue> | null;
};

export type CallSummaryCreate = CallSummaryBase;

export type CallSummaryUpdate = {
  summary: string | null;
  decisions: Record<string, JsonValue> | null;
  actionItems: Record<string, JsonValue> | null;
};

export type CallSummaryResponse = CallSummaryBase & {
  id: UUID;
  createdAt: DateTimeString;
};

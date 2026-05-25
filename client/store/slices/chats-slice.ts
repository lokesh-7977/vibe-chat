import {
  createAsyncThunk,
  createSlice,
  type PayloadAction,
} from "@reduxjs/toolkit";

import {
  listChannelActivities,
  createChannelActivity,
} from "@/apis/activities";
import { streamAiActionStream } from "@/apis/ai-actions";
import { createChannel, deleteChannel, updateChannel } from "@/apis/channels";
import { listChannels } from "@/apis/channels";
import { listUsers } from "@/apis/users";
import { createWorkspace, listWorkspaces } from "@/apis/workspaces";
import type {
  ActivityResponse,
  ChannelCreate,
  ChannelResponse,
  UserResponse,
  WorkspaceCreate,
  WorkspaceResponse,
} from "@/types";
import type { Message, Room } from "@/types/chats";

type LoadChatsPayload = {
  rooms: Room[];
  messagesByRoom: Record<string, Message[]>;
  selectedRoomId: string;
  needsWorkspace: boolean;
  workspaces: WorkspaceResponse[];
  currentWorkspaceId: string | null;
  usersById: Record<string, UserResponse>;
};

type ChatsState = {
  selectedRoomId: string;
  rooms: Room[];
  messagesByRoom: Record<string, Message[]>;
  workspaces: WorkspaceResponse[];
  currentWorkspaceId: string | null;
  usersById: Record<string, UserResponse>;
  typingByChannel: Record<string, string[]>;
  status: "idle" | "loading" | "ready" | "error";
  error: string | null;
  needsWorkspace: boolean;
};

const initialState: ChatsState = {
  selectedRoomId: "",
  rooms: [],
  messagesByRoom: {},
  workspaces: [],
  currentWorkspaceId: null,
  usersById: {},
  typingByChannel: {},
  status: "idle",
  error: null,
  needsWorkspace: false,
};

function channelToRoom(channel: ChannelResponse): Room {
  return {
    id: channel.id,
    name: channel.name,
    description: channel.description ?? channel.channelType,
    time: new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    }),
    unread: 0,
    avatar: channel.name
      .split(" ")
      .slice(0, 2)
      .map((part) => part[0])
      .join("")
      .toUpperCase(),
    online: true,
  };
}

function activityToMessage(
  activity: ActivityResponse,
  currentUserId?: string | null,
): Message {
  const actorId =
    (
      activity as unknown as {
        actorId?: string | null;
        actor_id?: string | null;
      }
    ).actorId ??
    (activity as unknown as { actor_id?: string | null }).actor_id ??
    null;
  const actorName =
    (
      activity as unknown as {
        actorName?: string | null;
        actor_name?: string | null;
      }
    ).actorName ??
    (activity as unknown as { actor_name?: string | null }).actor_name ??
    null;
  const activityType =
    (
      activity as unknown as {
        activityType?: string | null;
        activity_type?: string | null;
      }
    ).activityType ??
    (activity as unknown as { activity_type?: string | null }).activity_type ??
    null;
  const isMe = Boolean(currentUserId && actorId && currentUserId === actorId);
  return {
    id: activity.id,
    userId: actorId,
    author: isMe ? "You" : (actorName ?? "Member"),
    role: isMe ? "me" : "member",
    content: activity.content ?? "",
    isAi: activityType === "ai_message",
    time: new Date(activity.createdAt).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    }),
  };
}

async function fetchChats(
  workspaceId?: string,
  currentUserId?: string | null,
): Promise<LoadChatsPayload> {
  const workspaceResponse = await listWorkspaces();
  const workspaces = workspaceResponse.data ?? [];
  if (!workspaces.length) {
    return {
      rooms: [],
      messagesByRoom: {},
      selectedRoomId: "",
      needsWorkspace: true,
      workspaces: [],
      currentWorkspaceId: null,
      usersById: {},
    };
  }

  const target = workspaceId
    ? (workspaces.find((w) => w.id === workspaceId) ?? workspaces[0])
    : workspaces[0];

  const [channelResponse, usersResponse] = await Promise.all([
    listChannels(target.id),
    listUsers(),
  ]);

  const usersById: Record<string, UserResponse> = {};
  for (const u of usersResponse.data ?? []) {
    usersById[u.id] = u;
  }

  const apiRooms = (channelResponse.data ?? []).map(channelToRoom);

  const nextMessagesByRoom: Record<string, Message[]> = {};
  await Promise.all(
    apiRooms.map(async (room) => {
      const response = await listChannelActivities(room.id);
      const sorted = (response.data ?? []).sort(
        (a, b) =>
          new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime(),
      );
      nextMessagesByRoom[room.id] = sorted
        .map((a) => activityToMessage(a, currentUserId))
        .filter((m) => m.isAi !== true);
    }),
  );

  const savedRoomId = loadSavedRoomId();
  const resolvedRoomId =
    savedRoomId && apiRooms.some((r) => r.id === savedRoomId)
      ? savedRoomId
      : (apiRooms[0]?.id ?? "");

  return {
    rooms: apiRooms,
    messagesByRoom: nextMessagesByRoom,
    selectedRoomId: resolvedRoomId,
    needsWorkspace: false,
    workspaces,
    currentWorkspaceId: target.id,
    usersById,
  };
}

const WS_STORAGE_KEY = "vibe-chat-workspace";
const ROOM_STORAGE_KEY = "vibe-chat-room";

function loadSavedRoomId(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return sessionStorage.getItem(ROOM_STORAGE_KEY);
  } catch {
    return null;
  }
}

function saveRoomId(id: string) {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(ROOM_STORAGE_KEY, id);
  } catch {
    /* ignore */
  }
}

export const loadChats = createAsyncThunk<LoadChatsPayload>(
  "chats/loadChats",
  async (_, { getState }) => {
    const userId = (getState() as { auth: { user?: { id: string } | null } })
      .auth.user?.id;
    const saved =
      typeof window !== "undefined"
        ? sessionStorage.getItem(WS_STORAGE_KEY)
        : null;
    return fetchChats(saved ?? undefined, userId);
  },
);

export const switchWorkspace = createAsyncThunk<LoadChatsPayload, string>(
  "chats/switchWorkspace",
  async (workspaceId, { getState }) => {
    const userId = (getState() as { auth: { user?: { id: string } | null } })
      .auth.user?.id;
    return fetchChats(workspaceId, userId);
  },
);

export const createWorkspaceThunk = createAsyncThunk<
  LoadChatsPayload,
  WorkspaceCreate
>("chats/createWorkspace", async (payload, { getState }) => {
  await createWorkspace(payload);
  const userId = (getState() as { auth: { user?: { id: string } | null } }).auth
    .user?.id;
  return fetchChats(undefined, userId);
});

export const createChannelThunk = createAsyncThunk<
  LoadChatsPayload,
  ChannelCreate
>("chats/createChannel", async (payload, { getState }) => {
  await createChannel(payload);
  const userId = (getState() as { auth: { user?: { id: string } | null } }).auth
    .user?.id;
  return fetchChats(undefined, userId);
});

export const silentRefreshChats = createAsyncThunk<LoadChatsPayload, void>(
  "chats/silentRefreshChats",
  async (_, { getState }) => {
    const userId = (getState() as { auth: { user?: { id: string } | null } })
      .auth.user?.id;
    const saved =
      typeof window !== "undefined"
        ? sessionStorage.getItem(WS_STORAGE_KEY)
        : null;
    return fetchChats(saved ?? undefined, userId);
  },
);

export const deleteChannelThunk = createAsyncThunk<string, string>(
  "chats/deleteChannel",
  async (channelId) => {
    await deleteChannel(channelId);
    return channelId;
  },
);

export const updateChannelThunk = createAsyncThunk<
  { channelId: string; name: string; description: string },
  { channelId: string; name: string; description: string }
>("chats/updateChannel", async ({ channelId, name, description }) => {
  await updateChannel(channelId, {
    name,
    description,
    slug: null,
    channelType: null,
  });
  return { channelId, name, description };
});

export const sendChatMessage = createAsyncThunk<
  Message,
  { channelId: string; content: string }
>("chats/sendChatMessage", async ({ channelId, content }, { getState }) => {
  const response = await createChannelActivity(channelId, {
    content,
    activityType: "chat_message",
    metaData: null,
    parentActivityId: null,
  });

  if (!response.data) throw new Error(response.message || "Message not sent");

  const rootState = getState() as {
    auth: { user?: { id: string } | null };
    chats: ChatsState;
  };
  const userId = rootState.auth.user?.id;

  // The user just sent this message from this client; treat it as "me" even if
  // auth state hasn't loaded yet.
  const base = activityToMessage(response.data, userId);
  return {
    ...base,
    userId: userId ?? response.data.actorId ?? null,
    author: "You",
    role: "me",
  };
});

export const sendPrivateAiMessage = createAsyncThunk<
  void,
  { channelId: string; content: string }
>(
  "chats/sendPrivateAiMessage",
  async ({ channelId, content }, { dispatch, getState }) => {
    const rootState = getState() as {
      auth: { user?: { id: string; fullName?: string | null } | null };
      chats: ChatsState;
    };

    const prompt = content.replace(/^@vibe-chat\b[:,-]?\s*/i, "").trim();
    if (!prompt) return;

    const recent = rootState.chats.messagesByRoom[channelId] ?? [];
    const history: { role: "user" | "assistant"; content: string }[] = recent
      .filter((m) => (m.content || "").trim().length > 0)
      .slice(-30)
      .map((m) => ({
        role: (m.role === "me" ? "user" : m.isAi ? "assistant" : "user") as
          | "user"
          | "assistant",
        content: m.content,
      }));

    const now = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    const userMsgId = crypto.randomUUID();
    const aiMsgId = crypto.randomUUID();

    dispatch(
      chatsSlice.actions.addLocalMessage({
        channelId,
        message: {
          id: userMsgId,
          userId: rootState.auth.user?.id ?? null,
          author: "You",
          role: "me",
          content,
          time: now,
          isPrivate: true,
        },
      }),
    );

    dispatch(
      chatsSlice.actions.addLocalMessage({
        channelId,
        message: {
          id: aiMsgId,
          userId: null,
          author: "Aura Chat",
          role: "member",
          content: "",
          time: now,
          isAi: true,
          isPrivate: true,
          isStreaming: true,
        },
      }),
    );

    const body = await streamAiActionStream(channelId, {
      action: "auto",
      messageId: null,
      input: prompt,
      targetLanguage: null,
      privateResponse: true,
      history,
    });

    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let text = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const block of parts) {
        const eventLine = block
          .split("\n")
          .find((l) => l.startsWith("event: "));
        const dataLine = block.split("\n").find((l) => l.startsWith("data: "));
        if (!dataLine) continue;
        const evt = eventLine?.slice(7).trim() ?? "";
        const data = JSON.parse(dataLine.slice(6));
        if (evt === "token" && data.content) {
          text += String(data.content);
          dispatch(
            chatsSlice.actions.updateLocalMessage({
              channelId,
              messageId: aiMsgId,
              content: text,
            }),
          );
        }
        if (evt === "error" && data.message) {
          throw new Error(data.message);
        }
      }
    }

    dispatch(
      chatsSlice.actions.setLocalMessageStreaming({
        channelId,
        messageId: aiMsgId,
        isStreaming: false,
      }),
    );
  },
);

const chatsSlice = createSlice({
  name: "chats",
  initialState,
  reducers: {
    addLocalMessage(
      state,
      action: PayloadAction<{ channelId: string; message: Message }>,
    ) {
      state.messagesByRoom[action.payload.channelId] ??= [];
      state.messagesByRoom[action.payload.channelId].push(
        action.payload.message,
      );
      const room = state.rooms.find((r) => r.id === action.payload.channelId);
      if (room) room.time = action.payload.message.time;
    },
    updateLocalMessage(
      state,
      action: PayloadAction<{
        channelId: string;
        messageId: string;
        content: string;
      }>,
    ) {
      const list = state.messagesByRoom[action.payload.channelId];
      if (!list) return;
      const msg = list.find((m) => m.id === action.payload.messageId);
      if (msg) msg.content = action.payload.content;
    },
    setLocalMessageStreaming(
      state,
      action: PayloadAction<{
        channelId: string;
        messageId: string;
        isStreaming: boolean;
      }>,
    ) {
      const list = state.messagesByRoom[action.payload.channelId];
      if (!list) return;
      const msg = list.find((m) => m.id === action.payload.messageId);
      if (msg) msg.isStreaming = action.payload.isStreaming;
    },
    selectRoom(state, action: PayloadAction<string>) {
      if (state.rooms.some((r) => r.id === action.payload)) {
        state.selectedRoomId = action.payload;
        const room = state.rooms.find((r) => r.id === action.payload);
        if (room) room.unread = 0;
        saveRoomId(action.payload);
      }
    },
    receiveRealtimeEvent(
      state,
      action: PayloadAction<{ channelId: string; message: Message }>,
    ) {
      state.messagesByRoom[action.payload.channelId] ??= [];
      state.messagesByRoom[action.payload.channelId].push(
        action.payload.message,
      );
      const room = state.rooms.find((r) => r.id === action.payload.channelId);
      if (room) {
        room.time = action.payload.message.time;
        if (action.payload.channelId !== state.selectedRoomId) {
          room.unread = (room.unread ?? 0) + 1;
        }
        const idx = state.rooms.indexOf(room);
        if (idx > 0) {
          state.rooms.splice(idx, 1);
          state.rooms.unshift(room);
        }
      }
    },
    setTyping(
      state,
      action: PayloadAction<{ channelId: string; userId: string }>,
    ) {
      const { channelId, userId } = action.payload;
      state.typingByChannel[channelId] ??= [];
      if (!state.typingByChannel[channelId].includes(userId)) {
        state.typingByChannel[channelId].push(userId);
      }
    },
    clearTyping(
      state,
      action: PayloadAction<{ channelId: string; userId: string }>,
    ) {
      const { channelId, userId } = action.payload;
      if (state.typingByChannel[channelId]) {
        state.typingByChannel[channelId] = state.typingByChannel[
          channelId
        ].filter((id) => id !== userId);
      }
    },
  },
  extraReducers: (builder) => {
    const handleFulfilled = (
      state: ChatsState,
      action: { payload: LoadChatsPayload },
    ) => {
      state.status = "ready";
      state.rooms = action.payload.rooms;
      state.messagesByRoom = action.payload.messagesByRoom;
      state.selectedRoomId = action.payload.selectedRoomId;
      state.needsWorkspace = action.payload.needsWorkspace;
      state.workspaces = action.payload.workspaces;
      state.currentWorkspaceId = action.payload.currentWorkspaceId;
      state.usersById = action.payload.usersById;
      if (typeof window !== "undefined" && action.payload.currentWorkspaceId) {
        sessionStorage.setItem(
          WS_STORAGE_KEY,
          action.payload.currentWorkspaceId,
        );
      }
    };

    const handleSilentFulfilled = (
      state: ChatsState,
      action: { payload: LoadChatsPayload },
    ) => {
      // Preserve existing selectedRoomId, keep status unchanged
      const prevSelected = state.selectedRoomId;
      state.rooms = action.payload.rooms;
      state.messagesByRoom = action.payload.messagesByRoom;
      state.selectedRoomId = prevSelected || action.payload.selectedRoomId;
      state.needsWorkspace = action.payload.needsWorkspace;
      state.workspaces = action.payload.workspaces;
      state.currentWorkspaceId = action.payload.currentWorkspaceId;
      state.usersById = action.payload.usersById;
      if (typeof window !== "undefined" && action.payload.currentWorkspaceId) {
        sessionStorage.setItem(
          WS_STORAGE_KEY,
          action.payload.currentWorkspaceId,
        );
      }
    };

    builder
      .addCase(loadChats.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(loadChats.fulfilled, handleFulfilled)
      .addCase(loadChats.rejected, (state, action) => {
        state.status = "error";
        state.error = action.error.message ?? "Could not load chats";
      })
      .addCase(switchWorkspace.pending, (state) => {
        state.status = "loading";
      })
      .addCase(switchWorkspace.fulfilled, handleFulfilled)
      .addCase(switchWorkspace.rejected, (state, action) => {
        state.status = "error";
        state.error = action.error.message ?? "Could not switch workspace";
      })
      .addCase(createWorkspaceThunk.pending, (state) => {
        state.status = "loading";
      })
      .addCase(createWorkspaceThunk.fulfilled, handleFulfilled)
      .addCase(createWorkspaceThunk.rejected, (state, action) => {
        state.status = "error";
        state.error = action.error.message ?? "Could not create workspace";
      })
      .addCase(createChannelThunk.pending, (state) => {
        state.status = "loading";
      })
      .addCase(createChannelThunk.fulfilled, handleFulfilled)
      .addCase(createChannelThunk.rejected, (state, action) => {
        state.status = "error";
        state.error = action.error.message ?? "Could not create channel";
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.messagesByRoom[state.selectedRoomId] ??= [];
        state.messagesByRoom[state.selectedRoomId].push(action.payload);
        const room = state.rooms.find((r) => r.id === state.selectedRoomId);
        if (room) room.time = action.payload.time;
      })
      .addCase(deleteChannelThunk.fulfilled, (state, action) => {
        const channelId = action.payload;
        state.rooms = state.rooms.filter((r) => r.id !== channelId);
        delete state.messagesByRoom[channelId];
        delete state.typingByChannel[channelId];
        if (state.selectedRoomId === channelId) {
          const nextId = state.rooms[0]?.id ?? "";
          state.selectedRoomId = nextId;
          saveRoomId(nextId);
        }
      })
      .addCase(updateChannelThunk.fulfilled, (state, action) => {
        const { channelId, name, description } = action.payload;
        const room = state.rooms.find((r) => r.id === channelId);
        if (!room) return;
        room.name = name;
        room.description = description;
        room.avatar = name
          .split(" ")
          .slice(0, 2)
          .map((part) => part[0])
          .join("")
          .toUpperCase();
      })
      .addCase(silentRefreshChats.fulfilled, handleSilentFulfilled);
  },
});

export const {
  addLocalMessage,
  updateLocalMessage,
  setLocalMessageStreaming,
  receiveRealtimeEvent,
  selectRoom,
  setTyping,
  clearTyping,
} = chatsSlice.actions;
export default chatsSlice.reducer;

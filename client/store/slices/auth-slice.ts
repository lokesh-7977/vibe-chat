import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { UserResponse } from "../../types";

const STORAGE_KEY = "aura-chat-auth";

function loadFromSession(): { accessToken: string | null; user: UserResponse | null } {
  if (typeof window === "undefined") return { accessToken: null, user: null };
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return { accessToken: null, user: null };
    return JSON.parse(raw);
  } catch {
    return { accessToken: null, user: null };
  }
}

function saveToSession(accessToken: string, user: UserResponse) {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ accessToken, user }));
  } catch { /* quota exceeded */ }
}

function clearSession() {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch { /* ignore */ }
}

type AuthState = {
  accessToken: string | null;
  user: UserResponse | null;
  isAuthenticated: boolean;
};

const persisted = loadFromSession();
const initialState: AuthState = {
  accessToken: persisted.accessToken ?? null,
  user: persisted.user ?? null,
  isAuthenticated: Boolean(persisted.accessToken),
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setAuth(state, action: PayloadAction<{ accessToken: string; user: UserResponse }>) {
      const { accessToken, user } = action.payload;
      state.accessToken = accessToken;
      state.user = user;
      state.isAuthenticated = true;
      saveToSession(accessToken, user);
    },
    clearAuth(state) {
      state.accessToken = null;
      state.user = null;
      state.isAuthenticated = false;
      clearSession();
    },
    updateUser(state, action: PayloadAction<UserResponse>) {
      state.user = action.payload;
      if (state.accessToken) {
        saveToSession(state.accessToken, action.payload);
      }
    },
  },
});

export const { setAuth, clearAuth, updateUser } = authSlice.actions;
export default authSlice.reducer;

import { configureStore } from "@reduxjs/toolkit";

import authReducer from "./slices/auth-slice";
import chatsReducer from "./slices/chats-slice";

export const store = configureStore({
  reducer: {
    auth: authReducer,
    chats: chatsReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;


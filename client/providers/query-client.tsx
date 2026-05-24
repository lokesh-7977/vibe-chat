"use client";

import { QueryClient, QueryClientProvider, type DefaultOptions } from "@tanstack/react-query";
import { Provider as ReduxProvider } from "react-redux";
import { store } from "@/store";
import { ToastProvider } from "./toast-provider";

const defaultQueryOptions: DefaultOptions = {
  queries: {
    staleTime: 30_000,
    gcTime: 5 * 60_000,
    retry: 1,
    refetchOnWindowFocus: false,
  },
  mutations: {
    retry: 0,
  },
};

let browserQueryClient: QueryClient | undefined;

function getQueryClient() {
  if (typeof window === "undefined") {
    return new QueryClient({ defaultOptions: defaultQueryOptions });
  }
  browserQueryClient ??= new QueryClient({ defaultOptions: defaultQueryOptions });
  return browserQueryClient;
}

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ReduxProvider store={store}>
      <QueryClientProvider client={getQueryClient()}>
        <ToastProvider>{children}</ToastProvider>
      </QueryClientProvider>
    </ReduxProvider>
  );
}

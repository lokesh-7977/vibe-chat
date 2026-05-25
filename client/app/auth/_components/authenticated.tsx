"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAppSelector } from "@/store/hooks";

export default function AuthAwareHome() {
  const { isAuthenticated } = useAppSelector((s) => s.auth);
  const router = useRouter();

  useEffect(() => {
    router.replace(isAuthenticated ? "/chats" : "/auth");
  }, [isAuthenticated, router]);

  return null;
}

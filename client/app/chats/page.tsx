import { RequireAuth } from "@/components/auth-guard";
import ChatsShell from "./_components/chats-shell";

export default function ChatsPage() {
  return (
    <RequireAuth>
      <ChatsShell />
    </RequireAuth>
  );
}


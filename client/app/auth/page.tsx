import { RedirectIfAuth } from "@/components/auth-guard";
import AuthPanel from "./_components/auth-panel";

export default function AuthPage() {
  return (
    <RedirectIfAuth>
      <AuthPanel />
    </RedirectIfAuth>
  );
}

import { useEffect, useState } from "react";

import { clearSession, getSession, saveSession } from "./auth/session";
import { LoginPage } from "./pages/LoginPage";
import { ProjectsPage } from "./pages/ProjectsPage";
import type { Session } from "./auth/session";

export default function App() {
  const [session, setSession] = useState<Session | null>(() => getSession());

  useEffect(() => {
    function handleSessionExpired() {
      setSession(null);
    }

    window.addEventListener("session-expired", handleSessionExpired);
    return () => window.removeEventListener("session-expired", handleSessionExpired);
  }, []);

  function handleAuthenticated(nextSession: Session) {
    saveSession(nextSession);
    setSession(nextSession);
  }

  function handleSignOut() {
    clearSession();
    setSession(null);
    window.location.hash = "#/login";
  }

  if (session === null) {
    return <LoginPage onAuthenticated={handleAuthenticated} />;
  }

  return <ProjectsPage session={session} onSignOut={handleSignOut} />;
}

import type { User } from "../types/auth";

const sessionKey = "abb-mlops-session";

export interface Session {
  accessToken: string;
  user: User;
}

export function getSession(): Session | null {
  const storedSession = localStorage.getItem(sessionKey);
  if (storedSession === null) {
    return null;
  }

  try {
    return JSON.parse(storedSession) as Session;
  } catch {
    clearSession();
    return null;
  }
}

export function saveSession(session: Session): void {
  localStorage.setItem(sessionKey, JSON.stringify(session));
}

export function clearSession(): void {
  localStorage.removeItem(sessionKey);
}

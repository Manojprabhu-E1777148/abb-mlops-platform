import { useState } from "react";
import type { FormEvent } from "react";

import { getCurrentUser, login } from "../api/auth";
import type { Session } from "../auth/session";

interface LoginPageProps {
  onAuthenticated: (session: Session) => void;
}

export function LoginPage({ onAuthenticated }: LoginPageProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const token = await login(email, password);
      const user = await getCurrentUser(token.access_token);
      onAuthenticated({ accessToken: token.access_token, user });
      window.location.hash = "#/projects";
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to sign in.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <p className="eyebrow">ABB MLOps Platform</p>
        <h1>Sign in</h1>
        <p>Use your existing backend account to manage projects.</p>
        {error !== null && <p className="alert alert-error">{error}</p>}
        <label>
          Email
          <input
            autoComplete="email"
            required
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <label>
          Password
          <input
            autoComplete="current-password"
            required
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        <button disabled={isSubmitting} type="submit">
          {isSubmitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </main>
  );
}

import { apiRequest } from "./client";
import type { TokenResponse, User } from "../types/auth";

export async function login(email: string, password: string): Promise<TokenResponse> {
  const formData = new URLSearchParams({ username: email, password });
  const response = await fetch(
    `${(import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "")}/api/auth/login`,
    {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json" },
      body: formData,
    },
  );

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const message =
      typeof body === "object" && body !== null && "detail" in body && typeof body.detail === "string"
        ? body.detail
        : "Unable to sign in.";
    throw new Error(message);
  }

  return (await response.json()) as TokenResponse;
}

export function getCurrentUser(accessToken?: string): Promise<User> {
  return apiRequest<User>("/api/auth/me", {
    headers: accessToken === undefined ? undefined : { Authorization: `Bearer ${accessToken}` },
  });
}

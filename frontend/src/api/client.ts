import { clearSession, getSession } from "../auth/session";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  authenticated?: boolean;
}

function getErrorMessage(body: unknown): string {
  if (typeof body !== "object" || body === null) {
    return "The request could not be completed.";
  }

  if ("error" in body && typeof body.error === "object" && body.error !== null) {
    const error = body.error as { message?: unknown };
    if (typeof error.message === "string") {
      return error.message;
    }
  }

  if ("detail" in body) {
    const detail = body.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (typeof item === "object" && item !== null && "msg" in item) {
            return String(item.msg);
          }
          return String(item);
        })
        .join(" ");
    }
  }

  return "The request could not be completed.";
}

export async function apiRequest<T>(
  path: string,
  { body, authenticated = true, headers, ...options }: RequestOptions = {},
): Promise<T> {
  const requestHeaders = new Headers(headers);
  requestHeaders.set("Accept", "application/json");

  if (body !== undefined) {
    requestHeaders.set("Content-Type", "application/json");
  }

  if (authenticated) {
    const session = getSession();
    if (session !== null) {
      requestHeaders.set("Authorization", `Bearer ${session.accessToken}`);
    }
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers: requestHeaders,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (response.status === 401) {
    clearSession();
    window.location.hash = "#/login";
    window.dispatchEvent(new Event("session-expired"));
  }

  if (!response.ok) {
    let responseBody: unknown = null;
    try {
      responseBody = await response.json();
    } catch {}
    throw new ApiError(response.status, getErrorMessage(responseBody));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

import { API_BASE_URL } from "./env";

interface RequestOptions extends RequestInit {
  parse?: boolean;
}

const withBaseUrl = (path: string) =>
  `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;

async function handleResponse<T>(response: Response, parse = true): Promise<T> {
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  if (!parse) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type");
  if (contentType?.includes("application/json")) {
    return (await response.json()) as T;
  }

  return (await response.text()) as unknown as T;
}

export async function apiGet<T>(path: string, init?: RequestOptions): Promise<T> {
  const response = await fetch(withBaseUrl(path), {
    method: "GET",
    cache: "no-store",
    ...init,
  });
  return handleResponse<T>(response, init?.parse ?? true);
}

export async function apiPost<T, B = unknown>(
  path: string,
  body?: B,
  init?: RequestOptions
): Promise<T> {
  const response = await fetch(withBaseUrl(path), {
    method: "POST",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    body: body ? JSON.stringify(body) : undefined,
    ...init,
  });
  return handleResponse<T>(response, init?.parse ?? true);
}

export async function apiPut<T, B = unknown>(
  path: string,
  body?: B,
  init?: RequestOptions
): Promise<T> {
  const response = await fetch(withBaseUrl(path), {
    method: "PUT",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    body: body ? JSON.stringify(body) : undefined,
    ...init,
  });
  return handleResponse<T>(response, init?.parse ?? true);
}

export async function apiPostQuery<T>(path: string, params: Record<string, string>): Promise<T> {
  const usp = new URLSearchParams(params);
  return apiPost<T>(`${path}?${usp.toString()}`);
}

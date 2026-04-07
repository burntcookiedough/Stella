const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL ?? "ws://127.0.0.1:8000";
const TOKEN_KEY = "stella-token";

export type LoginPayload = {
  username: string;
  password: string;
};

export type OverviewResponse = {
  available_users: string[];
  selected_user: string | null;
  latest: {
    day: string;
    steps: number | null;
    sleep_minutes: number | null;
    resting_hr: number | null;
    hrv: number | null;
    health_score: number | null;
  } | null;
  trend_slices: Array<Record<string, number | string | null>>;
  anomalies: Array<{
    day: string;
    low_sleep: boolean;
    low_activity: boolean;
    high_resting_hr: boolean;
  }>;
};

export type CorrelationsResponse = {
  selected_user: string | null;
  matrix: Record<string, Record<string, number>>;
  pairs: Array<{
    metric_a: string;
    metric_b: string;
    lag_days: number;
    correlation: number;
    sample_size: number;
  }>;
};

export type ReportDownload = {
  blob: Blob;
  fileName: string;
  llmStatus: "ok" | "fallback";
  llmError: string | null;
};

export function getToken(): string | null {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

function buildRequestHeaders(init?: RequestInit): Headers {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  if (!(init?.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return headers;
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: buildRequestHeaders(init),
  });
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await request(path, init);

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }
  return (await response.blob()) as T;
}

export async function login(payload: LoginPayload): Promise<void> {
  const response = await apiFetch<{ access_token: string }>("/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  setToken(response.access_token);
}

export function fetchOverview(sourceUserId?: string): Promise<OverviewResponse> {
  const query = sourceUserId ? `?source_user_id=${encodeURIComponent(sourceUserId)}` : "";
  return apiFetch<OverviewResponse>(`/v1/overview${query}`);
}

export function fetchCorrelations(sourceUserId?: string): Promise<CorrelationsResponse> {
  const query = sourceUserId ? `?source_user_id=${encodeURIComponent(sourceUserId)}` : "";
  return apiFetch<CorrelationsResponse>(`/v1/analytics/correlations${query}`);
}

export async function uploadImport(files: File[], source?: string): Promise<void> {
  const body = new FormData();
  files.forEach((file) => body.append("files", file));
  if (source) {
    body.append("source", source);
  }
  await apiFetch("/v1/imports", { method: "POST", body });
}

export async function downloadReport(sourceUserId?: string): Promise<ReportDownload> {
  const response = await request("/v1/reports/pdf", {
    method: "POST",
    body: JSON.stringify({ source_user_id: sourceUserId ?? null }),
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  const contentDisposition = response.headers.get("content-disposition") ?? "";
  const fileName = contentDisposition.match(/filename="?([^"]+)"?/)?.[1] ?? "stella-report.pdf";
  return {
    blob: await response.blob(),
    fileName,
    llmStatus: response.headers.get("x-stella-llm-status") === "fallback" ? "fallback" : "ok",
    llmError: response.headers.get("x-stella-llm-error"),
  };
}

export function buildChatSocket(sourceUserId?: string): WebSocket {
  const params = new URLSearchParams();
  const token = getToken();
  if (token) {
    params.set("token", token);
  }
  if (sourceUserId) {
    params.set("source_user_id", sourceUserId);
  }
  return new WebSocket(`${WS_BASE_URL}/v1/chat/ws?${params.toString()}`);
}

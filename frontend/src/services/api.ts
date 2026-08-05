import type {
  ApiErrorBody,
  DecisionRequest,
  DecisionResponse,
  HealthResponse,
  ReadyResponse,
} from "../types/api";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  body: ApiErrorBody;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message || body.error || `API request failed with status ${status}`);
    this.status = status;
    this.body = body;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers: {
      "content-type": "application/json",
      ...(options?.headers || {}),
    },
  });

  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : {};

  if (!response.ok) {
    throw new ApiError(response.status, body as ApiErrorBody);
  }

  return body as T;
}

export const travelGuardApi = {
  health: () => request<HealthResponse>("/health"),
  ready: () => request<ReadyResponse>("/ready"),
  decide: (payload: DecisionRequest) =>
    request<DecisionResponse>("/v1/decision", {
      method: "POST",
      body: JSON.stringify(payload),
      headers: {
        "x-request-id": crypto.randomUUID(),
      },
    }),
};

export function apiDocsUrl() {
  return `${apiBaseUrl}/docs`;
}

export function openApiUrl() {
  return `${apiBaseUrl}/openapi.json`;
}

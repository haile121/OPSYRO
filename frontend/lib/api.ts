export type Creator = { id: number; username: string; email: string; first_name: string; last_name: string };
export type TwitchConnection = { connected: boolean; profile: { id: string; login: string; display_name: string; profile_image_url: string } | null };
export type CreatorSession = { id: number; title: string; description: string; twitch_channel_id: string; status: "draft" | "live" | "ended"; public_token: string; created_at: string; started_at: string | null; ended_at: string | null };
export type CreatorResponse = { id: number; cluster_id: number; text: string; status: "draft" | "published"; feedback_count: number; helpful_count: number; created_at: string; updated_at: string; published_at: string | null };
export type QuestionCluster = { id: number; label: string; region_key: string; signal_count: number; example_questions: string[]; creator_response: CreatorResponse | null; created_at: string; updated_at: string };
export type AttentionMap = { grid_size: number; signal_count: number; cells: { x: number; y: number; count: number }[]; region_summary: { region_key: string; count: number }[] };
export type SessionSummary = { session_id: number; signal_count: number; question_groups: number; published_responses: number; feedback_count: number; helpful_feedback_count: number };
export type PublicResponse = { id: number; cluster_id: number; question: string; text: string; feedback_count: number; helpful_count: number; published_at: string };
export type Experiment = { id: number; name: string; hypothesis: string; change: string; outcome: string; status: "planned" | "active" | "complete"; session_ids: number[]; created_at: string; started_at: string | null; completed_at: string | null; updated_at: string };

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
function readCsrfCookie() { return document.cookie.split("; ").find((part) => part.startsWith("csrftoken="))?.split("=")[1] || ""; }
async function csrfToken() { await fetch(`${API_URL}/api/auth/csrf/`, { credentials: "include" }); return readCsrfCookie(); }
async function request<T>(path: string, options: RequestInit = {}, protect = true): Promise<T> {
  const method = options.method || "GET";
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  if (protect && method !== "GET") headers.set("X-CSRFToken", await csrfToken());
  const response = await fetch(`${API_URL}${path}`, { ...options, headers, credentials: protect ? "include" : "omit" });
  if (response.status === 204) return undefined as T;
  const body = await response.json().catch(() => ({}));
  if (!response.ok) { const detail = body.detail || Object.values(body).flat().join(" ") || "The request could not be completed."; throw new Error(String(detail)); }
  return body as T;
}
const json = (method: string, value?: unknown): RequestInit => ({ method, body: value === undefined ? undefined : JSON.stringify(value) });
export const api = {
  register: (data: { username: string; email: string; password: string }) => request<Creator>("/api/auth/register/", json("POST", data)),
  login: (data: { username: string; password: string }) => request<Creator>("/api/auth/login/", json("POST", data)),
  logout: () => request<void>("/api/auth/logout/", json("POST")),
  me: () => request<Creator>("/api/auth/me/"),
  twitchConnection: () => request<TwitchConnection>("/api/v1/auth/twitch/status/"),
  sessions: async () => (await request<{ results: CreatorSession[] }>("/api/sessions/")).results,
  session: (id: string) => request<CreatorSession>(`/api/sessions/${id}/`),
  questions: (id: string) => request<QuestionCluster[]>(`/api/sessions/${id}/questions/`),
  attention: (id: string) => request<AttentionMap>(`/api/sessions/${id}/attention/`),
  summary: (id: string) => request<SessionSummary>(`/api/sessions/${id}/summary/`),
  createSession: (data: { title: string; description: string; twitch_channel_id: string }) => request<CreatorSession>("/api/sessions/", json("POST", data)),
  startSession: (id: number) => request<CreatorSession>(`/api/sessions/${id}/start/`, json("POST")),
  endSession: (id: number) => request<CreatorSession>(`/api/sessions/${id}/end/`, json("POST")),
  createResponse: (cluster_id: number, text: string) => request<CreatorResponse>("/api/responses/", json("POST", { cluster_id, text })),
  updateResponse: (id: number, text: string) => request<CreatorResponse>(`/api/responses/${id}/`, json("PATCH", { text })),
  publishResponse: (id: number) => request<CreatorResponse>(`/api/responses/${id}/publish/`, json("POST")),
  submitSignal: (data: { session_token: string; participant_key: string; idempotency_key: string; region_x: string; region_y: string; region_key: string; intent: string; question: string }) => request<{ duplicate: boolean }>("/api/signals/", json("POST", data), false),
  publicResponses: (token: string) => request<{ title: string; status: string; responses: PublicResponse[] }>(`/api/feedback/public/sessions/${token}/responses/`, {}, false),
  submitFeedback: (data: { session_token: string; cluster_id: number; participant_key: string; idempotency_key: string; helpful: boolean }) => request<{ response_id: number; duplicate: boolean; feedback_count: number; helpful_count: number }>("/api/feedback/", json("POST", data), false),
  experiments: async () => (await request<{ results: Experiment[] }>("/api/experiments/")).results,
  createExperiment: (data: Pick<Experiment, "name" | "hypothesis" | "change" | "outcome" | "session_ids">) => request<Experiment>("/api/experiments/", json("POST", data)),
  updateExperiment: (id: number, data: Partial<Pick<Experiment, "hypothesis" | "change" | "outcome" | "session_ids">>) => request<Experiment>(`/api/experiments/${id}/`, json("PATCH", data)),
  startExperiment: (id: number) => request<Experiment>(`/api/experiments/${id}/start/`, json("POST")),
  completeExperiment: (id: number) => request<Experiment>(`/api/experiments/${id}/complete/`, json("POST")),
};


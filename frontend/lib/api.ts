const API_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export interface HealthStatus {
  status: string;
}

export interface Niche {
  id: number;
  slug: string;
  name: string;
  generator_key: string;
  made_for_kids_default: boolean;
  created_at: string;
}

export interface Channel {
  id: number;
  niche_id: number;
  display_name: string;
  youtube_channel_id: string | null;
  oauth_credentials_ref: string | null;
  status: "active" | "paused";
  created_at: string;
}

export interface VideoProject {
  id: number;
  channel_id: number;
  status: "idea" | "researching" | "rendering" | "review" | "scheduled" | "published" | "failed";
  title: string | null;
  description: string | null;
  hashtags: string | null;
  render_output_path: string | null;
  youtube_video_id: string | null;
  scheduled_at: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface OAuthStatus {
  channel_id: number;
  connected: boolean;
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}${path}`, { cache: "no-store", ...options });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export const getHealth = () => apiFetch<HealthStatus>("/health");
export const getNiches = () => apiFetch<Niche[]>("/niches");
export const getChannels = () => apiFetch<Channel[]>("/channels");
export const getChannel = (id: number) => apiFetch<Channel>(`/channels/${id}`);
export const getOAuthStatus = (channelId: number) => apiFetch<OAuthStatus>(`/channels/${channelId}/oauth/status`);
export const getChannelProjects = (channelId: number) => apiFetch<VideoProject[]>(`/channels/${channelId}/video-projects`);
export const getProject = (id: number) => apiFetch<VideoProject>(`/video-projects/${id}`);

export async function createChannel(data: { niche_id: number; display_name: string }): Promise<Channel | null> {
  return apiFetch<Channel>("/channels", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function createVideoProject(
  channelId: number,
  data: { topic: string; duration_seconds: number; seed: number }
): Promise<VideoProject | null> {
  return apiFetch<VideoProject>(`/channels/${channelId}/video-projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function enqueueRender(
  projectId: number,
  params: { topic: string; duration_seconds: number; seed: number }
): Promise<VideoProject | null> {
  const qs = new URLSearchParams({
    topic: params.topic,
    duration_seconds: String(params.duration_seconds),
    seed: String(params.seed),
  });
  return apiFetch<VideoProject>(`/video-projects/${projectId}/render-params?${qs}`, { method: "POST" });
}

export async function enqueuePublish(projectId: number): Promise<VideoProject | null> {
  return apiFetch<VideoProject>(`/video-projects/${projectId}/publish`, { method: "POST" });
}

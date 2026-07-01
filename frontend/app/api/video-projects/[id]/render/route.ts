import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const { topic, duration_seconds, seed, visual_style = "gradient" } = await req.json();
  const qs = new URLSearchParams({ topic, duration_seconds: String(duration_seconds), seed: String(seed), visual_style });
  const res = await fetch(`${API_URL}/video-projects/${id}/render-params?${qs}`, { method: "POST" });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

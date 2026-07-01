import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const res = await fetch(`${API_URL}/video-projects/${id}/publish`, { method: "POST" });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

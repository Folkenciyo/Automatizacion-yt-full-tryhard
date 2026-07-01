import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const res = await fetch(`${API_URL}/video-projects/${id}/thumbnail`, { cache: "no-store" });

  if (!res.ok) return NextResponse.json({ error: "not found" }, { status: 404 });

  return new NextResponse(res.body, {
    status: 200,
    headers: { "Content-Type": "image/png", "Cache-Control": "public, max-age=3600" },
  });
}

import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const range = req.headers.get("range");

  const headers: HeadersInit = {};
  if (range) headers["Range"] = range;

  const res = await fetch(`${API_URL}/video-projects/${id}/preview`, {
    headers,
    cache: "no-store",
  });

  const responseHeaders: Record<string, string> = {
    "Content-Type": res.headers.get("Content-Type") ?? "video/mp4",
    "Accept-Ranges": "bytes",
  };

  const contentLength = res.headers.get("Content-Length");
  if (contentLength) responseHeaders["Content-Length"] = contentLength;

  const contentRange = res.headers.get("Content-Range");
  if (contentRange) responseHeaders["Content-Range"] = contentRange;

  return new NextResponse(res.body, { status: res.status, headers: responseHeaders });
}

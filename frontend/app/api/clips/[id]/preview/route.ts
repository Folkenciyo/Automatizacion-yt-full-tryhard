import { NextRequest } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://backend:8000";

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const range = req.headers.get("range");
  const backendRes = await fetch(`${BACKEND}/clips/${id}/preview`, {
    headers: range ? { Range: range } : {},
  });

  const headers: HeadersInit = {
    "Content-Type": backendRes.headers.get("Content-Type") ?? "video/mp4",
    "Accept-Ranges": "bytes",
  };
  const contentLength = backendRes.headers.get("Content-Length");
  if (contentLength) headers["Content-Length"] = contentLength;
  const contentRange = backendRes.headers.get("Content-Range");
  if (contentRange) headers["Content-Range"] = contentRange;

  return new Response(backendRes.body, {
    status: backendRes.status,
    headers,
  });
}

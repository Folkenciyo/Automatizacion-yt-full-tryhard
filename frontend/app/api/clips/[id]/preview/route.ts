import { NextRequest } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://backend:8000";

export async function GET(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const backendRes = await fetch(`${BACKEND}/clips/${id}/preview`, {
    headers: { Range: req.headers.get("range") ?? "" },
  });
  return new Response(backendRes.body, {
    status: backendRes.status,
    headers: {
      "Content-Type": "video/mp4",
      "Accept-Ranges": "bytes",
    },
  });
}

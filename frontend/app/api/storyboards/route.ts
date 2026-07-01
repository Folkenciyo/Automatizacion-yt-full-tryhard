import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://backend:8000";

export async function GET(req: NextRequest) {
  const channelId = req.nextUrl.searchParams.get("channel_id");
  const url = channelId ? `${BACKEND}/storyboards?channel_id=${channelId}` : `${BACKEND}/storyboards`;
  const res = await fetch(url);
  return NextResponse.json(await res.json(), { status: res.status });
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const res = await fetch(`${BACKEND}/storyboards`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return NextResponse.json(await res.json(), { status: res.status });
}

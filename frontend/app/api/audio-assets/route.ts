import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://backend:8000";

export async function GET() {
  const res = await fetch(`${BACKEND}/audio-assets`);
  return NextResponse.json(await res.json(), { status: res.status });
}

export async function POST(req: NextRequest) {
  const body = await req.formData();
  const res = await fetch(`${BACKEND}/audio-assets`, {
    method: "POST",
    body,
  });
  return NextResponse.json(await res.json(), { status: res.status });
}

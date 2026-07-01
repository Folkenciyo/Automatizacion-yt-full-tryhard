import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://backend:8000";

export async function POST(
  _: NextRequest,
  { params }: { params: Promise<{ id: string; promptId: string }> }
) {
  const { id, promptId } = await params;
  const res = await fetch(`${BACKEND}/storyboards/${id}/prompts/${promptId}/generate`, {
    method: "POST",
  });
  return NextResponse.json(await res.json(), { status: res.status });
}

import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://backend:8000";

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string; promptId: string }> }
) {
  const { id, promptId } = await params;
  const body = await req.text();
  const res = await fetch(`${BACKEND}/storyboards/${id}/prompts/${promptId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body,
  });
  return NextResponse.json(await res.json(), { status: res.status });
}

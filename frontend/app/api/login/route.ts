import { NextRequest, NextResponse } from "next/server";

const SESSION_COOKIE = "yt_session";

export async function POST(request: NextRequest) {
  const { password } = await request.json();

  if (!password || password !== process.env.APP_LOGIN_PASSWORD) {
    return NextResponse.json({ error: "Contraseña incorrecta" }, { status: 401 });
  }

  const sessionToken = process.env.APP_SESSION_TOKEN;
  if (!sessionToken) {
    return NextResponse.json({ error: "APP_SESSION_TOKEN no configurado" }, { status: 500 });
  }

  const response = NextResponse.json({ status: "ok" });
  response.cookies.set(SESSION_COOKIE, sessionToken, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 30,
  });
  return response;
}

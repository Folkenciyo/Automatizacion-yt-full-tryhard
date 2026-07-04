import { NextRequest, NextResponse } from "next/server";

const SESSION_COOKIE = "yt_session";
const PUBLIC_PATHS = ["/login", "/api/login"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (PUBLIC_PATHS.some((path) => pathname.startsWith(path))) {
    return NextResponse.next();
  }

  const sessionToken = process.env.APP_SESSION_TOKEN;
  const cookie = request.cookies.get(SESSION_COOKIE)?.value;

  if (!sessionToken || cookie !== sessionToken) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("from", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};

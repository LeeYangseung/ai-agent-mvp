import { NextResponse } from "next/server";

export async function GET() {
  // 런타임에 컨테이너 환경변수에서 값을 읽는다.
  const envBase = process.env.NEXT_PUBLIC_API_BASE_URL;
  const apiBaseUrl = envBase && envBase.trim().length > 0 ? envBase : "";

  return NextResponse.json({ apiBaseUrl });
}



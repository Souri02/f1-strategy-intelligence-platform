import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const title = searchParams.get("title");
  if (!title) {
    return NextResponse.json({ detail: "Missing 'title' query param." }, { status: 400 });
  }

  const url = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`;
  const r = await fetch(url, {
    // Cache on Vercel/Next for quick repeat loads
    next: { revalidate: 60 * 60 * 24 * 7 } // 7 days
  });
  if (!r.ok) {
    return NextResponse.json({ detail: "Wikipedia lookup failed." }, { status: 502 });
  }

  const data = await r.json();
  const res = NextResponse.json(data, { status: 200 });
  res.headers.set("Cache-Control", "public, max-age=3600, s-maxage=604800, stale-while-revalidate=86400");
  return res;
}


import Image from "next/image";
import Link from "next/link";

type SeasonMeta = {
  season: number;
  teams: { constructor_name?: string | null; wikipedia_title?: string | null }[];
};

type WikiSummary = {
  title: string;
  extract?: string;
  thumbnail?: { source: string };
  content_urls?: { desktop?: { page?: string } };
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function getSeasonMeta(season: number): Promise<SeasonMeta> {
  const r = await fetch(`${API_BASE}/api/v1/meta/season/${season}`, { cache: "no-store" });
  if (!r.ok) throw new Error("Metadata unavailable for season.");
  return (await r.json()) as SeasonMeta;
}

async function getWiki(title: string): Promise<WikiSummary | null> {
  const r = await fetch(`${process.env.NEXT_PUBLIC_SITE_ORIGIN ?? ""}/api/wiki?title=${encodeURIComponent(title)}`, {
    cache: "force-cache"
  }).catch(() => null);
  if (!r || !r.ok) return null;
  return (await r.json()) as WikiSummary;
}

export default async function TeamPage({
  params,
  searchParams
}: {
  params: { name: string };
  searchParams?: { season?: string };
}) {
  const season = Number(searchParams?.season ?? "2024");
  const name = decodeURIComponent(params.name);
  let meta: SeasonMeta | null = null;
  try {
    meta = await getSeasonMeta(season);
  } catch {
    meta = null;
  }
  const team = meta?.teams.find((t) => (t.constructor_name ?? "").toLowerCase() === name.toLowerCase());
  const wiki = team?.wikipedia_title ? await getWiki(team.wikipedia_title) : null;

  return (
    <main className="container">
      <Link href="/" className="backLink">
        ← Back
      </Link>
      {!meta ? (
        <div className="card">
          <p className="error">
            Team details are unavailable right now because season metadata couldn’t be loaded. Please go back and run{" "}
            <strong>Prepare season</strong> for {season}, and ensure the backend URL is configured in Vercel.
          </p>
        </div>
      ) : null}
      <div className="detailHero">
        <div className="detailImg">
          {wiki?.thumbnail?.source ? (
            <Image
              src={wiki.thumbnail.source}
              alt={name}
              fill
              sizes="(max-width: 900px) 100vw, 700px"
              style={{ objectFit: "contain" }}
            />
          ) : (
            <div className="imgFallback" />
          )}
        </div>
        <div>
          <h1 className="detailTitle">{wiki?.title ?? name}</h1>
          <p className="detailSub">Season {season}</p>
          <p className="detailText">{wiki?.extract ?? "No description available."}</p>
          {wiki?.content_urls?.desktop?.page ? (
            <p>
              Source:{" "}
              <a href={wiki.content_urls.desktop.page} target="_blank" rel="noreferrer">
                Wikipedia
              </a>
            </p>
          ) : null}
        </div>
      </div>
    </main>
  );
}


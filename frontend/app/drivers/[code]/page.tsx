import Image from "next/image";
import Link from "next/link";

type SeasonMeta = {
  season: number;
  drivers: { code: string; full_name?: string | null; constructor?: string | null; wikipedia_title?: string | null }[];
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

export default async function DriverPage({
  params,
  searchParams
}: {
  params: { code: string };
  searchParams?: { season?: string };
}) {
  const season = Number(searchParams?.season ?? "2024");
  const code = params.code.toUpperCase();
  const meta = await getSeasonMeta(season);
  const driver = meta.drivers.find((d) => d.code.toUpperCase() === code);
  const wiki = driver?.wikipedia_title ? await getWiki(driver.wikipedia_title) : null;

  return (
    <main className="container">
      <Link href="/" className="backLink">
        ← Back
      </Link>
      <div className="detailHero">
        <div className="detailImg">
          {wiki?.thumbnail?.source ? (
            <Image
              src={wiki.thumbnail.source}
              alt={driver?.full_name ?? code}
              fill
              sizes="(max-width: 900px) 100vw, 700px"
              style={{ objectFit: "contain" }}
            />
          ) : (
            <div className="imgFallback" />
          )}
        </div>
        <div>
          <h1 className="detailTitle">{driver?.full_name ?? code}</h1>
          <p className="detailSub">
            {driver?.constructor ? <>Team: <strong>{driver.constructor}</strong></> : null} · Season {season}
          </p>
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


"use client";

import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";

type DriverMeta = {
  code: string;
  full_name?: string | null;
  constructor?: string | null;
  wikipedia_title?: string | null;
};

type TeamMeta = {
  constructor_id?: string | null;
  constructor_name?: string | null;
  wikipedia_title?: string | null;
};

type SeasonMeta = {
  season: number;
  drivers: DriverMeta[];
  teams: TeamMeta[];
};

type WikiSummary = {
  title: string;
  extract?: string;
  thumbnail?: { source: string };
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function fetchWikiSummary(title: string): Promise<WikiSummary | null> {
  try {
    const url = `/api/wiki?title=${encodeURIComponent(title)}`;
    const r = await fetch(url, { cache: "force-cache" });
    if (!r.ok) return null;
    return (await r.json()) as WikiSummary;
  } catch {
    return null;
  }
}

export default function MediaExplorer({ season }: { season: number }) {
  const [tab, setTab] = useState<"drivers" | "teams">("drivers");
  const [query, setQuery] = useState("");
  const [meta, setMeta] = useState<SeasonMeta | null>(null);
  const [loading, setLoading] = useState(false);
  const [cards, setCards] = useState<Record<string, WikiSummary | null>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const r = await fetch(`${API_BASE}/api/v1/meta/season/${season}`, { cache: "no-store" });
        if (!r.ok) throw new Error("Metadata unavailable. Prepare this season first.");
        const body = (await r.json()) as SeasonMeta;
        if (!cancelled) {
          setMeta(body);
          setCards({});
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load metadata.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [season]);

  const driverList = useMemo(() => {
    const list = meta?.drivers ?? [];
    const q = query.trim().toLowerCase();
    if (!q) return list;
    return list.filter((d) => {
      const name = (d.full_name ?? "").toLowerCase();
      return d.code.toLowerCase().includes(q) || name.includes(q) || (d.constructor ?? "").toLowerCase().includes(q);
    });
  }, [meta, query]);

  const teamList = useMemo(() => {
    const list = meta?.teams ?? [];
    const q = query.trim().toLowerCase();
    if (!q) return list;
    return list.filter((t) => (t.constructor_name ?? "").toLowerCase().includes(q));
  }, [meta, query]);

  useEffect(() => {
    // prefetch top visible cards
    const items =
      tab === "drivers"
        ? driverList.slice(0, 12).map((d) => ({ key: `d:${d.code}`, title: d.wikipedia_title }))
        : teamList.slice(0, 12).map((t) => ({ key: `t:${t.constructor_name ?? ""}`, title: t.wikipedia_title }));

    (async () => {
      for (const item of items) {
        if (!item.title) continue;
        if (cards[item.key] !== undefined) continue;
        const summary = await fetchWikiSummary(item.title);
        setCards((prev) => ({ ...prev, [item.key]: summary }));
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, driverList, teamList]);

  return (
    <section className="neo">
      <div className="neoHeader">
        <div>
          <h2 className="neoTitle">F1 Visual Explorer</h2>
          <p className="neoSub">
            Search drivers and teams. Images are fetched from Wikipedia thumbnails (license-friendly).
          </p>
        </div>
        <div className="neoTabs">
          <button className={tab === "drivers" ? "tab active" : "tab"} onClick={() => setTab("drivers")}>
            Drivers
          </button>
          <button className={tab === "teams" ? "tab active" : "tab"} onClick={() => setTab("teams")}>
            Teams
          </button>
        </div>
      </div>

      <div className="neoControls">
        <input
          placeholder={tab === "drivers" ? "Search: VER, Hamilton, Red Bull..." : "Search: Ferrari, McLaren..."}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      {loading ? <p>Loading metadata…</p> : null}
      {error ? <p className="error">Error: {error}</p> : null}

      <div className="cardGrid">
        {tab === "drivers"
          ? driverList.map((d) => {
              const key = `d:${d.code}`;
              const summary = cards[key];
              const img = summary?.thumbnail?.source;
              return (
                <motion.div
                  key={key}
                  className="mediaCard"
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25 }}
                >
                  <Link className="cardLink" href={`/drivers/${encodeURIComponent(d.code)}?season=${season}`}>
                    <div className="mediaImg">
                      {img ? (
                        <Image
                          src={img}
                          alt={d.full_name ?? d.code}
                          fill
                          sizes="(max-width: 900px) 100vw, 33vw"
                          style={{ objectFit: "contain" }}
                          priority={false}
                        />
                      ) : (
                        <div className="imgFallback" />
                      )}
                    </div>
                    <div className="mediaBody">
                      <div className="mediaTop">
                        <span className="pill">{d.code}</span>
                        {d.constructor ? <span className="pill ghost">{d.constructor}</span> : null}
                      </div>
                      <h3 className="mediaTitle">{d.full_name ?? d.code}</h3>
                      <p className="mediaText">{summary?.extract ?? "No summary available yet."}</p>
                    </div>
                  </Link>
                </motion.div>
              );
            })
          : teamList.map((t) => {
              const name = t.constructor_name ?? "Team";
              const key = `t:${name}`;
              const summary = cards[key];
              const img = summary?.thumbnail?.source;
              return (
                <motion.div
                  key={key}
                  className="mediaCard"
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25 }}
                >
                  <Link className="cardLink" href={`/teams/${encodeURIComponent(name)}?season=${season}`}>
                    <div className="mediaImg">
                      {img ? (
                        <Image
                          src={img}
                          alt={name}
                          fill
                          sizes="(max-width: 900px) 100vw, 33vw"
                          style={{ objectFit: "contain" }}
                        />
                      ) : (
                        <div className="imgFallback" />
                      )}
                    </div>
                    <div className="mediaBody">
                      <div className="mediaTop">
                        <span className="pill">{name}</span>
                      </div>
                      <h3 className="mediaTitle">{summary?.title ?? name}</h3>
                      <p className="mediaText">{summary?.extract ?? "No summary available yet."}</p>
                    </div>
                  </Link>
                </motion.div>
              );
            })}
      </div>
    </section>
  );
}


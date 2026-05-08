import StrategySimulator from "./StrategySimulator";
import MediaExplorer from "./MediaExplorer";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function checkApiHealth() {
  try {
    const response = await fetch(`${API_BASE}/api/v1/health`, { cache: "no-store" });
    return response.ok;
  } catch {
    return false;
  }
}

export default async function HomePage() {
  const backendHealthy = await checkApiHealth();

  return (
    <main className="shell">
      <div className="bgGlow" />
      <header className="hero">
        <div className="heroInner">
          <div>
            <p className="kicker">AI Race Engineering · Counterfactual Strategy · Optimization</p>
            <h1 className="heroTitle">F1 Strategy Intelligence Platform</h1>
            <p className="heroText">
              A futuristic, full‑stack F1 analytics site: ingest seasons, train GPU models, run what‑if simulations,
              and optimize multi‑stop strategies.
            </p>
            <div className="statusRow">
              <span className={backendHealthy ? "status ok" : "status bad"}>
                API {backendHealthy ? "Connected" : "Not reachable"}
              </span>
              <span className="status note">Tip: prepare seasons 2022–2025 via API once, then explore instantly.</span>
            </div>
          </div>
          <div className="heroPanel">
            <div className="panelTitle">Quick start</div>
            <ol className="panelList">
              <li>Open API docs at <code>http://localhost:8000/docs</code></li>
              <li>Call <code>POST /api/v1/season/prepare</code> for 2022–2025</li>
              <li>Use the explorer + simulator below</li>
            </ol>
          </div>
        </div>
      </header>

      <div className="container">
        <MediaExplorer season={2024} />
        <StrategySimulator />
      </div>
    </main>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";

type SimulationResponse = {
  season: number;
  round: number;
  driver: string;
  baseline_pit_lap: number;
  counterfactual_pit_lap: number;
  baseline_estimated_time_seconds: number;
  counterfactual_estimated_time_seconds: number;
  delta_seconds: number;
  delta_confidence_low_seconds: number;
  delta_confidence_high_seconds: number;
  pit_stop_loss_seconds: number;
  estimated_position_gain: number;
  recommended_pit_lap: number;
  feasible_pit_window_start: number;
  feasible_pit_window_end: number;
  constraints_applied: string[];
  message: string;
};

type OptimizationCandidate = {
  strategy_label: string;
  pit_laps: number[];
  compounds: string[];
  estimated_time_seconds: number;
  uncertainty_seconds: number;
  position_gain_vs_baseline: number;
};

type OptimizationResponse = {
  season: number;
  round: number;
  driver: string;
  baseline_estimated_time_seconds: number;
  best_strategy: OptimizationCandidate;
  top_candidates: OptimizationCandidate[];
  explainability: Record<string, number>;
  message: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function getErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail ?? fallback;
  } catch {
    return fallback;
  }
}

export default function StrategySimulator() {
  const [season, setSeason] = useState(2024);
  const [round, setRound] = useState(1);
  const [driver, setDriver] = useState("VER");
  const [baselinePitLap, setBaselinePitLap] = useState(20);
  const [counterPitLap, setCounterPitLap] = useState(24);
  const [compound, setCompound] = useState("MEDIUM");
  const [loading, setLoading] = useState(false);
  const [optLoading, setOptLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [optResult, setOptResult] = useState<OptimizationResponse | null>(null);
  const [availableSeasons, setAvailableSeasons] = useState<number[]>([]);
  const [prepLoading, setPrepLoading] = useState(false);
  const [prepMsg, setPrepMsg] = useState<string | null>(null);

  const seasonOptions = useMemo(() => {
    if (availableSeasons.length > 0) return availableSeasons;
    return [2022, 2023, 2024, 2025];
  }, [availableSeasons]);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(`${API_BASE}/api/v1/data/available-seasons`, { cache: "no-store" });
        if (!r.ok) return;
        const body = (await r.json()) as { features?: number[]; models?: number[]; raw_laps?: number[] };
        const union = new Set<number>([...(body.features ?? []), ...(body.models ?? []), ...(body.raw_laps ?? [])]);
        const list = Array.from(union).sort((a, b) => b - a);
        if (list.length > 0) {
          setAvailableSeasons(list);
          setSeason((prev) => (union.has(prev) ? prev : list[0]));
        }
      } catch {
        // ignore; keep defaults
      }
    })();
  }, [API_BASE]);

  async function onSimulate() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetch(`${API_BASE}/api/v1/strategy/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          season,
          round,
          driver,
          baseline_pit_lap: baselinePitLap,
          counterfactual_pit_lap: counterPitLap,
          counterfactual_compound: compound
        })
      });
      if (!response.ok) {
        throw new Error(await getErrorMessage(response, "Simulation failed."));
      }
      setResult((await response.json()) as SimulationResponse);
    } catch (err) {
      if (err instanceof TypeError) {
        setError("Cannot reach backend API. Confirm backend is running at http://localhost:8000.");
      } else {
        setError(err instanceof Error ? err.message : "Simulation failed.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function onPrepareSeason() {
    setPrepLoading(true);
    setPrepMsg(null);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/v1/season/prepare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ season, use_gpu: true })
      });
      if (!response.ok) throw new Error(await getErrorMessage(response, "Prepare season failed."));
      const body = (await response.json()) as { message?: string };
      setPrepMsg(body.message ?? `Prepared season ${season}.`);
    } catch (err) {
      if (err instanceof TypeError) {
        setError("Cannot reach backend API. Confirm backend is running at http://localhost:8000.");
      } else {
        setError(err instanceof Error ? err.message : "Prepare season failed.");
      }
    } finally {
      setPrepLoading(false);
    }
  }

  async function onOptimize() {
    setOptLoading(true);
    setError(null);
    setOptResult(null);
    try {
      const response = await fetch(`${API_BASE}/api/v1/strategy/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          season,
          round,
          driver,
          baseline_pit_lap: baselinePitLap,
          monte_carlo_samples: 200
        })
      });
      if (!response.ok) {
        throw new Error(await getErrorMessage(response, "Optimization failed."));
      }
      setOptResult((await response.json()) as OptimizationResponse);
    } catch (err) {
      if (err instanceof TypeError) {
        setError("Cannot reach backend API. Confirm backend is running at http://localhost:8000.");
      } else {
        setError(err instanceof Error ? err.message : "Optimization failed.");
      }
    } finally {
      setOptLoading(false);
    }
  }

  return (
    <section className="card">
      <h2>Phase 3: What-If Strategy Simulator</h2>
      <p>Compare baseline vs counterfactual pit-stop lap for a driver race scenario.</p>
      <div className="grid">
        <label>
          Season
          <select value={season} onChange={(e) => setSeason(Number(e.target.value))}>
            {seasonOptions.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </label>
        <label>
          Round
          <input type="number" value={round} onChange={(e) => setRound(Number(e.target.value))} />
        </label>
        <label>
          Driver
          <input value={driver} maxLength={3} onChange={(e) => setDriver(e.target.value.toUpperCase())} />
        </label>
        <label>
          Baseline pit lap
          <input
            type="number"
            value={baselinePitLap}
            onChange={(e) => setBaselinePitLap(Number(e.target.value))}
          />
        </label>
        <label>
          Counterfactual pit lap
          <input type="number" value={counterPitLap} onChange={(e) => setCounterPitLap(Number(e.target.value))} />
        </label>
        <label>
          Counterfactual compound
          <select value={compound} onChange={(e) => setCompound(e.target.value)}>
            <option value="SOFT">SOFT</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HARD">HARD</option>
          </select>
        </label>
      </div>
      <button className="button" onClick={onSimulate} disabled={loading}>
        {loading ? "Running simulation..." : "Run Counterfactual Simulation"}
      </button>
      <button className="button secondary" onClick={onOptimize} disabled={optLoading}>
        {optLoading ? "Optimizing..." : "Optimize Multi-Stop Strategy"}
      </button>
      <button className="button ghost" onClick={onPrepareSeason} disabled={prepLoading}>
        {prepLoading ? `Preparing ${season}...` : `Prepare season ${season}`}
      </button>

      {prepMsg ? <p className="ok">{prepMsg}</p> : null}
      {error ? <p className="error">Error: {error}</p> : null}
      {result ? (
        <div className="result">
          <p>Baseline time: {result.baseline_estimated_time_seconds.toFixed(2)}s</p>
          <p>Counterfactual time: {result.counterfactual_estimated_time_seconds.toFixed(2)}s</p>
          <p>
            Delta (counterfactual - baseline): <strong>{result.delta_seconds.toFixed(2)}s</strong>
          </p>
          <p>
            95% uncertainty range: [{result.delta_confidence_low_seconds.toFixed(2)}s,{" "}
            {result.delta_confidence_high_seconds.toFixed(2)}s]
          </p>
          <p>Pit stop loss assumption: {result.pit_stop_loss_seconds.toFixed(2)}s</p>
          <p>Estimated position gain: {result.estimated_position_gain}</p>
          <p>Recommended pit lap: {result.recommended_pit_lap}</p>
          <p>
            Feasible pit window: {result.feasible_pit_window_start} - {result.feasible_pit_window_end}
          </p>
          {result.constraints_applied.length > 0 ? (
            <p>Applied constraints: {result.constraints_applied.join("; ")}</p>
          ) : (
            <p>Applied constraints: none</p>
          )}
        </div>
      ) : null}

      {optResult ? (
        <div className="result">
          <h3>Optimization Result</h3>
          <p>Baseline estimate: {optResult.baseline_estimated_time_seconds.toFixed(2)}s</p>
          <p>
            Best strategy: {optResult.best_strategy.strategy_label} | pits at{" "}
            {optResult.best_strategy.pit_laps.join(", ")} | compounds{" "}
            {optResult.best_strategy.compounds.join(" -> ")}
          </p>
          <p>
            Estimated time: {optResult.best_strategy.estimated_time_seconds.toFixed(2)}s (+/-
            {optResult.best_strategy.uncertainty_seconds.toFixed(2)}s)
          </p>
          <p>Position gain vs baseline: {optResult.best_strategy.position_gain_vs_baseline}</p>
          <p>
            Explainability:{" "}
            {Object.entries(optResult.explainability)
              .map(([k, v]) => `${k}=${v.toFixed(2)}s`)
              .join(" | ")}
          </p>
        </div>
      ) : null}
    </section>
  );
}

// Typed client for the FastAPI router (api/router.py). The types are generated from the API's own
// OpenAPI schema (npm run gen:types), so they cannot drift from the backend.
import type { components } from "./api-types";

type S = components["schemas"];
export type StatusResponse = S["StatusResponse"];
export type ComponentStatus = S["ComponentStatus"];
export type ModuleStatus = S["ModuleStatus"];
export type StageInfo = S["StageInfo"];
export type DDIStatsResponse = S["DDIStatsResponse"];
export type DDIExamplesResponse = S["DDIExamplesResponse"];
export type DDIExample = S["DDIExample"];
export type DailyMedStatsResponse = S["DailyMedStatsResponse"];
export type TacStatsResponse = S["TacStatsResponse"];
export type TraceResponse = S["TraceResponse"];
export type TraceRow = S["TraceRow"];
export type Readiness = { status: "ready" | "not_ready"; reason?: string | null; fix?: string | null };

const BASE: string = import.meta.env.VITE_API_BASE ?? "";

export class ApiError extends Error {}

async function get<T>(path: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`);
  } catch {
    throw new ApiError(
      "Cannot reach the API. Start it from the aakaash folder with: " +
        ".venv\\Scripts\\python.exe -m uvicorn api.app:app --port 8000",
    );
  }
  if (!res.ok) throw new ApiError(`API returned ${res.status} for ${path}`);
  return (await res.json()) as T;
}

export const api = {
  status: () => get<StatusResponse>("/api/status"),
  ddiStats: () => get<DDIStatsResponse>("/api/datasets/ddi2013/stats"),
  ddiExamples: (p: { split?: string; label?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (p.split) q.set("split", p.split);
    if (p.label) q.set("label", p.label);
    q.set("limit", String(p.limit ?? 6));
    return get<DDIExamplesResponse>(`/api/datasets/ddi2013/examples?${q}`);
  },
  dailymedStats: () => get<DailyMedStatsResponse>("/api/datasets/dailymed/stats"),
  tacStats: () => get<TacStatsResponse>("/api/datasets/tac2017/stats"),
  trace: () => get<TraceResponse>("/api/trace"),
};

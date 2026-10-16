import { createContext, useContext, type ReactNode } from "react";
import { api, type StatusResponse } from "./api";
import { useApi, type Query } from "./useApi";

const Ctx = createContext<Query<StatusResponse> | null>(null);

/** One /api/status fetch shared by the sidebar, the dashboard and the pages that need it. */
export function StatusProvider({ children }: { children: ReactNode }) {
  const q = useApi(api.status);
  return <Ctx.Provider value={q}>{children}</Ctx.Provider>;
}

export function useStatus(): Query<StatusResponse> {
  const q = useContext(Ctx);
  if (!q) throw new Error("useStatus must be used inside StatusProvider");
  return q;
}

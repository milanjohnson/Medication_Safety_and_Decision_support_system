import { useCallback, useEffect, useState } from "react";

export type Query<T> = {
  state: "loading" | "error" | "ok";
  data?: T;
  message?: string;
  reload: () => void;
};

/** Run `load` on mount and whenever `deps` change. Always one of: loading, error, ok. */
export function useApi<T>(load: () => Promise<T>, deps: unknown[] = []): Query<T> {
  const [res, setRes] = useState<{ state: Query<T>["state"]; data?: T; message?: string }>({
    state: "loading",
  });
  const [tick, setTick] = useState(0);
  const reload = useCallback(() => setTick((n) => n + 1), []);

  useEffect(() => {
    let alive = true;
    setRes((r) => ({ state: "loading", data: r.data }));
    load()
      .then((data) => alive && setRes({ state: "ok", data }))
      .catch((e: unknown) =>
        alive && setRes({ state: "error", message: e instanceof Error ? e.message : String(e) }),
      );
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  return { ...res, reload };
}

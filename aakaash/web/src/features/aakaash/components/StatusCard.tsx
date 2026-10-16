import type { ComponentStatus } from "../api";
import { StatusBadge } from "./Panel";

const bytes = (n: number) => `${(n / 1e9).toFixed(2)} GB`;

function detailText(k: string, v: string | number): string {
  if (k === "total_bytes" && typeof v === "number") return bytes(v);
  return typeof v === "number" ? v.toLocaleString("en-US") : v;
}

/** One system component, exactly as /api/status reports it. */
export function StatusCard({ c }: { c: ComponentStatus }) {
  const detail = Object.entries(c.detail ?? {});
  return (
    <article className={`card status-card ${c.status === "ready" ? "is-ready" : "is-not-ready"}`}>
      <header>
        <h3>{c.label}</h3>
        <StatusBadge status={c.status} />
      </header>
      {c.reason && <p className="small">{c.reason}</p>}
      {c.fix && (
        <p className="small muted">
          <strong>To fix:</strong> {c.fix}
        </p>
      )}
      {detail.length > 0 && (
        <dl className="kv kv-compact">
          {detail.map(([k, v]) => (
            <div key={k}>
              <dt>{k.replace(/_/g, " ")}</dt>
              <dd>{detailText(k, v)}</dd>
            </div>
          ))}
        </dl>
      )}
    </article>
  );
}

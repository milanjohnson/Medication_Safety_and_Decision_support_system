import type { ReactNode } from "react";
import type { Readiness } from "../api";
import type { Query } from "../useApi";

export function NotReadyBox({ reason, fix, title }: { reason?: string | null; fix?: string | null; title?: string }) {
  return (
    <div className="notice notice-warn" role="status">
      <div className="notice-title">
        <span aria-hidden="true">⚠</span> {title ?? "Not ready"}
      </div>
      {reason && <p>{reason}</p>}
      {fix && (
        <p className="muted">
          <strong>To fix:</strong> {fix}
        </p>
      )}
    </div>
  );
}

export function LoadingBox({ what }: { what: string }) {
  return (
    <div className="notice" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" /> Loading {what}…
    </div>
  );
}

export function ErrorBox({ message, onRetry }: { message?: string; onRetry?: () => void }) {
  return (
    <div className="notice notice-error" role="alert">
      <div className="notice-title">
        <span aria-hidden="true">✕</span> Could not load
      </div>
      <p>{message}</p>
      {onRetry && (
        <button type="button" className="btn" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

/** A titled section whose body handles loading, error and not_ready before showing real data. */
export function Panel<T extends Readiness>({
  title,
  hint,
  query,
  children,
  id,
}: {
  title: string;
  hint?: ReactNode;
  query: Query<T>;
  children: (data: T) => ReactNode;
  id?: string;
}) {
  let body: ReactNode;
  if (query.state === "loading" && !query.data) body = <LoadingBox what={title.toLowerCase()} />;
  else if (query.state === "error") body = <ErrorBox message={query.message} onRetry={query.reload} />;
  else if (query.data && query.data.status === "not_ready")
    body = <NotReadyBox reason={query.data.reason} fix={query.data.fix} />;
  else if (query.data) body = children(query.data);
  return (
    <section className="panel" aria-labelledby={id ? `${id}-h` : undefined} id={id}>
      <h2 id={id ? `${id}-h` : undefined}>{title}</h2>
      {hint && <p className="muted panel-hint">{hint}</p>}
      {body}
    </section>
  );
}

export function StatusBadge({ status }: { status: "ready" | "not_ready" | "coming_soon" }) {
  const map = {
    ready: { icon: "✓", text: "Ready", cls: "badge-ok" },
    not_ready: { icon: "⚠", text: "Not ready", cls: "badge-warn" },
    coming_soon: { icon: "◷", text: "Coming soon", cls: "badge-soon" },
  }[status];
  return (
    <span className={`badge ${map.cls}`}>
      <span aria-hidden="true">{map.icon}</span> {map.text}
    </span>
  );
}

export function KeyValues({ items }: { items: [string, ReactNode][] }) {
  return (
    <dl className="kv">
      {items.map(([k, v]) => (
        <div key={k}>
          <dt>{k}</dt>
          <dd>{v}</dd>
        </div>
      ))}
    </dl>
  );
}

export const fmt = (n: number | null | undefined) => (n == null ? "–" : n.toLocaleString("en-US"));

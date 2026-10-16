import { useParams } from "react-router-dom";
import { ErrorBox, LoadingBox, StatusBadge } from "../components/Panel";
import { useStatus } from "../StatusContext";

/** Name, stage, "Coming soon", owner. Nothing else: no sample data, no mock output. */
export function ComingSoon({ id: idProp }: { id?: string }) {
  const params = useParams();
  const id = idProp ?? params.id;
  const q = useStatus();
  if (q.state === "loading" && !q.data) return <LoadingBox what="module" />;
  if (q.state === "error") return <ErrorBox message={q.message} onRetry={q.reload} />;
  const m = q.data?.modules.find((x) => x.id === id);
  if (!m)
    return (
      <>
        <h1>Unknown module</h1>
        <p>The API does not list a module with id “{id}”.</p>
      </>
    );
  return (
    <>
      <h1>{m.label}</h1>
      <section className="panel coming-soon">
        <p>
          <StatusBadge status="coming_soon" />
        </p>
        <dl className="kv">
          <div>
            <dt>{m.stages.length > 1 ? "Architecture stages" : "Architecture stage"}</dt>
            <dd>
              {m.stages.map((n, i) => (
                <span key={n}>
                  {i > 0 && " · "}Stage {n}: {m.stage_names[i]}
                </span>
              ))}
            </dd>
          </div>
          <div>
            <dt>Owner</dt>
            <dd>{m.owner}</dd>
          </div>
        </dl>
      </section>
    </>
  );
}

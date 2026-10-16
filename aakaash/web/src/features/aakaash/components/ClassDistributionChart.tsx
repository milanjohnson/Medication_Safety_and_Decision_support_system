import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DDIStatsResponse } from "../api";

const SERIES = [
  { key: "train", color: "var(--series-1)" },
  { key: "dev", color: "var(--series-2)" },
  { key: "test", color: "var(--series-3)" },
] as const;

const compact = (v: number) => (v >= 1000 ? `${v / 1000}K` : String(v));

type Row = { label: string } & Record<"train" | "dev" | "test", number>;

function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: { dataKey: string; value: number }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <strong>{label}</strong>
      {SERIES.map((s) => (
        <div key={s.key}>
          <span className="swatch" style={{ background: s.color }} aria-hidden="true" /> {s.key}:{" "}
          {payload.find((p) => p.dataKey === s.key)?.value.toLocaleString("en-US")}
        </div>
      ))}
    </div>
  );
}

/** Instances per class, one bar per split, on a LOG axis so `int` is visible beside `false`. */
export function ClassDistributionChart({ stats }: { stats: DDIStatsResponse }) {
  const rows: Row[] = stats.labels.map((label) => {
    const row = { label } as Row;
    for (const s of stats.splits) row[s.split] = s.class_counts[label] ?? 0;
    return row;
  });
  const max = Math.max(...rows.flatMap((r) => [r.train, r.dev, r.test]), 10);
  const top = 10 ** Math.ceil(Math.log10(max + 1));
  const ticks: number[] = [];
  for (let t = 1; t <= top; t *= 10) ticks.push(t);

  return (
    <figure className="chart" aria-label="DDI instances per class and split on a logarithmic axis">
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={rows} margin={{ top: 8, right: 12, left: 4, bottom: 4 }} barGap={2} barCategoryGap="22%">
          <CartesianGrid vertical={false} stroke="var(--grid)" strokeWidth={1} />
          <XAxis dataKey="label" tickLine={false} axisLine={{ stroke: "var(--grid)" }} tick={{ fill: "var(--text-muted)", fontSize: 13 }} />
          <YAxis
            scale="log"
            domain={[1, top]}
            ticks={ticks}
            allowDataOverflow
            tickFormatter={compact}
            tickLine={false}
            axisLine={false}
            width={48}
            tick={{ fill: "var(--text-muted)", fontSize: 12 }}
            label={{ value: "Instances (log scale)", angle: -90, position: "insideLeft", fill: "var(--text-muted)", fontSize: 12, dx: -2, dy: 56 }}
          />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: "var(--hover)" }} />
          <Legend iconType="square" formatter={(v: string) => <span className="legend-text">{v}</span>} />
          {SERIES.map((s) => (
            <Bar key={s.key} dataKey={s.key} fill={s.color} maxBarSize={22} radius={[4, 4, 0, 0]} isAnimationActive={false} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </figure>
  );
}

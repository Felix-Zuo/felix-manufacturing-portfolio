import { MoveDownRight, MoveUpRight } from "lucide-react";

import type { Metric } from "@/data/types";
import { CountUp } from "./CountUp";

const toneAccent: Record<Metric["tone"], string> = {
  blue: "text-sky-300",
  steel: "text-sky-300",
  green: "text-emerald-300",
  amber: "text-amber-300",
};

const toneBar: Record<Metric["tone"], string> = {
  blue: "bg-sky-400/70",
  steel: "bg-sky-400/70",
  green: "bg-emerald-400/70",
  amber: "bg-amber-400/70",
};

export function MetricCard({ metric }: { metric: Metric }) {
  const improvementDown = Boolean(metric.before);
  const Arrow = improvementDown ? MoveDownRight : MoveUpRight;

  return (
    <article className="surface-card group relative overflow-hidden rounded-xl p-6 transition-colors hover:border-slate-500/40">
      <span className={`absolute inset-x-0 top-0 h-0.5 ${toneBar[metric.tone]}`} aria-hidden="true" />
      <p className="mono-label text-slate-500">{metric.label}</p>
      <div className="mt-5 flex items-end justify-between gap-3">
        <div>
          {metric.before && (
            <p className="font-mono text-sm text-slate-500">
              <span className="line-through decoration-slate-600">{metric.before}</span>
              <span className="ml-2 text-slate-600">before</span>
            </p>
          )}
          <p className={`mt-1 font-mono text-3xl font-semibold tabular-nums tracking-tight ${toneAccent[metric.tone]}`}>
            {metric.count ? <CountUp count={metric.count} fallback={metric.value} /> : metric.value}
          </p>
        </div>
        <Arrow className={`mb-1 h-5 w-5 flex-none ${toneAccent[metric.tone]}`} aria-hidden="true" />
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-400">{metric.detail}</p>
      <p className="mono-label mt-5 text-slate-600">{metric.source}</p>
    </article>
  );
}

import type { Metric } from "@/data/types";

const toneClass: Record<Metric["tone"], string> = {
  blue: "border-blue-300 bg-blue-50 text-blue-950",
  amber: "border-amber-300 bg-amber-50 text-amber-950",
  green: "border-emerald-300 bg-emerald-50 text-emerald-950",
  steel: "border-slate-300 bg-slate-100 text-slate-950",
};

export function MetricCard({ metric }: { metric: Metric }) {
  return (
    <article className={`rounded-lg border p-5 shadow-sm ${toneClass[metric.tone]}`}>
      <p className="text-sm font-medium text-slate-700">{metric.label}</p>
      <strong className="mt-3 block text-2xl font-semibold text-slate-950">{metric.value}</strong>
      <p className="mt-3 text-sm leading-6 text-slate-700">{metric.detail}</p>
      <p className="mt-4 text-xs font-semibold uppercase tracking-wider text-slate-600">{metric.source}</p>
    </article>
  );
}


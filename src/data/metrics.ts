import type { Metric } from "./types";

export const metrics: Metric[] = [
  {
    id: "notice-time",
    label: "Production notice preparation",
    before: "20-40 min",
    value: "<1 min",
    count: { from: 40, to: 1, template: "{n} min", final: "<1 min" },
    detail: "From around 20-40 minutes of cross-system checking to under 1 minute with reviewable output.",
    source: "Production notice workflow",
    tone: "blue",
  },
  {
    id: "takt-cycle",
    label: "Trial takt analysis and adjustment cycle",
    before: "3 days",
    value: "1 day",
    count: { from: 3, to: 1, template: "{n} day", final: "1 day" },
    detail: "Full-line takt modeling shortened the adjustment loop before ramp-up.",
    source: "Trial production takt simulation",
    tone: "steel",
  },
  {
    id: "scrap-reduction",
    label: "Trial machining/debugging scrap",
    value: "~90% less",
    count: { from: 0, to: 90, template: "~{n}% less", final: "~90% less" },
    detail: "Data-supported adjustment reduced repeated trial-and-error during debugging.",
    source: "Trial production improvement",
    tone: "green",
  },
  {
    id: "changeover-saving",
    label: "Estimated saving per regular changeover",
    value: "RMB 20,000",
    count: { from: 0, to: 20000, template: "RMB {n}", final: "RMB 20,000" },
    detail: "Across inner/outer rings, auxiliary components, consumables, and labor efficiency.",
    source: "Model changeover support",
    tone: "amber",
  },
];

export function metricsById(ids: string[]) {
  return metrics.filter((metric) => ids.includes(metric.id));
}

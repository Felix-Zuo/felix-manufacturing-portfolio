import type { Metric } from "./types";

export const metrics: Metric[] = [
  {
    id: "notice-time",
    value: "20-40 min -> <1 min",
    label: "Production notice preparation",
    detail: "Structured inputs and generated release artifacts reduced repeated manual checks.",
    source: "Production notice workflow",
    tone: "blue",
  },
  {
    id: "takt-cycle",
    value: "3 days -> 1 day",
    label: "Trial takt analysis cycle",
    detail: "Full-line takt modeling shortened the adjustment loop before ramp-up.",
    source: "Trial production takt simulation",
    tone: "steel",
  },
  {
    id: "scrap-reduction",
    value: "~90% reduction",
    label: "Trial machining/debugging scrap",
    detail: "Data-supported adjustment reduced repeated trial-and-error during debugging.",
    source: "Trial production improvement",
    tone: "green",
  },
  {
    id: "changeover-saving",
    value: "~RMB 20,000",
    label: "Estimated saving per regular changeover",
    detail: "Across inner/outer rings, auxiliary components, consumables, and labor efficiency.",
    source: "Model changeover support",
    tone: "amber",
  },
];

export function metricsById(ids: string[]) {
  return metrics.filter((metric) => ids.includes(metric.id));
}


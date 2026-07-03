import { Gauge, ListChecks, Route, Workflow } from "lucide-react";

import { methodology } from "@/data/methodology";

const icons = [ListChecks, Route, Gauge, Workflow];

export function MethodologyGrid() {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {methodology.map((pillar, index) => {
        const Icon = icons[index] ?? ListChecks;
        return (
          <article className="rounded-lg border border-slate-300 bg-white p-5 shadow-sm" key={pillar.title}>
            <Icon className="h-6 w-6 text-blue-700" aria-hidden="true" />
            <h3 className="mt-4 text-lg font-semibold text-slate-950">{pillar.title}</h3>
            <p className="mt-3 text-sm leading-6 text-slate-600">{pillar.summary}</p>
            <ul className="mt-5 space-y-2 text-sm text-slate-700">
              {pillar.practices.map((practice) => (
                <li className="flex gap-2" key={practice}>
                  <span className="mt-2 h-1.5 w-1.5 flex-none rounded-full bg-emerald-500" />
                  <span>{practice}</span>
                </li>
              ))}
            </ul>
          </article>
        );
      })}
    </div>
  );
}


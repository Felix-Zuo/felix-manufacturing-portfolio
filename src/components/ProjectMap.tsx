import { CheckCircle2 } from "lucide-react";

import { projectCycle } from "@/data/profile";

export function ProjectMap() {
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
      {projectCycle.map((step, index) => (
        <article className="rounded-lg border border-slate-700 bg-slate-900 p-4 text-slate-100" key={step.label}>
          <div className="flex items-center gap-2 text-sm font-semibold text-amber-300">
            <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
            <span>{String(index + 1).padStart(2, "0")}</span>
          </div>
          <h3 className="mt-4 text-base font-semibold text-white">{step.label}</h3>
          <p className="mt-2 text-sm leading-6 text-slate-300">{step.detail}</p>
        </article>
      ))}
    </div>
  );
}


import { ArrowRight } from "lucide-react";

import type { WorkflowStep } from "@/data/types";

type BeforeAfterWorkflowProps = {
  before: WorkflowStep[];
  after: WorkflowStep[];
};

function StepList({ title, steps, tone }: { title: string; steps: WorkflowStep[]; tone: "before" | "after" }) {
  const accent = tone === "before" ? "text-amber-300" : "text-emerald-300";
  const rail = tone === "before" ? "bg-amber-400/40" : "bg-emerald-400/40";
  const marker = tone === "before" ? "border-amber-400/60 text-amber-300" : "border-emerald-400/60 text-emerald-300";

  return (
    <div className="surface-card rounded-md p-6">
      <p className={`mono-label ${accent}`}>{title}</p>
      <ol className="relative mt-6 space-y-6">
        <span className={`absolute bottom-2 left-[13px] top-2 w-px ${rail}`} aria-hidden="true" />
        {steps.map((step, index) => (
          <li className="relative flex gap-4" key={`${step.label}-${index}`}>
            <span
              className={`z-10 flex h-7 w-7 flex-none items-center justify-center rounded-md border bg-[#0a101d] font-mono text-xs font-semibold ${marker}`}
            >
              {index + 1}
            </span>
            <span>
              <strong className="block text-sm font-semibold text-slate-100">{step.label}</strong>
              <span className="mt-1 block text-sm leading-6 text-slate-500">{step.detail}</span>
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}

export function BeforeAfterWorkflow({ before, after }: BeforeAfterWorkflowProps) {
  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_auto_1fr] lg:items-center">
      <StepList steps={before} title="Before — manual loop" tone="before" />
      <div className="flex justify-center" aria-hidden="true">
        <span className="flex h-10 w-10 items-center justify-center rounded-full border hairline bg-[#0a101d]">
          <ArrowRight className="h-4 w-4 text-slate-400 max-lg:rotate-90" />
        </span>
      </div>
      <StepList steps={after} title="After — structured workflow" tone="after" />
    </div>
  );
}

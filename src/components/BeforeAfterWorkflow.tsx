import { ArrowRight } from "lucide-react";

import type { WorkflowStep } from "@/data/types";

type BeforeAfterWorkflowProps = {
  before: WorkflowStep[];
  after: WorkflowStep[];
};

function StepList({ title, steps, tone }: { title: string; steps: WorkflowStep[]; tone: "before" | "after" }) {
  const toneClass =
    tone === "before"
      ? "border-amber-300 bg-amber-50 text-amber-950"
      : "border-emerald-300 bg-emerald-50 text-emerald-950";

  return (
    <div className={`rounded-lg border p-5 ${toneClass}`}>
      <h3 className="text-lg font-semibold">{title}</h3>
      <ol className="mt-5 space-y-4">
        {steps.map((step, index) => (
          <li className="flex gap-3" key={`${step.label}-${index}`}>
            <span className="flex h-7 w-7 flex-none items-center justify-center rounded-md bg-white text-sm font-semibold text-slate-950">
              {index + 1}
            </span>
            <span>
              <strong className="block text-sm">{step.label}</strong>
              <span className="mt-1 block text-sm leading-6 text-slate-700">{step.detail}</span>
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}

export function BeforeAfterWorkflow({ before, after }: BeforeAfterWorkflowProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_auto_1fr] lg:items-center">
      <StepList title="Before" steps={before} tone="before" />
      <div className="flex justify-center">
        <ArrowRight className="hidden h-8 w-8 text-slate-400 lg:block" aria-hidden="true" />
        <div className="h-8 w-px bg-slate-300 lg:hidden" />
      </div>
      <StepList title="After" steps={after} tone="after" />
    </div>
  );
}


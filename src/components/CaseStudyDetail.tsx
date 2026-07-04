import Image from "next/image";
import Link from "next/link";
import { ArrowLeft, ArrowUpRight, CheckCircle2 } from "lucide-react";

import { metricsById } from "@/data/metrics";
import { projectsByIds } from "@/data/portfolioProjects";
import type { CaseStudy } from "@/data/types";
import { BeforeAfterWorkflow } from "./BeforeAfterWorkflow";
import { ConfidentialityNotice } from "./ConfidentialityNotice";
import { MetricCard } from "./MetricCard";

export function CaseStudyDetail({ caseStudy }: { caseStudy: CaseStudy }) {
  const relatedMetrics = metricsById(caseStudy.metricIds);
  const evidenceProjects = projectsByIds(caseStudy.evidenceProjectIds);

  return (
    <main className="min-h-screen bg-slate-50 text-slate-950">
      <section className="bg-slate-950 py-8 text-white">
        <div className="mx-auto max-w-6xl px-5">
          <Link className="inline-flex items-center gap-2 text-sm font-semibold text-blue-200 hover:text-white" href="/">
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Back to portfolio
          </Link>
          <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_0.9fr] lg:items-end">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wider text-amber-300">Manufacturing case study</p>
              <h1 className="mt-4 text-4xl font-semibold text-white">{caseStudy.title}</h1>
              <p className="mt-5 text-lg leading-8 text-slate-300">{caseStudy.subtitle}</p>
            </div>
            <div className="relative aspect-[16/10] overflow-hidden rounded-lg border border-slate-700 bg-slate-900">
              <Image src={caseStudy.image} alt={caseStudy.imageAlt} fill sizes="(max-width: 1024px) 100vw, 45vw" className="object-cover" loading="eager" fetchPriority="high" />
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-12">
        {relatedMetrics.length > 0 && (
          <div className="mb-10 grid gap-4 md:grid-cols-3">
            {relatedMetrics.map((metric) => (
              <MetricCard metric={metric} key={metric.id} />
            ))}
          </div>
        )}

        <div className="grid gap-8 lg:grid-cols-[0.85fr_1.15fr]">
          <div className="space-y-6">
            <article className="rounded-lg border border-slate-300 bg-white p-6 shadow-sm">
              <h2 className="text-2xl font-semibold">Problem</h2>
              <p className="mt-4 leading-7 text-slate-700">{caseStudy.problem}</p>
            </article>
            <article className="rounded-lg border border-slate-300 bg-white p-6 shadow-sm">
              <h2 className="text-2xl font-semibold">Felix&apos;s role</h2>
              <p className="mt-4 leading-7 text-slate-700">{caseStudy.role}</p>
            </article>
          </div>

          <article className="rounded-lg border border-slate-300 bg-white p-6 shadow-sm">
            <h2 className="text-2xl font-semibold">Methods and actions</h2>
            <div className="mt-6 grid gap-6 md:grid-cols-2">
              <div>
                <h3 className="font-semibold text-blue-800">Methods</h3>
                <ul className="mt-4 space-y-3 text-sm leading-6 text-slate-700">
                  {caseStudy.methods.map((method) => (
                    <li className="flex gap-2" key={method}>
                      <CheckCircle2 className="mt-1 h-4 w-4 flex-none text-emerald-600" aria-hidden="true" />
                      <span>{method}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-blue-800">Actions</h3>
                <ul className="mt-4 space-y-3 text-sm leading-6 text-slate-700">
                  {caseStudy.actions.map((action) => (
                    <li className="flex gap-2" key={action}>
                      <CheckCircle2 className="mt-1 h-4 w-4 flex-none text-emerald-600" aria-hidden="true" />
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </article>
        </div>

        <section className="mt-12">
          <h2 className="mb-6 text-2xl font-semibold">Before / after workflow</h2>
          <BeforeAfterWorkflow before={caseStudy.before} after={caseStudy.after} />
        </section>

        <section className="mt-12 grid gap-8 lg:grid-cols-[1fr_0.8fr]">
          <article className="rounded-lg border border-slate-300 bg-white p-6 shadow-sm">
            <h2 className="text-2xl font-semibold">Outcomes</h2>
            <ul className="mt-5 space-y-4 leading-7 text-slate-700">
              {caseStudy.outcomes.map((outcome) => (
                <li className="flex gap-3" key={outcome}>
                  <CheckCircle2 className="mt-1 h-5 w-5 flex-none text-emerald-600" aria-hidden="true" />
                  <span>{outcome}</span>
                </li>
              ))}
            </ul>
          </article>

          <article className="rounded-lg border border-slate-300 bg-white p-6 shadow-sm">
            <h2 className="text-2xl font-semibold">Public evidence</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Public sanitized or synthetic-data showcase based on real manufacturing workflow
              patterns — not an internal system.
            </p>
            <div className="mt-5 space-y-5">
              {evidenceProjects.map((project) => (
                <div className="border-t border-slate-200 pt-5 first:border-t-0 first:pt-0" key={project.id}>
                  <h3 className="font-semibold text-slate-950">{project.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">{project.evidenceRole}</p>
                  <div className="mt-3 flex flex-wrap gap-3">
                    {project.repoUrl && (
                      <a className="inline-flex items-center gap-2 text-sm font-semibold text-blue-700 hover:text-blue-900" href={project.repoUrl} target="_blank" rel="noreferrer">
                        GitHub <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
                      </a>
                    )}
                    {project.liveUrl && (
                      <a className="inline-flex items-center gap-2 text-sm font-semibold text-blue-700 hover:text-blue-900" href={project.liveUrl} target="_blank" rel="noreferrer">
                        Live page <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </article>
        </section>

        <div className="mt-12">
          <ConfidentialityNotice text="This case study is presented with sanitized or synthetic data. It describes selected improvement outcomes and tool concepts based on real manufacturing workflow patterns. No customer names, private BOMs, supplier records, internal system exports, production routes, machine parameters, or confidential factory files are disclosed." />
        </div>
      </section>
    </main>
  );
}

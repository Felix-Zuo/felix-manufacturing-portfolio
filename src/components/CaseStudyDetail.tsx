import Link from "next/link";
import { ArrowLeft, ArrowRight, ArrowUpRight, CheckCircle2 } from "lucide-react";

import { caseStudies } from "@/data/caseStudies";
import { metricsById } from "@/data/metrics";
import { projectsByIds } from "@/data/portfolioProjects";
import type { CaseStudy } from "@/data/types";
import { BeforeAfterWorkflow } from "./BeforeAfterWorkflow";
import { ConfidentialityNotice } from "./ConfidentialityNotice";
import { MetricCard } from "./MetricCard";
import { Reveal } from "./Reveal";
import { ScreenshotFrame } from "./ScreenshotFrame";

const CASE_CONFIDENTIALITY =
  "This case study is presented with sanitized or synthetic data. It describes selected improvement outcomes and tool concepts based on real manufacturing workflow patterns. No customer names, private BOMs, supplier records, internal system exports, production routes, machine parameters, or confidential factory files are disclosed.";

export function CaseStudyDetail({ caseStudy }: { caseStudy: CaseStudy }) {
  const relatedMetrics = metricsById(caseStudy.metricIds);
  const evidenceProjects = projectsByIds(caseStudy.evidenceProjectIds);
  const index = caseStudies.findIndex((entry) => entry.slug === caseStudy.slug);
  const nextCase = caseStudies[(index + 1) % caseStudies.length];

  return (
    <main className="pt-16">
      {/* Case hero */}
      <section className="relative overflow-hidden border-b hairline">
        <div className="blueprint-grid grid-fade absolute inset-0 opacity-50" aria-hidden="true" />
        <div className="relative mx-auto max-w-6xl px-5 pb-16 pt-12">
          <Link
            className="group inline-flex items-center gap-2 text-sm font-semibold text-slate-400 transition-colors hover:text-slate-100"
            href="/#case-studies"
          >
            <ArrowLeft className="h-4 w-4 transition-transform group-hover:-translate-x-0.5" aria-hidden="true" />
            All case studies
          </Link>
          <div className="mt-10 grid items-end gap-10 lg:grid-cols-[1fr_0.9fr]">
            <Reveal>
              <p className="mono-label text-amber-400/90">
                Case {String(index + 1).padStart(2, "0")} · Manufacturing case study
              </p>
              <h1 className="mt-4 text-3xl font-semibold tracking-tight text-slate-100 sm:text-4xl">
                {caseStudy.title}
              </h1>
              <p className="mt-5 max-w-xl text-lg leading-8 text-slate-400">{caseStudy.subtitle}</p>
            </Reveal>
            <Reveal delay={0.12}>
              <ScreenshotFrame
                alt={caseStudy.imageAlt}
                eager
                src={caseStudy.image}
                url={caseStudy.imageSourceUrl}
              />
            </Reveal>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-6xl px-5 py-16">
        {relatedMetrics.length > 0 && (
          <div className="mb-14 grid gap-5 md:grid-cols-3">
            {relatedMetrics.map((metric, metricIndex) => (
              <Reveal className="h-full" delay={metricIndex * 0.06} key={metric.id}>
                <MetricCard metric={metric} />
              </Reveal>
            ))}
          </div>
        )}

        <div className="grid gap-5 lg:grid-cols-[0.85fr_1.15fr]">
          <div className="space-y-5">
            <Reveal>
              <article className="surface-card rounded-xl p-6">
                <h2 className="mono-label text-amber-400/90">Problem</h2>
                <p className="mt-4 leading-7 text-slate-300">{caseStudy.problem}</p>
              </article>
            </Reveal>
            <Reveal delay={0.06}>
              <article className="surface-card rounded-xl p-6">
                <h2 className="mono-label text-amber-400/90">Felix&apos;s role</h2>
                <p className="mt-4 leading-7 text-slate-300">{caseStudy.role}</p>
              </article>
            </Reveal>
          </div>

          <Reveal delay={0.1}>
            <article className="surface-card h-full rounded-xl p-6">
              <h2 className="mono-label text-amber-400/90">Methods and actions</h2>
              <div className="mt-6 grid gap-8 md:grid-cols-2">
                <div>
                  <h3 className="text-sm font-semibold text-slate-100">Methods</h3>
                  <ul className="mt-4 space-y-2.5 text-sm leading-6 text-slate-400">
                    {caseStudy.methods.map((method) => (
                      <li className="flex gap-2.5" key={method}>
                        <span className="mt-[9px] h-px w-3 flex-none bg-sky-400/60" aria-hidden="true" />
                        <span>{method}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-100">Actions</h3>
                  <ul className="mt-4 space-y-2.5 text-sm leading-6 text-slate-400">
                    {caseStudy.actions.map((action) => (
                      <li className="flex gap-2.5" key={action}>
                        <span className="mt-[9px] h-px w-3 flex-none bg-emerald-400/60" aria-hidden="true" />
                        <span>{action}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </article>
          </Reveal>
        </div>

        <section className="mt-16">
          <h2 className="mono-label mb-8 text-amber-400/90">Before / after workflow</h2>
          <Reveal>
            <BeforeAfterWorkflow after={caseStudy.after} before={caseStudy.before} />
          </Reveal>
        </section>

        <section className="mt-16 grid gap-5 lg:grid-cols-[1fr_0.8fr]">
          <Reveal>
            <article className="surface-card h-full rounded-xl p-6">
              <h2 className="mono-label text-emerald-300">Outcomes</h2>
              <ul className="mt-5 space-y-4 leading-7 text-slate-300">
                {caseStudy.outcomes.map((outcome) => (
                  <li className="flex gap-3" key={outcome}>
                    <CheckCircle2 className="mt-1 h-5 w-5 flex-none text-emerald-400" aria-hidden="true" />
                    <span>{outcome}</span>
                  </li>
                ))}
              </ul>
            </article>
          </Reveal>

          <Reveal delay={0.08}>
            <article className="surface-card h-full rounded-xl p-6">
              <h2 className="mono-label text-amber-400/90">Public evidence</h2>
              <p className="mt-3 text-sm leading-6 text-slate-500">
                Public sanitized or synthetic-data showcase based on real manufacturing workflow
                patterns — not an internal system.
              </p>
              <div className="mt-5 space-y-5">
                {evidenceProjects.map((project) => (
                  <div className="border-t hairline pt-5 first:border-t-0 first:pt-0" key={project.id}>
                    <h3 className="font-semibold text-slate-100">{project.title}</h3>
                    <p className="mt-2 text-sm leading-6 text-slate-500">{project.evidenceRole}</p>
                    <div className="mt-3 flex flex-wrap gap-4">
                      {project.repoUrl && (
                        <a
                          className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-300 transition-colors hover:text-white"
                          href={project.repoUrl}
                          rel="noreferrer"
                          target="_blank"
                        >
                          GitHub <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" />
                        </a>
                      )}
                      {project.liveUrl && (
                        <a
                          className="inline-flex items-center gap-1.5 text-sm font-semibold text-sky-300 transition-colors hover:text-sky-200"
                          href={project.liveUrl}
                          rel="noreferrer"
                          target="_blank"
                        >
                          Live page <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </Reveal>
        </section>

        <div className="mt-16">
          <ConfidentialityNotice text={CASE_CONFIDENTIALITY} />
        </div>

        {/* Next case pagination */}
        <Link
          className="group mt-16 flex items-center justify-between rounded-xl border hairline bg-[#0a101d] p-6 transition-colors hover:border-slate-500/40"
          href={`/case-studies/${nextCase.slug}`}
        >
          <div>
            <p className="mono-label text-slate-500">Next case</p>
            <p className="mt-2 text-lg font-semibold tracking-tight text-slate-100">{nextCase.title}</p>
          </div>
          <ArrowRight
            className="h-5 w-5 flex-none text-amber-300 transition-transform group-hover:translate-x-1"
            aria-hidden="true"
          />
        </Link>
      </div>
    </main>
  );
}

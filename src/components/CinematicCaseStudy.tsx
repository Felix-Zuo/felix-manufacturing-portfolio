import Link from "next/link";
import { ArrowRight, CheckCircle2 } from "lucide-react";

import { metricsById } from "@/data/metrics";
import type { CaseStudy } from "@/data/types";
import { BulletTimeCard } from "./CinematicScene";
import { ScreenshotFrame } from "./ScreenshotFrame";

export function CinematicCaseStudy({
  caseStudy,
  index,
}: {
  caseStudy: CaseStudy;
  index: number;
}) {
  const relatedMetrics = metricsById(caseStudy.metricIds);
  const number = String(index + 1).padStart(2, "0");
  const reversed = index % 2 === 1;

  return (
    <article className="grid items-center gap-10 lg:grid-cols-2 lg:gap-14 [&>*]:min-w-0">
      <div className={reversed ? "lg:order-2" : ""}>
        <p className="mono-label text-amber-300">Case node {number}</p>
        <h2 className="mt-4 max-w-xl text-3xl font-semibold leading-tight text-slate-100 sm:text-4xl">
          {caseStudy.title}
        </h2>
        <p className="mt-4 max-w-xl text-lg leading-7 text-slate-300">{caseStudy.subtitle}</p>
        <p className="mt-4 max-w-xl leading-7 text-slate-400">{caseStudy.summary}</p>

        {relatedMetrics.length > 0 && (
          <dl className="mt-6 flex flex-wrap gap-2.5">
            {relatedMetrics.map((metric) => (
              <div className="surface-card rounded-md px-3 py-2" key={metric.id}>
                <dt className="sr-only">{metric.label}</dt>
                <dd className="font-mono text-sm font-semibold text-slate-100">
                  {metric.before ? `${metric.before} -> ${metric.value}` : metric.value}
                </dd>
                <dd className="mt-1 text-xs text-slate-500">{metric.label}</dd>
              </div>
            ))}
          </dl>
        )}

        <ul className="mt-6 space-y-2.5">
          {caseStudy.outcomes.slice(0, 3).map((outcome) => (
            <li className="flex gap-3 text-sm leading-6 text-slate-400" key={outcome}>
              <CheckCircle2 className="mt-1 h-4 w-4 flex-none text-emerald-300" aria-hidden="true" />
              <span>{outcome}</span>
            </li>
          ))}
        </ul>

        <Link
          className="group mt-7 inline-flex items-center gap-2 text-sm font-semibold text-amber-300 transition-colors hover:text-amber-200"
          href={`/case-studies/${caseStudy.slug}`}
        >
          Open full case study
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
        </Link>
      </div>

      <BulletTimeCard className={reversed ? "lg:order-1" : ""} direction={reversed ? -1 : 1}>
        <ScreenshotFrame
          alt={caseStudy.imageAlt}
          src={caseStudy.image}
          url={caseStudy.imageSourceUrl}
        />
      </BulletTimeCard>
    </article>
  );
}

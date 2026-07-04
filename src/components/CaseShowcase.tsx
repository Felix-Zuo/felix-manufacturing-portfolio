import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { metricsById } from "@/data/metrics";
import type { CaseStudy } from "@/data/types";
import { Reveal } from "./Reveal";
import { ScreenshotFrame } from "./ScreenshotFrame";

export function CaseShowcase({ caseStudy, index }: { caseStudy: CaseStudy; index: number }) {
  const relatedMetrics = metricsById(caseStudy.metricIds);
  const number = String(index + 1).padStart(2, "0");
  const reversed = index % 2 === 1;

  return (
    <article className="relative border-t hairline py-16 first:border-t-0 first:pt-0 lg:py-20">
      <span
        aria-hidden="true"
        className="pointer-events-none absolute -top-3 right-0 select-none font-mono text-[110px] font-semibold leading-none text-slate-500/40 lg:text-[150px]"
      >
        {number}
      </span>
      <div className={`grid items-center gap-10 lg:grid-cols-2 lg:gap-14 ${reversed ? "lg:[&>*:first-child]:order-2" : ""} [&>*]:min-w-0`}>
        <Reveal>
          <p className="mono-label text-amber-400/90">Case {number}</p>
          <h3 className="mt-3 max-w-lg text-2xl font-semibold tracking-tight text-slate-100 sm:text-3xl">
            {caseStudy.title}
          </h3>
          <p className="mt-4 max-w-lg leading-7 text-slate-400">{caseStudy.summary}</p>

          {relatedMetrics.length > 0 && (
            <dl className="mt-6 flex flex-wrap gap-2.5">
              {relatedMetrics.map((metric) => (
                <div className="rounded-md border hairline bg-[#0a101d] px-3 py-2" key={metric.id}>
                  <dt className="sr-only">{metric.label}</dt>
                  <dd className="font-mono text-sm font-semibold text-slate-200">
                    {metric.before ? `${metric.before} → ${metric.value}` : metric.value}
                  </dd>
                  <dd className="mt-0.5 text-xs text-slate-500">{metric.label}</dd>
                </div>
              ))}
            </dl>
          )}

          <Link
            className="group mt-8 inline-flex items-center gap-2 text-sm font-semibold text-amber-300 transition-colors hover:text-amber-200"
            href={`/case-studies/${caseStudy.slug}`}
          >
            Read the full case
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" aria-hidden="true" />
          </Link>
        </Reveal>

        <Reveal delay={0.12}>
          <ScreenshotFrame
            alt={caseStudy.imageAlt}
            src={caseStudy.image}
            url={caseStudy.imageSourceUrl}
          />
        </Reveal>
      </div>
    </article>
  );
}

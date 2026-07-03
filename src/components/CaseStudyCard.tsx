import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight, Factory } from "lucide-react";

import { metricsById } from "@/data/metrics";
import type { CaseStudy } from "@/data/types";

export function CaseStudyCard({ caseStudy }: { caseStudy: CaseStudy }) {
  const relatedMetrics = metricsById(caseStudy.metricIds);

  return (
    <article className="overflow-hidden rounded-lg border border-slate-300 bg-white shadow-sm">
      <div className="relative aspect-[16/9] bg-slate-900">
        <Image
          src={caseStudy.image}
          alt={caseStudy.imageAlt}
          fill
          sizes="(max-width: 1024px) 100vw, 33vw"
          className="object-cover"
        />
      </div>
      <div className="p-5">
        <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-blue-700">
          <Factory className="h-4 w-4" aria-hidden="true" />
          <span>Case study</span>
        </div>
        <h3 className="text-xl font-semibold text-slate-950">{caseStudy.title}</h3>
        <p className="mt-3 text-sm leading-6 text-slate-600">{caseStudy.summary}</p>
        {relatedMetrics.length > 0 && (
          <div className="mt-5 grid gap-2">
            {relatedMetrics.map((metric) => (
              <div className="rounded-md border border-slate-200 bg-slate-50 p-3" key={metric.id}>
                <strong className="block text-base text-slate-950">{metric.value}</strong>
                <span className="text-sm text-slate-600">{metric.label}</span>
              </div>
            ))}
          </div>
        )}
        <Link
          className="mt-5 inline-flex items-center gap-2 rounded-md bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-800"
          href={`/case-studies/${caseStudy.slug}`}
        >
          Read case study
          <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
        </Link>
      </div>
    </article>
  );
}


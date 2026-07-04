import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight, ExternalLink, GitBranch } from "lucide-react";

import type { PortfolioProject } from "@/data/types";

export function PortfolioProjectCard({ project }: { project: PortfolioProject }) {
  return (
    <article className="rounded-lg border border-slate-700 bg-slate-900 p-5 text-slate-100">
      {project.image && (
        <div className="relative mb-5 aspect-[16/9] overflow-hidden rounded-md border border-slate-700 bg-slate-950">
          <Image
            src={project.image}
            alt={project.imageAlt ?? project.title}
            fill
            sizes="(max-width: 1024px) 100vw, 33vw"
            className="object-cover"
          />
        </div>
      )}
      <p className="text-sm font-semibold uppercase tracking-wider text-amber-300">{project.tier}</p>
      <h3 className="mt-3 text-xl font-semibold text-white">{project.title}</h3>
      <p className="mt-3 text-sm leading-6 text-slate-300">{project.description}</p>
      <dl className="mt-5 space-y-3 text-sm">
        <div>
          <dt className="font-semibold text-slate-100">Evidence role</dt>
          <dd className="mt-1 text-slate-300">{project.evidenceRole}</dd>
        </div>
        <div>
          <dt className="font-semibold text-slate-100">Boundary</dt>
          <dd className="mt-1 text-slate-300">{project.dataBoundary}</dd>
        </div>
      </dl>
      <div className="mt-5 flex flex-wrap gap-3">
        {project.repoUrl && (
          <a
            className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-3 py-2 text-sm font-semibold text-white transition hover:border-blue-300 hover:text-blue-200"
            href={project.repoUrl}
            target="_blank"
            rel="noreferrer"
          >
            <GitBranch className="h-4 w-4" aria-hidden="true" />
            GitHub
          </a>
        )}
        {project.liveUrl && (
          <a
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-blue-500"
            href={project.liveUrl}
            target="_blank"
            rel="noreferrer"
          >
            <ExternalLink className="h-4 w-4" aria-hidden="true" />
            Live page
          </a>
        )}
        {project.relatedCaseSlugs[0] && (
          <Link
            className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-3 py-2 text-sm font-semibold text-white transition hover:border-emerald-300 hover:text-emerald-200"
            href={`/case-studies/${project.relatedCaseSlugs[0]}`}
          >
            Case link
            <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        )}
      </div>
    </article>
  );
}

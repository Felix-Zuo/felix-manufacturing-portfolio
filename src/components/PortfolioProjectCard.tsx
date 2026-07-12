import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight, ExternalLink, GitBranch } from "lucide-react";

import type { PortfolioProject } from "@/data/types";

const tierTone: Record<PortfolioProject["tier"], string> = {
  "Main evidence": "text-amber-300 border-amber-400/40",
  "System concept": "text-sky-300 border-sky-400/40",
  "Method support": "text-emerald-300 border-emerald-400/40",
  Experimental: "text-slate-400 border-slate-500/40",
};

export function PortfolioProjectCard({
  compact = false,
  project,
}: {
  compact?: boolean;
  project: PortfolioProject;
}) {
  return (
    <article className="surface-card group flex h-full flex-col overflow-hidden rounded-md transition-colors hover:border-slate-500/40">
      {project.image && !compact && (
        <div className="relative aspect-[16/9] overflow-hidden border-b hairline bg-[#070c16]">
          <Image
            src={project.image}
            alt={project.imageAlt ?? project.title}
            fill
            sizes="(max-width: 1024px) 100vw, 33vw"
            className="object-cover object-top transition-transform duration-500 group-hover:scale-[1.02]"
          />
        </div>
      )}
      <div className={`flex flex-1 flex-col ${compact ? "p-4" : "p-5"}`}>
        <p className={`mono-label w-fit rounded border px-2 py-1 ${tierTone[project.tier]}`}>{project.tier}</p>
        <h3 className={`${compact ? "mt-3 text-base" : "mt-4 text-lg"} font-semibold text-slate-100`}>{project.title}</h3>
        <p className="mt-2.5 text-sm leading-6 text-slate-400">{project.description}</p>
        <p className={`mono-label ${compact ? "mt-3" : "mt-4"} text-slate-600`}>{project.stack}</p>
        <p className="mt-3 text-xs leading-5 text-slate-500">
          <span className="font-semibold text-emerald-400/80">Boundary·</span> {project.dataBoundary}
        </p>
        <div className={`mt-auto flex flex-wrap gap-4 ${compact ? "pt-4" : "pt-5"}`}>
          {project.repoUrl && (
            <a
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-300 transition-colors hover:text-white"
              href={project.repoUrl}
              rel="noreferrer"
              target="_blank"
            >
              <GitBranch className="h-3.5 w-3.5" aria-hidden="true" />
              GitHub
            </a>
          )}
          {project.liveUrl && (
            <a
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-sky-300 transition-colors hover:text-sky-200"
              href={project.liveUrl}
              rel="noreferrer"
              target="_blank"
            >
              <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
              Live page
            </a>
          )}
          {project.relatedCaseSlugs[0] && (
            <Link
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-amber-300 transition-colors hover:text-amber-200"
              href={`/case-studies/${project.relatedCaseSlugs[0]}`}
            >
              Case
              <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" />
            </Link>
          )}
        </div>
      </div>
    </article>
  );
}

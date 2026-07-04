import { ArrowUpRight, Mail } from "lucide-react";

import { profile } from "@/data/profile";

export function CTA() {
  return (
    <section className="bg-slate-950 py-16 text-white" id="contact">
      <div className="mx-auto grid max-w-6xl gap-8 px-5 md:grid-cols-[1.2fr_0.8fr] md:items-center">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wider text-amber-300">Resume / contact</p>
          <h2 className="mt-3 text-3xl font-semibold">Manufacturing execution, improved with proof.</h2>
          <p className="mt-4 max-w-2xl leading-7 text-slate-300">
            The strongest fit is a role where project coordination, supply-production-delivery visibility,
            launch readiness, and practical workflow tooling need to work together. Email is the fastest
            way to reach Felix or request a resume.
          </p>
        </div>
        <div className="flex flex-wrap gap-3 md:justify-end">
          <a
            className="inline-flex items-center gap-2 rounded-md bg-emerald-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
            href={`mailto:${profile.email}`}
          >
            <Mail className="h-4 w-4" aria-hidden="true" />
            Email Felix
          </a>
          <a
            className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-4 py-3 text-sm font-semibold text-white transition hover:border-blue-300 hover:text-blue-200"
            href={profile.github}
            target="_blank"
            rel="noreferrer"
          >
            GitHub portfolio
            <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
          </a>
        </div>
      </div>
    </section>
  );
}

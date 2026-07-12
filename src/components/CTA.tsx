import { ArrowUpRight, Mail } from "lucide-react";

import { profile } from "@/data/profile";
import { Reveal } from "./Reveal";

export function CTA() {
  return (
    <section className="relative overflow-hidden border-t hairline" id="contact">
      <div className="blueprint-grid grid-fade absolute inset-0 opacity-40" aria-hidden="true" />
      <div className="relative mx-auto max-w-6xl px-5 py-24 text-center">
        <Reveal>
          <p className="mono-label text-amber-400/90">Resume / contact</p>
          <h2 className="mx-auto mt-5 max-w-2xl text-3xl font-semibold text-slate-100 sm:text-4xl">
            Manufacturing execution, improved with proof.
          </h2>
          <p className="mx-auto mt-5 max-w-xl leading-7 text-slate-400">
            The strongest fit is a role where project coordination, supply-production-delivery
            visibility, launch readiness, and practical workflow tooling need to work together.
            Email is the fastest way to reach Felix or request a resume.
          </p>
          <div className="mt-9 flex flex-wrap justify-center gap-3">
            <a
              className="inline-flex items-center gap-2 rounded-md bg-amber-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-amber-300"
              href={`mailto:${profile.email}`}
            >
              <Mail className="h-4 w-4" aria-hidden="true" />
              Email Felix
            </a>
            <a
              className="inline-flex items-center gap-2 rounded-md border hairline px-5 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:text-white"
              href={profile.github}
              rel="noreferrer"
              target="_blank"
            >
              GitHub portfolio
              <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
            </a>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

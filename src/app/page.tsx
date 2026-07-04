import { ArrowDown, Mail } from "lucide-react";

import { BeforeAfterWorkflow } from "@/components/BeforeAfterWorkflow";
import { CaseShowcase } from "@/components/CaseShowcase";
import { ConfidentialityNotice } from "@/components/ConfidentialityNotice";
import { CTA } from "@/components/CTA";
import { HeroConsole } from "@/components/HeroConsole";
import { MethodologyGrid } from "@/components/MethodologyGrid";
import { MetricCard } from "@/components/MetricCard";
import { PortfolioProjectCard } from "@/components/PortfolioProjectCard";
import { ProjectMap } from "@/components/ProjectMap";
import { Reveal } from "@/components/Reveal";
import { SectionHeading } from "@/components/SectionHeading";
import { StatusTicker } from "@/components/StatusTicker";
import { caseStudies } from "@/data/caseStudies";
import { metrics } from "@/data/metrics";
import { portfolioProjects } from "@/data/portfolioProjects";
import { profile } from "@/data/profile";

export default function Home() {
  return (
    <main>
      {/* Hero */}
      <section className="relative overflow-hidden pt-16">
        <div className="blueprint-grid grid-fade absolute inset-0 opacity-60" aria-hidden="true" />
        <div className="relative mx-auto grid max-w-6xl items-center gap-14 px-5 pb-20 pt-16 lg:grid-cols-[1.05fr_0.95fr] lg:pb-28 lg:pt-24">
          <Reveal>
            <p className="mono-label text-amber-400/90">{profile.headline}</p>
            <h1 className="mt-6 text-4xl font-semibold leading-[1.1] tracking-tight text-slate-100 sm:text-5xl lg:text-[3.4rem]">
              {profile.heroTitle.lead}{" "}
              <span className="text-amber-300">{profile.heroTitle.emphasis}</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-8 text-slate-400">{profile.summary}</p>
            <div className="mt-9 flex flex-wrap gap-3">
              <a
                className="inline-flex items-center gap-2 rounded-md bg-amber-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-amber-300"
                href="#case-studies"
              >
                View case studies
                <ArrowDown className="h-4 w-4" aria-hidden="true" />
              </a>
              <a
                className="inline-flex items-center gap-2 rounded-md border hairline px-5 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-500 hover:text-white"
                href={`mailto:${profile.email}`}
              >
                <Mail className="h-4 w-4" aria-hidden="true" />
                Email Felix
              </a>
            </div>
            <div className="mt-9 flex flex-wrap gap-2">
              {profile.targetDirections.slice(0, 4).map((direction) => (
                <span className="rounded border hairline bg-[#0a101d]/80 px-3 py-1.5 text-xs text-slate-400" key={direction}>
                  {direction}
                </span>
              ))}
            </div>
          </Reveal>
          <Reveal delay={0.15}>
            <HeroConsole />
          </Reveal>
        </div>
      </section>

      <StatusTicker />

      {/* Impact metrics */}
      <section className="mx-auto max-w-6xl px-5 py-24" id="impact">
        <SectionHeading
          index="01"
          eyebrow="Impact metrics"
          title="Outcomes first. Tools second."
          summary="Four measured improvements from real manufacturing execution work. Every public demo behind them uses sanitized or synthetic data."
        />
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric, index) => (
            <Reveal className="h-full" delay={index * 0.06} key={metric.id}>
              <MetricCard metric={metric} />
            </Reveal>
          ))}
        </div>
      </section>

      {/* Project map */}
      <section className="border-t hairline bg-[#070c16]" id="project-map">
        <div className="mx-auto max-w-6xl px-5 py-24">
          <SectionHeading
            index="02"
            eyebrow="Full-cycle project map"
            title="From risk review to delivery, audit, and corrective action."
            summary="Felix coordinates and improves execution across all ten stages of the launch-to-delivery chain, with digital tools supporting the work at each stage."
          />
          <ProjectMap />
        </div>
      </section>

      {/* Case studies */}
      <section className="mx-auto max-w-6xl px-5 py-24" id="case-studies">
        <SectionHeading
          index="03"
          eyebrow="Case studies"
          title="Three manufacturing problems, three measured improvements."
          summary="Each case follows the same structure: problem, role, methods, actions, outcomes, and public sanitized evidence."
        />
        <div>
          {caseStudies.map((caseStudy, index) => (
            <CaseShowcase caseStudy={caseStudy} index={index} key={caseStudy.slug} />
          ))}
        </div>
      </section>

      {/* Before / after pattern */}
      <section className="border-t hairline bg-[#070c16]">
        <div className="mx-auto max-w-6xl px-5 py-24">
          <SectionHeading
            index="04"
            eyebrow="The improvement pattern"
            title="Manual checking becomes a controlled review workflow."
            summary="The production notice case shows the pattern used across the portfolio: clarify the work, structure the inputs, generate reviewable artifacts, and keep release under human control."
          />
          <Reveal>
            <BeforeAfterWorkflow after={caseStudies[0].after} before={caseStudies[0].before} />
          </Reveal>
        </div>
      </section>

      {/* Portfolio lab */}
      <section className="mx-auto max-w-6xl px-5 py-24" id="portfolio-lab">
        <SectionHeading
          index="05"
          eyebrow="Portfolio Lab"
          title="Public sanitized projects that make the work inspectable."
          summary="These projects demonstrate the same workflow patterns as the case studies — structured notices, takt simulation, and operations dashboards — alongside supporting method and verification tools, all built with synthetic or public-safe data."
        />
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {portfolioProjects.map((project, index) => (
            <Reveal className="h-full" delay={(index % 3) * 0.06} key={project.id}>
              <PortfolioProjectCard project={project} />
            </Reveal>
          ))}
        </div>
        <div className="mt-8 grid gap-4 lg:grid-cols-2">
          <div className="rounded-xl border border-amber-400/25 bg-amber-950/20 p-5">
            <p className="mono-label text-amber-300">BOM toolkit status</p>
            <p className="mt-2.5 text-sm leading-6 text-slate-400">
              BOM and material readiness are represented through public synthetic examples in the
              current version. A dedicated BOM knowledge toolkit remains outside public evidence
              until a separate data-safety review is complete.
            </p>
          </div>
          <ConfidentialityNotice compact />
        </div>
      </section>

      {/* Methodology */}
      <section className="border-t hairline bg-[#070c16]" id="methodology">
        <div className="mx-auto max-w-6xl px-5 py-24">
          <SectionHeading
            index="06"
            eyebrow="Methodology"
            title="A practical operating system for manufacturing improvement."
            summary="Not a buzzword list — a working loop that connects project control, launch support, continuous improvement, and digital workflow tools."
          />
          <MethodologyGrid />
        </div>
      </section>

      {/* About */}
      <section className="mx-auto max-w-6xl px-5 py-24" id="about">
        <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr]">
          <Reveal>
            <p className="mono-label text-amber-400/90">About Felix</p>
            <h2 className="mt-4 text-3xl font-semibold tracking-tight text-slate-100">{profile.name}</h2>
            <p className="mt-2 text-sm text-slate-500">{profile.currentTitle}</p>
          </Reveal>
          <Reveal delay={0.08}>
            <div className="space-y-6">
              <p className="text-lg leading-8 text-slate-300">{profile.locationContext}</p>
              <p className="leading-7 text-slate-400">
                He coordinates production planning, material readiness, inventory and WIP tracking,
                purchasing follow-up, shipment coordination, and cross-functional factory
                communication, using milestone tracking, PDCA cycles, and Lean Six Sigma thinking to
                improve project visibility and execution efficiency.
              </p>
            </div>
          </Reveal>
        </div>
      </section>

      <CTA />
    </main>
  );
}

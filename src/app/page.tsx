import Image from "next/image";
import Link from "next/link";
import { ArrowDown, Factory, GitBranch, ShieldCheck } from "lucide-react";

import { BeforeAfterWorkflow } from "@/components/BeforeAfterWorkflow";
import { CaseStudyCard } from "@/components/CaseStudyCard";
import { ConfidentialityNotice } from "@/components/ConfidentialityNotice";
import { CTA } from "@/components/CTA";
import { MethodologyGrid } from "@/components/MethodologyGrid";
import { MetricCard } from "@/components/MetricCard";
import { PortfolioProjectCard } from "@/components/PortfolioProjectCard";
import { ProjectMap } from "@/components/ProjectMap";
import { Reveal } from "@/components/Reveal";
import { SectionHeader } from "@/components/SectionHeader";
import { caseStudies } from "@/data/caseStudies";
import { metrics } from "@/data/metrics";
import { navigation } from "@/data/navigation";
import { portfolioProjects } from "@/data/portfolioProjects";
import { profile } from "@/data/profile";

export default function Home() {
  return (
    <>
      <header className="sticky top-0 z-30 border-b border-slate-800 bg-slate-950/95 text-white backdrop-blur">
        <nav className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4">
          <Link className="flex items-center gap-3 font-semibold" href="/">
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-amber-400 text-slate-950">
              <Factory className="h-5 w-5" aria-hidden="true" />
            </span>
            <span>Felix Zuo</span>
          </Link>
          <div className="hidden items-center gap-5 lg:flex">
            {navigation.map((item) => (
              <a className="text-sm text-slate-300 transition hover:text-white" href={item.href} key={item.href}>
                {item.label}
              </a>
            ))}
          </div>
          <a
            className="inline-flex items-center gap-2 rounded-md border border-slate-700 px-3 py-2 text-sm font-semibold text-white transition hover:border-blue-300 hover:text-blue-200"
            href={profile.github}
            target="_blank"
            rel="noreferrer"
          >
            <GitBranch className="h-4 w-4" aria-hidden="true" />
            GitHub
          </a>
        </nav>
      </header>

      <main className="bg-slate-50 text-slate-950">
      <section className="bg-slate-950 text-white">
        <div className="mx-auto grid max-w-7xl gap-10 px-5 py-14 lg:grid-cols-[1.02fr_0.98fr] lg:items-center">
          <Reveal>
            <p className="text-sm font-semibold uppercase tracking-wider text-amber-300">Manufacturing improvement portfolio</p>
            <h1 className="mt-5 text-4xl font-semibold leading-tight text-white sm:text-5xl sm:leading-[1.08]">
              {profile.headline}
            </h1>
            <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-300">{profile.summary}</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a
                className="inline-flex items-center gap-2 rounded-md bg-emerald-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
                href="#case-studies"
              >
                View case studies
                <ArrowDown className="h-4 w-4" aria-hidden="true" />
              </a>
              <a
                className="inline-flex items-center gap-2 rounded-md border border-slate-600 px-4 py-3 text-sm font-semibold text-white transition hover:border-blue-300 hover:text-blue-200"
                href="#portfolio-lab"
              >
                Public evidence
                <ArrowDown className="h-4 w-4" aria-hidden="true" />
              </a>
            </div>
            <div className="mt-8 flex flex-wrap gap-2 text-sm text-slate-300">
              {profile.targetDirections.slice(0, 4).map((direction) => (
                <span className="rounded-md border border-slate-700 px-3 py-2" key={direction}>
                  {direction}
                </span>
              ))}
            </div>
          </Reveal>

          <Reveal delay={0.12}>
            <div className="overflow-hidden rounded-lg border border-slate-700 bg-slate-900 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-700 px-4 py-3">
                <span className="text-sm font-semibold text-slate-200">Public sanitized evidence</span>
                <span className="rounded-md bg-emerald-500 px-2 py-1 text-xs font-semibold text-slate-950">
                  No private factory data
                </span>
              </div>
              <div className="relative aspect-[16/10] bg-slate-950">
                <Image
                  src="/evidence/factory-takt-showcase.png"
                  alt="Factory Takt Simulator public showcase screenshot"
                  fill
                  sizes="(max-width: 1024px) 100vw, 50vw"
                  className="object-cover"
                  loading="eager"
                  fetchPriority="high"
                />
              </div>
              <div className="grid gap-0 border-t border-slate-700 md:grid-cols-3">
                {metrics.slice(0, 3).map((metric, index) => (
                  <div className={index < 2 ? "border-slate-700 p-4 md:border-r" : "p-4"} key={metric.id}>
                    <strong className="block text-xl leading-snug text-white">{metric.value}</strong>
                    <span className="text-sm text-slate-300">{metric.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <section className="border-b border-slate-200 bg-white py-12" id="impact">
        <div className="mx-auto max-w-7xl px-5">
          <SectionHeader
            eyebrow="Impact metrics"
            title="Manufacturing outcomes first, tool evidence second."
            summary="The numbers establish the business case. Public projects then show how the same workflow patterns can be demonstrated safely with synthetic data."
          />
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {metrics.map((metric, index) => (
              <Reveal delay={index * 0.04} key={metric.id}>
                <MetricCard metric={metric} />
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-slate-950 py-16 text-white" id="project-map">
        <div className="mx-auto max-w-7xl px-5">
          <SectionHeader
            eyebrow="Full-cycle project map"
            title="From risk review to delivery, audit, and corrective action."
            summary="Felix coordinates and improves execution across all ten stages of the launch-to-delivery chain, with digital tools supporting the work at each stage."
            inverse
          />
          <ProjectMap />
        </div>
      </section>

      <section className="bg-slate-50 py-16" id="case-studies">
        <div className="mx-auto max-w-7xl px-5">
          <SectionHeader
            eyebrow="Featured case studies"
            title="Three manufacturing problems, three evidence-backed improvements."
            summary="Each case keeps the structure simple: problem, Felix's role, methods, actions, outcomes, and public sanitized evidence."
          />
          <div className="grid gap-5 lg:grid-cols-3">
            {caseStudies.map((caseStudy, index) => (
              <Reveal delay={index * 0.06} key={caseStudy.slug}>
                <CaseStudyCard caseStudy={caseStudy} />
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-white py-16">
        <div className="mx-auto max-w-7xl px-5">
          <SectionHeader
            eyebrow="Before / after example"
            title="Manual checking becomes a controlled review workflow."
            summary="The production notice case shows the pattern used across the portfolio: clarify the work, structure the inputs, generate reviewable artifacts, and keep release under human control."
          />
          <BeforeAfterWorkflow before={caseStudies[0].before} after={caseStudies[0].after} />
        </div>
      </section>

      <section className="bg-slate-950 py-16 text-white" id="portfolio-lab">
        <div className="mx-auto max-w-7xl px-5">
          <SectionHeader
            eyebrow="Portfolio Lab"
            title="Public sanitized projects that make the work inspectable."
            summary="These projects demonstrate the same workflow patterns as the case studies — structured notices, takt simulation, and operations dashboards — alongside supporting method and verification tools, all built with synthetic or public-safe data."
            inverse
          />
          <div className="grid gap-5 lg:grid-cols-3">
            {portfolioProjects.map((project, index) => (
              <Reveal delay={index * 0.04} key={project.id}>
                <PortfolioProjectCard project={project} />
              </Reveal>
            ))}
          </div>
          <div className="mt-6 rounded-lg border border-amber-400/60 bg-amber-950/40 p-5 text-amber-100">
            <div className="flex gap-3">
              <ShieldCheck className="mt-1 h-5 w-5 flex-none text-amber-300" aria-hidden="true" />
              <p className="leading-7">
                BOM and material readiness are represented through public synthetic examples in the current v1.
                A dedicated BOM knowledge toolkit remains outside public evidence until a separate data-safety review is complete.
              </p>
            </div>
          </div>
          <div className="mt-4">
            <ConfidentialityNotice compact />
          </div>
        </div>
      </section>

      <section className="bg-slate-50 py-16" id="methodology">
        <div className="mx-auto max-w-7xl px-5">
          <SectionHeader
            eyebrow="Methodology"
            title="A practical operating system for manufacturing improvement."
            summary="The method is not a buzzword list. It connects project control, manufacturing launch support, continuous improvement, and digital workflow tools."
          />
          <MethodologyGrid />
        </div>
      </section>

      <section className="bg-white py-16" id="about">
        <div className="mx-auto grid max-w-7xl gap-8 px-5 lg:grid-cols-[0.8fr_1.2fr]">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-blue-700">About Felix</p>
            <h2 className="mt-3 text-3xl font-semibold text-slate-950">{profile.name}</h2>
            <p className="mt-2 text-slate-600">{profile.currentTitle}</p>
          </div>
          <div className="space-y-6">
            <p className="text-lg leading-8 text-slate-700">{profile.locationContext}</p>
            <p className="leading-7 text-slate-700">
              He coordinates production planning, material readiness, inventory and WIP tracking,
              purchasing follow-up, shipment coordination, and cross-functional factory communication,
              using milestone tracking, PDCA cycles, and Lean Six Sigma thinking to improve project
              visibility and execution efficiency.
            </p>
            <ConfidentialityNotice />
          </div>
        </div>
      </section>

      <CTA />
      </main>
    </>
  );
}

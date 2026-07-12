import { ArrowDown, ArrowUpRight, GitBranch, Mail } from "lucide-react";

import { BeforeAfterWorkflow } from "@/components/BeforeAfterWorkflow";
import { CinematicBackdrop } from "@/components/CinematicBackdrop";
import { CinematicCaseStudy } from "@/components/CinematicCaseStudy";
import { BulletTimeCard, CinematicScene } from "@/components/CinematicScene";
import { ConfidentialityNotice } from "@/components/ConfidentialityNotice";
import { HeroConsole } from "@/components/HeroConsole";
import { MethodologyGrid } from "@/components/MethodologyGrid";
import { MetricCard } from "@/components/MetricCard";
import { PortfolioProjectCard } from "@/components/PortfolioProjectCard";
import { ProjectMap } from "@/components/ProjectMap";
import { SectionHeading } from "@/components/SectionHeading";
import { StatusTicker } from "@/components/StatusTicker";
import { caseStudies } from "@/data/caseStudies";
import { metrics } from "@/data/metrics";
import { portfolioProjects } from "@/data/portfolioProjects";
import { profile } from "@/data/profile";

const primaryProjects = portfolioProjects.filter((project) => project.tier === "Main evidence");
const supportingProjects = portfolioProjects.filter((project) => project.tier !== "Main evidence");

export default function Home() {
  return (
    <main className="cinematic-home">
      <CinematicBackdrop sceneCount={12} />

      <CinematicScene duration="hero" index="01" label="Origin">
        <div className="grid items-center gap-12 lg:grid-cols-[1.02fr_0.98fr] lg:gap-16">
          <div>
            <p className="mono-label text-amber-300">Independent portfolio / {profile.headline}</p>
            <h1 className="mt-6 text-5xl font-semibold leading-none text-slate-100 sm:text-6xl lg:text-7xl">
              Felix Zuo
            </h1>
            <p className="mt-7 max-w-2xl text-3xl font-semibold leading-tight text-slate-100 sm:text-4xl lg:text-5xl">
              {profile.heroTitle.lead} <span className="text-amber-300">{profile.heroTitle.emphasis}</span>
            </p>
            <p className="mt-6 max-w-xl text-lg leading-8 text-slate-400">{profile.summary}</p>

            <div className="mt-9 flex flex-wrap gap-3">
              <a
                className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-amber-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-amber-300 sm:w-auto"
                href="#case-studies"
              >
                View case studies
                <ArrowDown className="h-4 w-4" aria-hidden="true" />
              </a>
              <a
                className="inline-flex w-full items-center justify-center gap-2 rounded-md border hairline bg-[#05080f]/60 px-5 py-3 text-sm font-semibold text-slate-200 backdrop-blur-md transition hover:border-slate-500 hover:text-white sm:w-auto"
                href={`mailto:${profile.email}`}
              >
                <Mail className="h-4 w-4" aria-hidden="true" />
                Email Felix
              </a>
            </div>

            <div className="mt-9 flex flex-wrap gap-2">
              {profile.targetDirections.slice(0, 4).map((direction) => (
                <span className="max-w-full whitespace-normal rounded border hairline bg-[#0a101d]/80 px-3 py-1.5 text-xs text-slate-400" key={direction}>
                  {direction}
                </span>
              ))}
            </div>
          </div>

          <BulletTimeCard direction={-1}>
            <div className="cinematic-instrument">
              <div className="cinematic-instrument-bar">
                <span>Live operations model</span>
                <span>FZ / 001</span>
              </div>
              <HeroConsole />
            </div>
          </BulletTimeCard>
        </div>
      </CinematicScene>

      <div className="cinematic-band">
        <StatusTicker />
      </div>

      <CinematicScene duration="standard" id="impact" index="02" label="Measured impact">
        <SectionHeading
          index="01"
          eyebrow="Impact metrics"
          title="Outcomes first. Tools second."
          summary="Four measured improvements from manufacturing execution work. Every public demo behind them uses sanitized or synthetic data."
        />
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric, index) => (
            <BulletTimeCard className="h-full" direction={index % 2 === 0 ? 1 : -1} key={metric.id}>
              <MetricCard metric={metric} />
            </BulletTimeCard>
          ))}
        </div>
      </CinematicScene>

      <CinematicScene align="right" duration="long" id="project-map" index="03" label="Project cycle">
        <SectionHeading
          index="02"
          eyebrow="Full-cycle project map"
          title="One operating thread from risk review to delivery and corrective action."
          summary="Felix coordinates and improves execution across all ten stages of the launch-to-delivery chain, with digital tools supporting the work at each stage."
        />
        <ProjectMap />
      </CinematicScene>

      {caseStudies.map((caseStudy, index) => (
        <CinematicScene
          align={index % 2 === 1 ? "right" : "left"}
          duration="long"
          id={index === 0 ? "case-studies" : undefined}
          index={String(index + 4).padStart(2, "0")}
          key={caseStudy.slug}
          label={`Case / ${caseStudy.title}`}
        >
          <CinematicCaseStudy caseStudy={caseStudy} index={index} />
        </CinematicScene>
      ))}

      <CinematicScene align="center" duration="long" index="07" label="Control loop">
        <SectionHeading
          index="04"
          eyebrow="The improvement pattern"
          title="Manual checking becomes a controlled review workflow."
          summary="The production notice case shows the pattern used across the portfolio: clarify the work, structure the inputs, generate reviewable artifacts, and keep release under human control."
        />
        <BeforeAfterWorkflow after={caseStudies[0].after} before={caseStudies[0].before} />
      </CinematicScene>

      <CinematicScene duration="long" id="portfolio-lab" index="08" label="Portfolio / core systems">
        <SectionHeading
          index="05"
          eyebrow="Portfolio Lab"
          title="Public systems that make the manufacturing work inspectable."
          summary="The three primary evidence projects cover structured production notices, takt simulation, and supply-production-delivery visibility."
        />
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {primaryProjects.map((project, index) => (
            <BulletTimeCard className="h-full" direction={index % 2 === 0 ? 1 : -1} key={project.id}>
              <PortfolioProjectCard project={project} />
            </BulletTimeCard>
          ))}
        </div>
      </CinematicScene>

      <CinematicScene align="right" duration="extraLong" index="09" label="Portfolio / connected tools">
        <SectionHeading
          index="05.2"
          eyebrow="Connected tools"
          title="Supporting systems extend the same operating logic."
          summary="Operations intelligence, manufacturing data literacy, Six Sigma learning, and long-running agent verification complete the public portfolio without exposing private factory data."
        />
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          {supportingProjects.map((project, index) => (
            <BulletTimeCard className="h-full" direction={index % 2 === 0 ? -1 : 1} key={project.id}>
              <PortfolioProjectCard compact project={project} />
            </BulletTimeCard>
          ))}
        </div>
      </CinematicScene>

      <CinematicScene align="center" duration="long" id="methodology" index="10" label="Operating method">
        <SectionHeading
          index="06"
          eyebrow="Methodology"
          title="A practical operating system for manufacturing improvement."
          summary="A working loop connecting project control, launch support, continuous improvement, and digital workflow tools."
        />
        <MethodologyGrid />
      </CinematicScene>

      <CinematicScene duration="standard" id="about" index="11" label="Profile">
        <div className="grid gap-12 lg:grid-cols-[0.78fr_1.22fr] lg:items-start">
          <div>
            <p className="mono-label text-amber-300">About Felix</p>
            <h2 className="mt-4 text-4xl font-semibold text-slate-100">{profile.name}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-500">{profile.currentTitle}</p>
            <div className="mt-7 flex flex-wrap gap-2">
              {profile.targetDirections.map((direction) => (
                <span className="max-w-full whitespace-normal rounded border hairline bg-[#0a101d]/75 px-3 py-1.5 text-xs text-slate-400" key={direction}>
                  {direction}
                </span>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xl leading-8 text-slate-200">{profile.locationContext}</p>
            <p className="mt-6 leading-7 text-slate-400">
              He coordinates production planning, material readiness, inventory and WIP tracking, purchasing follow-up, shipment coordination, and cross-functional factory communication. Milestone tracking, PDCA cycles, and Lean Six Sigma thinking keep the work visible and measurable.
            </p>
            <div className="mt-7">
              <ConfidentialityNotice compact />
            </div>
            <div className="mt-4 rounded-md border border-amber-400/25 bg-amber-950/25 p-5 backdrop-blur-md">
              <p className="mono-label text-amber-300">BOM toolkit status</p>
              <p className="mt-2.5 text-sm leading-6 text-slate-400">
                BOM and material readiness are represented through public synthetic examples. A dedicated toolkit remains outside public evidence until a separate data-safety review is complete.
              </p>
            </div>
          </div>
        </div>
      </CinematicScene>

      <CinematicScene align="center" duration="standard" id="contact" index="12" label="Contact">
        <div className="mx-auto max-w-3xl text-center">
          <p className="mono-label text-amber-300">Resume / contact</p>
          <h2 className="mt-5 text-4xl font-semibold leading-tight text-slate-100 sm:text-5xl">
            Manufacturing execution, improved with proof.
          </h2>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-slate-400">
            The strongest fit is a role where project coordination, supply-production-delivery visibility, launch readiness, and practical workflow tooling need to work together.
          </p>
          <div className="mt-9 flex flex-wrap justify-center gap-3">
            <a
              className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-amber-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-amber-300 sm:w-auto"
              href={`mailto:${profile.email}`}
            >
              <Mail className="h-4 w-4" aria-hidden="true" />
              Email Felix
            </a>
            <a
              className="inline-flex w-full items-center justify-center gap-2 rounded-md border hairline bg-[#05080f]/60 px-5 py-3 text-sm font-semibold text-slate-200 backdrop-blur-md transition hover:border-slate-500 hover:text-white sm:w-auto"
              href={profile.github}
              rel="noreferrer"
              target="_blank"
            >
              <GitBranch className="h-4 w-4" aria-hidden="true" />
              GitHub portfolio
              <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
            </a>
          </div>
        </div>
      </CinematicScene>
    </main>
  );
}

"use client";

import {
  Activity,
  ArrowLeft,
  ArrowUpRight,
  Boxes,
  ClipboardCheck,
  Factory,
  Gauge,
  GitBranch,
  Mail,
  Network,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import Image from "next/image";
import Link from "next/link";
import { useMemo, useState } from "react";

import { portfolioProjects } from "@/data/portfolioProjects";
import { profile } from "@/data/profile";

import styles from "./JourneyControlDeck.module.css";

type ControlModuleId = "release" | "flow" | "inventory" | "system";

type ControlModule = {
  caseHref?: string;
  eyebrow: string;
  icon: LucideIcon;
  id: ControlModuleId;
  label: string;
  projectId: string;
  signalLabel: string;
  signalValue: string;
  supportingSignal: string;
};

const CONTROL_MODULES: readonly ControlModule[] = [
  {
    caseHref: "/case-studies/production-notice-workflow-standardization",
    eyebrow: "Release control",
    icon: ClipboardCheck,
    id: "release",
    label: "Release",
    projectId: "notice-workbench",
    signalLabel: "Preparation",
    signalValue: "< 1 min",
    supportingSignal: "Human review remains the final gate",
  },
  {
    caseHref: "/case-studies/trial-production-takt-simulation-changeover-improvement",
    eyebrow: "Trial production",
    icon: Gauge,
    id: "flow",
    label: "Flow",
    projectId: "takt-simulator",
    signalLabel: "Adjustment cycle",
    signalValue: "3 d to 1 d",
    supportingSignal: "Bottlenecks tested before physical change",
  },
  {
    caseHref: "/case-studies/supply-production-delivery-operations-visibility",
    eyebrow: "Material readiness",
    icon: Boxes,
    id: "inventory",
    label: "Inventory",
    projectId: "excel-dashboard",
    signalLabel: "Operating span",
    signalValue: "Supply to delivery",
    supportingSignal: "Exceptions stay visible through closure",
  },
  {
    eyebrow: "Connected operations",
    icon: Network,
    id: "system",
    label: "System",
    projectId: "ops-platform",
    signalLabel: "Control model",
    signalValue: "4 linked tools",
    supportingSignal: "Public-safe contracts and synthetic data",
  },
] as const;

const SUPPORT_PROJECT_IDS = ["data-pocket-lab", "six-sigma-study", "hulunguard"] as const;

type JourneyControlDeckProps = {
  active: boolean;
  onReturn: () => void;
};

export function JourneyControlDeck({ active, onReturn }: JourneyControlDeckProps) {
  const [activeModuleId, setActiveModuleId] = useState<ControlModuleId>("release");
  const reduceMotion = useReducedMotion();
  const activeModule =
    CONTROL_MODULES.find((module) => module.id === activeModuleId) ?? CONTROL_MODULES[0];
  const project =
    portfolioProjects.find((candidate) => candidate.id === activeModule.projectId) ??
    portfolioProjects[0];
  const supportProjects = useMemo(
    () =>
      SUPPORT_PROJECT_IDS.map((id) => portfolioProjects.find((project) => project.id === id)).filter(
        (project): project is (typeof portfolioProjects)[number] => Boolean(project),
      ),
    [],
  );

  return (
    <section
      aria-hidden={!active}
      aria-label="Felix Zuo operations control deck"
      className={styles.deck}
      data-active={active || undefined}
      data-testid="journey-control-deck"
    >
      <div aria-hidden="true" className={styles.backdrop}>
        <Image
          alt=""
          className={styles.backdropBase}
          fill
          priority={false}
          sizes="100vw"
          src="/media/control-room-base.jpg"
        />
        <Image
          alt=""
          className={styles.backdropLive}
          fill
          priority={false}
          sizes="100vw"
          src="/media/control-room-live.jpg"
        />
        <span className={styles.backdropShade} />
        <span className={styles.scanLine} />
      </div>

      <div className={styles.shell}>
        <header className={styles.topBar}>
          <div className={styles.identity}>
            <Factory aria-hidden="true" size={18} strokeWidth={1.6} />
            <div>
              <p>Felix Zuo</p>
              <span>Manufacturing Operations Control Deck</span>
            </div>
          </div>

          <div className={styles.systemStatus}>
            <span aria-hidden="true" className={styles.liveDot} />
            <span>Portfolio systems online</span>
            <span>Public-safe evidence</span>
          </div>
        </header>

        <div className={styles.deckBody}>
          <nav aria-label="Operations modules" className={styles.moduleRail}>
            <p>Channels</p>
            {CONTROL_MODULES.map((module, index) => {
              const Icon = module.icon;
              const selected = module.id === activeModule.id;

              return (
                <button
                  aria-pressed={selected}
                  className={selected ? styles.moduleActive : ""}
                  data-testid={`control-module-${module.id}`}
                  key={module.id}
                  onClick={() => setActiveModuleId(module.id)}
                  tabIndex={active ? 0 : -1}
                  title={`Open ${module.label} module`}
                  type="button"
                >
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <Icon aria-hidden="true" size={19} strokeWidth={1.55} />
                  <strong>{module.label}</strong>
                </button>
              );
            })}
          </nav>

          <main className={styles.workspace}>
            <div className={styles.workspaceHeader}>
              <div>
                <p>{activeModule.eyebrow}</p>
                <span>Selected operating channel</span>
              </div>
              <Activity aria-hidden="true" size={19} strokeWidth={1.5} />
            </div>

            <motion.div
              animate={{ opacity: 1, x: 0 }}
              className={styles.projectView}
              initial={reduceMotion ? false : { opacity: 0, x: 18 }}
              key={activeModule.id}
              transition={{ duration: reduceMotion ? 0 : 0.46, ease: [0.22, 1, 0.36, 1] }}
            >
              <section className={styles.projectCopy}>
                <p className={styles.projectTier}>{project.tier}</p>
                <h2>{project.title}</h2>
                <p className={styles.projectDescription}>{project.description}</p>

                <dl className={styles.projectFacts}>
                  <div>
                    <dt>Operational role</dt>
                    <dd>{project.evidenceRole}</dd>
                  </div>
                  <div>
                    <dt>Working stack</dt>
                    <dd>{project.stack}</dd>
                  </div>
                </dl>

                <div className={styles.projectActions}>
                  {activeModule.caseHref && (
                    <Link href={activeModule.caseHref} tabIndex={active ? 0 : -1}>
                      Open case
                      <ArrowUpRight aria-hidden="true" size={15} />
                    </Link>
                  )}
                  {project.liveUrl && (
                    <a
                      href={project.liveUrl}
                      rel="noreferrer"
                      tabIndex={active ? 0 : -1}
                      target="_blank"
                    >
                      Live project
                      <ArrowUpRight aria-hidden="true" size={15} />
                    </a>
                  )}
                  <a
                    href={project.repoUrl}
                    rel="noreferrer"
                    tabIndex={active ? 0 : -1}
                    target="_blank"
                  >
                    Source
                    <GitBranch aria-hidden="true" size={15} />
                  </a>
                </div>
              </section>

              <figure className={styles.projectScreen}>
                {project.image && (
                  <Image
                    alt={project.imageAlt ?? `${project.title} project interface`}
                    fill
                    sizes="(max-width: 900px) 92vw, 48vw"
                    src={project.image}
                  />
                )}
                <figcaption>
                  <span>LIVE / PUBLIC DEMO</span>
                  <span>{activeModule.id.toUpperCase()} CHANNEL</span>
                </figcaption>
              </figure>
            </motion.div>
          </main>

          <aside className={styles.signalPanel}>
            <div className={styles.signalHeading}>
              <ShieldCheck aria-hidden="true" size={18} strokeWidth={1.5} />
              <span>Verified signal</span>
            </div>
            <dl className={styles.primarySignal}>
              <dt>{activeModule.signalLabel}</dt>
              <dd>{activeModule.signalValue}</dd>
            </dl>
            <p>{activeModule.supportingSignal}</p>

            <div className={styles.boundary}>
              <span>Evidence boundary</span>
              <p>{project.dataBoundary}</p>
            </div>

            <div className={styles.maturity}>
              <span>Delivery state</span>
              <p>{project.maturity}</p>
            </div>
          </aside>
        </div>

        <footer className={styles.deckFooter}>
          <button
            className={styles.returnButton}
            onClick={onReturn}
            tabIndex={active ? 0 : -1}
            title="Return to the final factory frame"
            type="button"
          >
            <ArrowLeft aria-hidden="true" size={16} />
            Return to journey
          </button>

          <nav aria-label="Supporting public projects" className={styles.supportLinks}>
            <span>Supporting systems</span>
            {supportProjects.map((supportProject) => (
              <a
                href={supportProject.liveUrl ?? supportProject.repoUrl}
                key={supportProject.id}
                rel="noreferrer"
                tabIndex={active ? 0 : -1}
                target="_blank"
              >
                {supportProject.title}
                <ArrowUpRight aria-hidden="true" size={13} />
              </a>
            ))}
          </nav>

          <div className={styles.contactLinks}>
            <a href={profile.github} rel="noreferrer" tabIndex={active ? 0 : -1} target="_blank">
              <GitBranch aria-hidden="true" size={16} />
              GitHub
            </a>
            <a href={`mailto:${profile.email}`} tabIndex={active ? 0 : -1}>
              <Mail aria-hidden="true" size={16} />
              {profile.email}
            </a>
          </div>
        </footer>
      </div>
    </section>
  );
}

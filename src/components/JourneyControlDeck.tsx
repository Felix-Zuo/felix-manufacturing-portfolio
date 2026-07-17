"use client";

import {
  ArrowLeft,
  ArrowUpRight,
  Boxes,
  ClipboardCheck,
  Gauge,
  GitBranch,
  Mail,
  Network,
  RotateCcw,
  type LucideIcon,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import { portfolioProjects } from "@/data/portfolioProjects";
import { profile } from "@/data/profile";

import type { CinematicAssetKey } from "./cinematicAssets";
import styles from "./JourneyControlDeck.module.css";

type SceneModuleId = "release" | "flow" | "inventory" | "system";
type SceneSelection = SceneModuleId | "contact" | null;

type SceneModule = {
  caseHref?: string;
  hotspotClass: string;
  icon: LucideIcon;
  id: SceneModuleId;
  image?: string;
  imageKey?: CinematicAssetKey;
  label: string;
  metric: string;
  projectId: string;
  screen: "left" | "right";
  video?: boolean;
};

const SCENE_MODULES: readonly SceneModule[] = [
  {
    caseHref: "/case-studies/production-notice-workflow-standardization",
    hotspotClass: "hotspotRelease",
    icon: ClipboardCheck,
    id: "release",
    image: "/evidence/notice-cinematic.png",
    imageKey: "scene-notice",
    label: "Release",
    metric: "< 1 min preparation",
    projectId: "notice-workbench",
    screen: "left",
  },
  {
    caseHref:
      "/case-studies/trial-production-takt-simulation-changeover-improvement",
    hotspotClass: "hotspotFlow",
    icon: Gauge,
    id: "flow",
    label: "Takt",
    metric: "3 d to 1 d adjustment",
    projectId: "takt-simulator",
    screen: "right",
    video: true,
  },
  {
    caseHref: "/case-studies/supply-production-delivery-operations-visibility",
    hotspotClass: "hotspotInventory",
    icon: Boxes,
    id: "inventory",
    image: "/evidence/visibility-cinematic.png",
    imageKey: "scene-visibility",
    label: "Visibility",
    metric: "Supply to delivery",
    projectId: "excel-dashboard",
    screen: "left",
  },
  {
    hotspotClass: "hotspotSystem",
    icon: Network,
    id: "system",
    image: "/evidence/lab-cinematic.png",
    imageKey: "scene-system",
    label: "Systems",
    metric: "7 connected projects",
    projectId: "ops-platform",
    screen: "right",
  },
] as const;

type JourneyControlDeckProps = {
  active: boolean;
  backdropSrc?: string;
  mediaUrls?: Readonly<Partial<Record<CinematicAssetKey, string>>>;
  onReturn: () => void;
  taktVideoSrc?: string;
};

export function JourneyControlDeck({
  active,
  backdropSrc,
  mediaUrls,
  onReturn,
  taktVideoSrc,
}: JourneyControlDeckProps) {
  const [selection, setSelection] = useState<SceneSelection>(null);
  const backdropVideoRef = useRef<HTMLVideoElement>(null);
  const taktVideoRef = useRef<HTMLVideoElement>(null);
  const selectedModule = useMemo(
    () => SCENE_MODULES.find((module) => module.id === selection) ?? null,
    [selection],
  );
  const selectedProject = selectedModule
    ? portfolioProjects.find(
        (candidate) => candidate.id === selectedModule.projectId,
      ) ?? null
    : null;

  useEffect(() => {
    const video = backdropVideoRef.current;
    if (!video || !backdropSrc) return;

    video.src = backdropSrc;
    video.load();
  }, [backdropSrc]);

  useEffect(() => {
    const backdrop = backdropVideoRef.current;
    const takt = taktVideoRef.current;

    if (!active) {
      backdrop?.pause();
      takt?.pause();
      return;
    }

    void backdrop?.play().catch(() => undefined);
    if (selectedModule?.video) {
      void takt?.play().catch(() => undefined);
    } else {
      takt?.pause();
    }
  }, [active, selectedModule]);

  const selectModule = (moduleId: SceneModuleId) => {
    setSelection((current) => (current === moduleId ? null : moduleId));
  };

  return (
    <section
      aria-hidden={!active}
      aria-label="Felix Zuo interactive manufacturing control room"
      className={styles.deck}
      data-active={active || undefined}
      data-contact={selection === "contact" || undefined}
      data-selection={selection ?? undefined}
      data-testid="journey-control-deck"
    >
      <div aria-hidden="true" className={styles.backdrop}>
        <Image
          alt=""
          className={styles.backdropPoster}
          fill
          loading="eager"
          sizes="100vw"
          src="/media/control-room-loop-poster.webp"
        />
        <video
          className={styles.backdropVideo}
          loop
          muted
          playsInline
          poster="/media/control-room-loop-poster.webp"
          preload="auto"
          ref={backdropVideoRef}
          tabIndex={-1}
        />
        <span className={styles.backdropShade} />
      </div>

      <header className={styles.sceneHeader}>
        <div>
          <span>Felix Zuo</span>
          <strong>Manufacturing systems / online</strong>
        </div>
        <button
          aria-label="Return to the factory journey"
          onClick={onReturn}
          tabIndex={active ? 0 : -1}
          title="Return to journey"
          type="button"
        >
          <ArrowLeft aria-hidden="true" size={17} />
          <span>Journey</span>
        </button>
      </header>

      <div className={styles.sceneCanvas}>
        <div
          aria-hidden="true"
          className={`${styles.screenMedia} ${styles.screenLeft}`}
          data-visible={selectedModule?.screen === "left" || undefined}
        >
          {selectedModule?.screen === "left" && selectedModule.image && (
            <Image
              alt=""
              fill
              key={selectedModule.id}
              sizes="18vw"
              src={
                (selectedModule.imageKey && mediaUrls?.[selectedModule.imageKey]) ||
                selectedModule.image
              }
              unoptimized
            />
          )}
          <span />
        </div>

        <div
          aria-hidden="true"
          className={`${styles.screenMedia} ${styles.screenRight}`}
          data-visible={selectedModule?.screen === "right" || undefined}
        >
          {selectedModule?.screen === "right" && selectedModule.video && (
            <video
              autoPlay
              key={selectedModule.id}
              loop
              muted
              playsInline
              preload="auto"
              ref={taktVideoRef}
              src={taktVideoSrc ?? "/evidence/takt-live-workbench.mp4"}
              tabIndex={-1}
            />
          )}
          {selectedModule?.screen === "right" &&
            !selectedModule.video &&
            selectedModule.image && (
              <Image
                alt=""
                fill
                key={selectedModule.id}
                sizes="18vw"
                src={
                  (selectedModule.imageKey && mediaUrls?.[selectedModule.imageKey]) ||
                  selectedModule.image
                }
                unoptimized
              />
            )}
          <span />
        </div>

        {SCENE_MODULES.map((module) => {
          const Icon = module.icon;
          const selected = module.id === selection;

          return (
            <button
              aria-label={`Open ${module.label} project`}
              aria-pressed={selected}
              className={`${styles.hotspot} ${styles[module.hotspotClass]}`}
              data-selected={selected || undefined}
              key={module.id}
              onClick={() => selectModule(module.id)}
              tabIndex={active ? 0 : -1}
              title={module.label}
              type="button"
            >
              <span className={styles.hotspotRing}>
                <Icon aria-hidden="true" size={18} strokeWidth={1.7} />
              </span>
              <strong>{module.label}</strong>
            </button>
          );
        })}

        <button
          aria-label="Open Felix Zuo contact details"
          aria-pressed={selection === "contact"}
          className={`${styles.hotspot} ${styles.hotspotContact}`}
          data-selected={selection === "contact" || undefined}
          onClick={() =>
            setSelection((current) => (current === "contact" ? null : "contact"))
          }
          tabIndex={active ? 0 : -1}
          title="Contact"
          type="button"
        >
          <span className={styles.hotspotRing}>
            <Mail aria-hidden="true" size={18} strokeWidth={1.7} />
          </span>
          <strong>Contact</strong>
        </button>
      </div>

      <div aria-live="polite" className={styles.lowerThird}>
        {selectedProject && selectedModule ? (
          <div className={styles.projectSummary} key={selectedModule.id}>
            <p>
              {selectedModule.label} / <span>{selectedModule.metric}</span>
            </p>
            <h2>{selectedProject.title}</h2>
            <div className={styles.summaryRow}>
              <p>{selectedProject.description}</p>
              <nav aria-label={`${selectedProject.title} links`}>
                {selectedModule.caseHref && (
                  <Link href={selectedModule.caseHref} tabIndex={active ? 0 : -1}>
                    Case study
                    <ArrowUpRight aria-hidden="true" size={15} />
                  </Link>
                )}
                {selectedProject.liveUrl && (
                  <a
                    href={selectedProject.liveUrl}
                    rel="noreferrer"
                    tabIndex={active ? 0 : -1}
                    target="_blank"
                  >
                    Live project
                    <ArrowUpRight aria-hidden="true" size={15} />
                  </a>
                )}
                <a
                  href={selectedProject.repoUrl}
                  rel="noreferrer"
                  tabIndex={active ? 0 : -1}
                  target="_blank"
                >
                  Source
                  <GitBranch aria-hidden="true" size={15} />
                </a>
              </nav>
            </div>
          </div>
        ) : selection === "contact" ? (
          <div className={styles.contactSummary}>
            <p>Manufacturing project coordination</p>
            <h2>Build the next improvement loop.</h2>
            <div>
              <a href={`mailto:${profile.email}`} tabIndex={active ? 0 : -1}>
                <Mail aria-hidden="true" size={17} />
                {profile.email}
              </a>
              <a
                href={profile.github}
                rel="noreferrer"
                tabIndex={active ? 0 : -1}
                target="_blank"
              >
                <GitBranch aria-hidden="true" size={17} />
                GitHub
              </a>
              <button
                onClick={onReturn}
                tabIndex={active ? 0 : -1}
                type="button"
              >
                <RotateCcw aria-hidden="true" size={17} />
                Replay journey
              </button>
            </div>
          </div>
        ) : (
          <div className={styles.roomSummary}>
            <p>Manufacturing operations / selected work</p>
            <h2>Felix Zuo</h2>
            <span>Workflow control, flow simulation, visibility, and connected systems.</span>
          </div>
        )}
      </div>
    </section>
  );
}

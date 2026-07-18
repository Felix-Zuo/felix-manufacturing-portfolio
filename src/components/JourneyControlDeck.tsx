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
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react";

import { portfolioProjects } from "@/data/portfolioProjects";
import { profile } from "@/data/profile";

import type { CinematicAssetKey } from "./cinematicAssets";
import styles from "./JourneyControlDeck.module.css";

type SceneModuleId = "release" | "flow" | "inventory" | "system";
type SceneTargetId = SceneModuleId | "contact";
type SceneSelection = SceneTargetId | null;

type ScenePosition = {
  x: number;
  y: number;
};

type SceneModule = ScenePosition & {
  caseHref?: string;
  icon: LucideIcon;
  id: SceneModuleId;
  image?: string;
  imageKey?: CinematicAssetKey;
  label: string;
  metric: string;
  projectId: string;
  screen: "left" | "right";
  screenPosition: string;
  video?: boolean;
};

const SCENE_MODULES: readonly SceneModule[] = [
  {
    caseHref: "/case-studies/production-notice-workflow-standardization",
    icon: ClipboardCheck,
    id: "release",
    image: "/evidence/notice-cinematic.png",
    imageKey: "scene-notice",
    label: "Release",
    metric: "< 1 min preparation",
    projectId: "notice-workbench",
    screen: "left",
    screenPosition: "0% 50%",
    x: 13.4,
    y: 34.5,
  },
  {
    caseHref:
      "/case-studies/trial-production-takt-simulation-changeover-improvement",
    icon: Gauge,
    id: "flow",
    label: "Takt",
    metric: "3 d to 1 d adjustment",
    projectId: "takt-simulator",
    screen: "right",
    screenPosition: "50% 36%",
    video: true,
    x: 89.5,
    y: 34.5,
  },
  {
    caseHref: "/case-studies/supply-production-delivery-operations-visibility",
    icon: Boxes,
    id: "inventory",
    image: "/evidence/visibility-cinematic.png",
    imageKey: "scene-visibility",
    label: "Visibility",
    metric: "Supply to delivery",
    projectId: "excel-dashboard",
    screen: "left",
    screenPosition: "0% 50%",
    x: 24,
    y: 58.5,
  },
  {
    icon: Network,
    id: "system",
    image: "/evidence/lab-cinematic.png",
    imageKey: "scene-system",
    label: "Systems",
    metric: "7 connected projects",
    projectId: "ops-platform",
    screen: "right",
    screenPosition: "4% 50%",
    x: 76,
    y: 58.5,
  },
] as const;

const CONTACT_POSITION: ScenePosition = { x: 50, y: 51 };
const TARGET_POSITIONS: Readonly<Record<SceneTargetId, ScenePosition>> = {
  contact: CONTACT_POSITION,
  flow: SCENE_MODULES[1],
  inventory: SCENE_MODULES[2],
  release: SCENE_MODULES[0],
  system: SCENE_MODULES[3],
};
const TARGET_ORDER: readonly SceneTargetId[] = [
  "release",
  "inventory",
  "contact",
  "system",
  "flow",
];

type JourneyControlDeckProps = {
  active: boolean;
  backdropSrc?: string;
  mediaUrls?: Readonly<Partial<Record<CinematicAssetKey, string>>>;
  onReturn: () => void;
  taktVideoSrc?: string;
};

function directionalTarget(
  currentId: SceneTargetId,
  key: string,
): SceneTargetId | null {
  const current = TARGET_POSITIONS[currentId];
  const candidates = TARGET_ORDER.flatMap((id) => {
    if (id === currentId) return [];

    const position = TARGET_POSITIONS[id];
    const dx = position.x - current.x;
    const dy = position.y - current.y;
    const valid =
      (key === "ArrowLeft" && dx < 0) ||
      (key === "ArrowRight" && dx > 0) ||
      (key === "ArrowUp" && dy < 0) ||
      (key === "ArrowDown" && dy > 0);

    if (!valid) return [];

    const primary = key === "ArrowLeft" || key === "ArrowRight" ? Math.abs(dx) : Math.abs(dy);
    const cross = key === "ArrowLeft" || key === "ArrowRight" ? Math.abs(dy) : Math.abs(dx);
    return [{ id, score: primary + cross * 1.6 }];
  });

  candidates.sort((a, b) => a.score - b.score);
  return candidates[0]?.id ?? null;
}

export function JourneyControlDeck({
  active,
  backdropSrc,
  mediaUrls,
  onReturn,
  taktVideoSrc,
}: JourneyControlDeckProps) {
  const [selection, setSelection] = useState<SceneSelection>(null);
  const [reducedMotion, setReducedMotion] = useState(false);
  const backdropVideoRef = useRef<HTMLVideoElement>(null);
  const taktVideoRef = useRef<HTMLVideoElement>(null);
  const hotspotRefs = useRef(new Map<SceneTargetId, HTMLButtonElement>());
  const wasActiveRef = useRef(false);
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
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const updatePreference = () => setReducedMotion(query.matches);

    updatePreference();
    query.addEventListener("change", updatePreference);
    return () => query.removeEventListener("change", updatePreference);
  }, []);

  useEffect(() => {
    const enteringDeck = active && !wasActiveRef.current;
    wasActiveRef.current = active;

    if (enteringDeck && window.matchMedia("(max-width: 760px)").matches) {
      setSelection("release");
    }
  }, [active]);

  useEffect(() => {
    const video = backdropVideoRef.current;
    if (!video || !backdropSrc) return;

    video.src = backdropSrc;
    video.load();
  }, [backdropSrc]);

  useEffect(() => {
    const backdrop = backdropVideoRef.current;
    const takt = taktVideoRef.current;

    if (!active || reducedMotion) {
      backdrop?.pause();
    } else {
      void backdrop?.play().catch(() => undefined);
    }

    if (!active || !selectedModule?.video) {
      takt?.pause();
    } else {
      void takt?.play().catch(() => undefined);
    }
  }, [active, reducedMotion, selectedModule]);

  useEffect(() => {
    if (!active) return;

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;

      event.preventDefault();
      if (selection) {
        setSelection(null);
      } else {
        onReturn();
      }
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [active, onReturn, selection]);

  const selectTarget = (targetId: SceneTargetId) => {
    setSelection((current) => (current === targetId ? null : targetId));
  };

  const handleHotspotKeyDown = (
    event: ReactKeyboardEvent<HTMLButtonElement>,
    currentId: SceneTargetId,
  ) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectTarget(currentId);
      return;
    }

    if (event.key === "Home" || event.key === "End") {
      event.preventDefault();
      const targetId = event.key === "Home" ? TARGET_ORDER[0] : TARGET_ORDER.at(-1);
      if (targetId) hotspotRefs.current.get(targetId)?.focus();
      return;
    }

    if (!event.key.startsWith("Arrow")) return;

    const targetId = directionalTarget(currentId, event.key);
    if (!targetId) return;

    event.preventDefault();
    hotspotRefs.current.get(targetId)?.focus();
  };

  const registerHotspot = (
    targetId: SceneTargetId,
    node: HTMLButtonElement | null,
  ) => {
    if (node) {
      hotspotRefs.current.set(targetId, node);
    } else {
      hotspotRefs.current.delete(targetId);
    }
  };

  const SelectedIcon = selectedModule?.icon;
  const selectedScreenStyle = selectedModule
    ? ({
        "--screen-position": selectedModule.screenPosition,
      } as CSSProperties)
    : undefined;

  return (
    <section
      aria-hidden={!active}
      aria-label="Felix Zuo interactive manufacturing control room"
      className={styles.deck}
      data-active={active || undefined}
      data-reduced-motion={reducedMotion || undefined}
      data-selection={selection ?? undefined}
      data-testid="journey-control-deck"
    >
      <div className={styles.sceneFrame}>
        <div aria-hidden="true" className={styles.backdrop}>
          <Image
            alt=""
            className={styles.backdropPoster}
            fill
            loading="eager"
            priority
            sizes="100vw"
            src="/media/control-room-loop-poster.webp?v=10"
            unoptimized
          />
          <video
            className={styles.backdropVideo}
            loop
            muted
            playsInline
            poster="/media/control-room-loop-poster.webp?v=10"
            preload="auto"
            ref={backdropVideoRef}
            tabIndex={-1}
          />
          <span className={styles.backdropShade} />
        </div>

        <div
          aria-hidden="true"
          className={`${styles.screenMedia} ${styles.screenLeft}`}
          data-module={selectedModule?.screen === "left" ? selectedModule.id : undefined}
          data-visible={selectedModule?.screen === "left" || undefined}
          style={selectedModule?.screen === "left" ? selectedScreenStyle : undefined}
        >
          <span className={styles.screenInterior} />
          {selectedModule?.screen === "left" && selectedModule.image && (
            <span className={styles.screenSurface} key={selectedModule.id}>
              <Image
                alt=""
                className={styles.screenAsset}
                data-active="true"
                fill
                sizes="16vw"
                src={
                  (selectedModule.imageKey && mediaUrls?.[selectedModule.imageKey]) ||
                  selectedModule.image
                }
                unoptimized
              />
            </span>
          )}
          {selectedModule?.screen === "left" && (
            <span className={styles.screenStatus} key={`left-status-${selectedModule.id}`}>
              <span>{selectedModule.label}</span>
              <strong>{selectedModule.metric}</strong>
            </span>
          )}
          <span
            className={styles.screenEffect}
            key={`left-effect-${selectedModule?.screen === "left" ? selectedModule.id : "idle"}`}
          />
        </div>

        <div
          aria-hidden="true"
          className={`${styles.screenMedia} ${styles.screenRight}`}
          data-module={selectedModule?.screen === "right" ? selectedModule.id : undefined}
          data-live={selectedModule?.video || undefined}
          data-visible={selectedModule?.screen === "right" || undefined}
          style={selectedModule?.screen === "right" ? selectedScreenStyle : undefined}
        >
          <span className={styles.screenInterior} />
          <span className={styles.screenSurface}>
            <video
              className={styles.screenAsset}
              data-active={selectedModule?.video || undefined}
              loop
              muted
              onCanPlay={(event) => {
                if (active && selection === "flow") {
                  void event.currentTarget.play().catch(() => undefined);
                }
              }}
              playsInline
              poster="/evidence/takt-cinematic.png"
              preload="auto"
              ref={taktVideoRef}
              src={taktVideoSrc ?? "/evidence/takt-live-workbench.mp4"}
              tabIndex={-1}
            />
            {selectedModule?.screen === "right" &&
              !selectedModule.video &&
              selectedModule.image && (
              <Image
                alt=""
                className={styles.screenAsset}
                data-active="true"
                fill
                key={selectedModule.id}
                sizes="16vw"
                src={
                  (selectedModule.imageKey && mediaUrls?.[selectedModule.imageKey]) ||
                  selectedModule.image
                }
                unoptimized
              />
              )}
          </span>
          {selectedModule?.screen === "right" && (
            <span className={styles.screenStatus} key={`right-status-${selectedModule.id}`}>
              <span>{selectedModule.label}</span>
              <strong>{selectedModule.video ? "Live simulation" : selectedModule.metric}</strong>
            </span>
          )}
          <span
            className={styles.screenEffect}
            key={`right-effect-${selectedModule?.screen === "right" ? selectedModule.id : "idle"}`}
          />
        </div>

        {SCENE_MODULES.map((module) => {
          const Icon = module.icon;
          const selected = module.id === selection;
          const hotspotStyle = {
            "--hotspot-x": `${module.x}%`,
            "--hotspot-y": `${module.y}%`,
          } as CSSProperties;

          return (
            <button
              aria-controls="journey-control-deck-detail"
              aria-label={`Open ${module.label} project`}
              aria-pressed={selected}
              className={styles.hotspot}
              data-screen={module.screen}
              data-selected={selected || undefined}
              key={module.id}
              onClick={() => selectTarget(module.id)}
              onKeyDown={(event) => handleHotspotKeyDown(event, module.id)}
              ref={(node) => registerHotspot(module.id, node)}
              style={hotspotStyle}
              tabIndex={active ? 0 : -1}
              title={module.label}
              type="button"
            >
              <span className={styles.hotspotRing}>
                <Icon aria-hidden="true" size={17} strokeWidth={1.7} />
              </span>
              <strong className={styles.hotspotLabel}>{module.label}</strong>
            </button>
          );
        })}

        <button
          aria-controls="journey-control-deck-detail"
          aria-label="Open Felix Zuo contact details"
          aria-pressed={selection === "contact"}
          className={styles.hotspot}
          data-contact="true"
          data-selected={selection === "contact" || undefined}
          onClick={() => selectTarget("contact")}
          onKeyDown={(event) => handleHotspotKeyDown(event, "contact")}
          ref={(node) => registerHotspot("contact", node)}
          style={
            {
              "--hotspot-x": `${CONTACT_POSITION.x}%`,
              "--hotspot-y": `${CONTACT_POSITION.y}%`,
            } as CSSProperties
          }
          tabIndex={active ? 0 : -1}
          title="Contact"
          type="button"
        >
          <span className={styles.hotspotRing}>
            <Mail aria-hidden="true" size={17} strokeWidth={1.7} />
          </span>
          <strong className={styles.hotspotLabel}>Contact</strong>
        </button>
      </div>

      <header className={styles.sceneHeader}>
        <div className={styles.identity}>
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

      {selection && (
        <div
          aria-live="polite"
          className={styles.lowerThird}
          id="journey-control-deck-detail"
          key={selection}
        >
          {selectedProject && selectedModule && SelectedIcon ? (
            <div className={styles.projectSummary}>
              <p className={styles.eyebrow}>
                <SelectedIcon aria-hidden="true" size={15} strokeWidth={1.8} />
                <span>{selectedModule.label}</span>
                <strong>{selectedModule.metric}</strong>
              </p>
              <h2>{selectedProject.title}</h2>
              <div className={styles.summaryRow}>
                <p className={styles.summaryCopy}>{selectedProject.description}</p>
                <nav aria-label={`${selectedProject.title} links`}>
                  {selectedModule.caseHref && (
                    <Link
                      href={selectedModule.caseHref}
                      tabIndex={active ? 0 : -1}
                    >
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
          ) : (
            <div className={styles.contactSummary}>
              <p className={styles.eyebrow}>
                <Mail aria-hidden="true" size={15} strokeWidth={1.8} />
                <span>Contact</span>
                <strong>Manufacturing project coordination</strong>
              </p>
              <h2>Build the next improvement loop.</h2>
              <div className={styles.summaryRow}>
                <p className={styles.summaryCopy}>
                  Workflow control, flow simulation, operational visibility, and
                  connected production systems.
                </p>
                <nav aria-label="Contact links">
                  <a href={`mailto:${profile.email}`} tabIndex={active ? 0 : -1}>
                    <Mail aria-hidden="true" size={15} />
                    Email
                  </a>
                  <a
                    href={profile.github}
                    rel="noreferrer"
                    tabIndex={active ? 0 : -1}
                    target="_blank"
                  >
                    <GitBranch aria-hidden="true" size={15} />
                    GitHub
                  </a>
                  <button
                    onClick={onReturn}
                    tabIndex={active ? 0 : -1}
                    type="button"
                  >
                    <RotateCcw aria-hidden="true" size={15} />
                    Replay
                  </button>
                </nav>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

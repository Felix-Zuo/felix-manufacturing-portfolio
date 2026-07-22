"use client";

import {
  ArrowLeft,
  Boxes,
  CalendarRange,
  Crosshair,
  GraduationCap,
  Mail,
  PackageSearch,
  RotateCcw,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";
import Image from "next/image";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent as ReactKeyboardEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";

import {
  factoryProjectAtlas,
  type FactoryProjectId,
} from "@/data/factoryProjectAtlas";
import { profile } from "@/data/profile";

import styles from "./JourneyControlDeck.module.css";

type ScenePosition = {
  x: number;
  y: number;
};

const ZONE_ICONS: Readonly<Record<FactoryProjectId, LucideIcon>> = {
  planning: CalendarRange,
  procurement: PackageSearch,
  resilience: ShieldCheck,
  skills: GraduationCap,
  wip: Boxes,
};

const TARGET_ORDER = factoryProjectAtlas.map(
  (project) => project.id,
) as readonly FactoryProjectId[];

function targetPosition(targetId: FactoryProjectId): ScenePosition {
  const project = factoryProjectAtlas.find(({ id }) => id === targetId);
  if (!project) {
    throw new Error(`Unknown factory project target: ${targetId}`);
  }

  return project.scene;
}

type JourneyControlDeckProps = {
  active: boolean;
  backdropSrc?: string;
  onReturn: () => void;
  visible: boolean;
};

function directionalTarget(
  currentId: FactoryProjectId,
  key: string,
): FactoryProjectId | null {
  const current = targetPosition(currentId);
  const candidates = TARGET_ORDER.flatMap((id) => {
    if (id === currentId) return [];

    const position = targetPosition(id);
    const dx = position.x - current.x;
    const dy = position.y - current.y;
    const valid =
      (key === "ArrowLeft" && dx < 0) ||
      (key === "ArrowRight" && dx > 0) ||
      (key === "ArrowUp" && dy < 0) ||
      (key === "ArrowDown" && dy > 0);

    if (!valid) return [];

    const horizontal = key === "ArrowLeft" || key === "ArrowRight";
    const primary = horizontal ? Math.abs(dx) : Math.abs(dy);
    const cross = horizontal ? Math.abs(dy) : Math.abs(dx);
    return [{ id, score: primary + cross * 1.6 }];
  });

  candidates.sort((a, b) => a.score - b.score);
  return candidates[0]?.id ?? null;
}

export function JourneyControlDeck({
  active,
  backdropSrc,
  onReturn,
  visible,
}: JourneyControlDeckProps) {
  const [selection, setSelection] = useState<FactoryProjectId | null>(null);
  const [focusChanging, setFocusChanging] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const backdropVideoRef = useRef<HTMLVideoElement>(null);
  const deckRef = useRef<HTMLElement>(null);
  const focusTimerRef = useRef<number | null>(null);
  const pointerFrameRef = useRef<number | null>(null);
  const hotspotRefs = useRef(new Map<FactoryProjectId, HTMLButtonElement>());
  const wasActiveRef = useRef(false);

  const selectedProject = useMemo(
    () => factoryProjectAtlas.find((project) => project.id === selection) ?? null,
    [selection],
  );
  const SelectedIcon = selectedProject ? ZONE_ICONS[selectedProject.id] : null;

  const deckStyle = {
    "--scene-scale": selectedProject ? "1.048" : "1",
    "--scene-shift-x": selectedProject
      ? `${((50 - selectedProject.scene.x) * 0.045).toFixed(2)}vw`
      : "0vw",
    "--scene-shift-y": selectedProject
      ? `${((50 - selectedProject.scene.y) * 0.035).toFixed(2)}vh`
      : "0vh",
  } as CSSProperties;

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

    if (enteringDeck) {
      setSelection(null);
      setFocusChanging(false);
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

    if (!visible || reducedMotion) {
      backdrop?.pause();
    } else {
      void backdrop?.play().catch(() => undefined);
    }
  }, [reducedMotion, visible]);

  useEffect(() => {
    return () => {
      if (focusTimerRef.current !== null) {
        window.clearTimeout(focusTimerRef.current);
      }
      if (pointerFrameRef.current !== null) {
        window.cancelAnimationFrame(pointerFrameRef.current);
      }
    };
  }, []);

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

  const selectTarget = (targetId: FactoryProjectId) => {
    if (targetId === selection) return;

    if (focusTimerRef.current !== null) {
      window.clearTimeout(focusTimerRef.current);
    }
    setFocusChanging(true);
    setSelection(targetId);
    focusTimerRef.current = window.setTimeout(() => {
      setFocusChanging(false);
      focusTimerRef.current = null;
    }, reducedMotion ? 0 : 760);
  };

  const clearSelection = () => {
    if (!selection) return;
    setFocusChanging(true);
    setSelection(null);
    if (focusTimerRef.current !== null) {
      window.clearTimeout(focusTimerRef.current);
    }
    focusTimerRef.current = window.setTimeout(() => {
      setFocusChanging(false);
      focusTimerRef.current = null;
    }, reducedMotion ? 0 : 640);
  };

  const handleHotspotKeyDown = (
    event: ReactKeyboardEvent<HTMLButtonElement>,
    currentId: FactoryProjectId,
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
    targetId: FactoryProjectId,
    node: HTMLButtonElement | null,
  ) => {
    if (node) {
      hotspotRefs.current.set(targetId, node);
    } else {
      hotspotRefs.current.delete(targetId);
    }
  };

  const handlePointerMove = (event: ReactPointerEvent<HTMLElement>) => {
    if (event.pointerType === "touch") return;
    const deck = deckRef.current;
    if (!deck) return;

    const x = event.clientX;
    const y = event.clientY;
    const target = event.target as HTMLElement;
    const interactive = Boolean(target.closest("a, button, [role='button']"));
    if (pointerFrameRef.current !== null) {
      window.cancelAnimationFrame(pointerFrameRef.current);
    }
    pointerFrameRef.current = window.requestAnimationFrame(() => {
      deck.style.setProperty("--pointer-x", `${x}px`);
      deck.style.setProperty("--pointer-y", `${y}px`);
      deck.toggleAttribute("data-pointer-interactive", interactive);
      pointerFrameRef.current = null;
    });
  };

  const handlePointerLeave = () => {
    deckRef.current?.removeAttribute("data-pointer-interactive");
  };

  return (
    <section
      aria-hidden={!active}
      aria-label="Felix Zuo factory project atlas"
      className={styles.deck}
      data-active={active || undefined}
      data-focus-changing={focusChanging || undefined}
      data-reduced-motion={reducedMotion || undefined}
      data-selection={selection ?? undefined}
      data-visible={visible || undefined}
      onPointerLeave={handlePointerLeave}
      onPointerMove={handlePointerMove}
      ref={deckRef}
      style={deckStyle}
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
            onCanPlay={(event) => {
              if (visible && !reducedMotion) {
                void event.currentTarget.play().catch(() => undefined);
              }
            }}
            playsInline
            poster="/media/control-room-loop-poster.webp?v=10"
            preload="auto"
            ref={backdropVideoRef}
            tabIndex={-1}
          />
          <span className={styles.backdropShade} />
        </div>

        {factoryProjectAtlas.map((project) => {
          const Icon = ZONE_ICONS[project.id];
          const selected = project.id === selection;
          const hotspotStyle = {
            "--hotspot-x": `${project.scene.x}%`,
            "--hotspot-y": `${project.scene.y}%`,
          } as CSSProperties;

          return (
            <button
              aria-controls="factory-project-briefing"
              aria-label={`Inspect ${project.title}`}
              aria-pressed={selected}
              className={styles.hotspot}
              data-label-side={project.scene.labelSide}
              data-selected={selected || undefined}
              key={project.id}
              onClick={() => selectTarget(project.id)}
              onKeyDown={(event) => handleHotspotKeyDown(event, project.id)}
              ref={(node) => registerHotspot(project.id, node)}
              style={hotspotStyle}
              tabIndex={active ? 0 : -1}
              title={project.title}
              type="button"
            >
              <span className={styles.hotspotRing}>
                <Icon aria-hidden="true" size={17} strokeWidth={1.7} />
              </span>
              <span className={styles.hotspotLabel}>
                <small>{project.index}</small>
                <strong>{project.shortLabel}</strong>
                <span>{project.scope}</span>
              </span>
            </button>
          );
        })}
      </div>

      <header className={styles.sceneHeader}>
        <div className={styles.identity}>
          <span>Felix Zuo</span>
          <strong>Factory project atlas / 05 systems online</strong>
        </div>
        <div className={styles.headerActions}>
          <a
            aria-label={`Email ${profile.email}`}
            href={`mailto:${profile.email}`}
            tabIndex={active ? 0 : -1}
            title="Email Felix Zuo"
          >
            <Mail aria-hidden="true" size={16} />
          </a>
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
        </div>
      </header>

      <div aria-live="polite" className={styles.zoneGuidance}>
        <span>{selectedProject ? `${selectedProject.index} / 05` : "05 / operational systems"}</span>
        <strong>{selectedProject ? selectedProject.label : "Select a factory signal"}</strong>
      </div>

      {selectedProject && SelectedIcon ? (
        <div
          aria-live="polite"
          className={styles.lowerThird}
          id="factory-project-briefing"
          key={selectedProject.id}
        >
          <div className={styles.projectSummary}>
            <p className={styles.eyebrow}>
              <SelectedIcon aria-hidden="true" size={15} strokeWidth={1.8} />
              <span>{selectedProject.index} / {selectedProject.label}</span>
              <strong>{selectedProject.scope}</strong>
            </p>
            <div className={styles.briefingGrid}>
              <div>
                <h2>{selectedProject.title}</h2>
                <p className={styles.summaryCopy}>{selectedProject.description}</p>
              </div>
              <div className={styles.metricBlock}>
                <strong>{selectedProject.metric}</strong>
                <span>{selectedProject.metricLabel}</span>
              </div>
            </div>
            <div className={styles.briefingFooter}>
              <div aria-label="Project signals" className={styles.signalList}>
                {selectedProject.signals.map((signal) => (
                  <span key={signal}>{signal}</span>
                ))}
              </div>
              <button
                aria-label="Return to all factory project zones"
                onClick={clearSelection}
                tabIndex={active ? 0 : -1}
                type="button"
              >
                <RotateCcw aria-hidden="true" size={14} />
                All zones
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div
          aria-live="polite"
          className={styles.lowerThird}
          id="factory-project-briefing"
        >
          <div className={styles.overviewSummary}>
            <p className={styles.eyebrow}>
              <Crosshair aria-hidden="true" size={15} strokeWidth={1.8} />
              <span>Factory project atlas</span>
              <strong>Five projects / one operating model</strong>
            </p>
            <div className={styles.briefingGrid}>
              <div>
                <h2>Five systems. One operating rhythm.</h2>
                <p className={styles.summaryCopy}>
                  Follow the operating chain from demand and WIP through procurement,
                  supplier resilience, and frontline capability.
                </p>
              </div>
              <div className={styles.metricBlock}>
                <strong>05</strong>
                <span>selectable factory zones</span>
              </div>
            </div>
            <div aria-label="Factory project map" className={styles.signalList}>
              {factoryProjectAtlas.map((project) => (
                <span key={project.id}>{project.index} / {project.shortLabel}</span>
              ))}
            </div>
          </div>
        </div>
      )}

      <nav aria-label="Factory project zones" className={styles.atlasRail}>
        <div className={styles.railLead}>
          <span>Project atlas</span>
          <strong>{selectedProject?.shortLabel ?? "05 factory systems"}</strong>
        </div>
        <ol>
          {factoryProjectAtlas.map((project) => {
            const Icon = ZONE_ICONS[project.id];
            const selected = project.id === selection;
            return (
              <li key={project.id}>
                <button
                  aria-label={`Select ${project.title}`}
                  aria-pressed={selected}
                  data-selected={selected || undefined}
                  onClick={() => selectTarget(project.id)}
                  tabIndex={active ? 0 : -1}
                  type="button"
                >
                  <Icon aria-hidden="true" size={14} strokeWidth={1.7} />
                  <span>{project.index}</span>
                  <strong>{project.shortLabel}</strong>
                </button>
              </li>
            );
          })}
        </ol>
        <div className={styles.railHint}>
          <Crosshair aria-hidden="true" size={14} />
          <span>{selectedProject ? "Choose another" : "Select a signal"}</span>
        </div>
      </nav>

      <span aria-hidden="true" className={styles.pointerFollower}>
        <Crosshair size={18} strokeWidth={1.5} />
      </span>
      <span aria-hidden="true" className={styles.focusVeil} />
    </section>
  );
}

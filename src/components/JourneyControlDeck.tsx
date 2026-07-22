"use client";

import {
  ArrowLeft,
  ArrowUpRight,
  Boxes,
  CalendarRange,
  Crosshair,
  GraduationCap,
  Languages,
  Mail,
  PackageSearch,
  RotateCcw,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import {
  useEffect,
  useCallback,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
  type CSSProperties,
  type KeyboardEvent as ReactKeyboardEvent,
  type MouseEvent as ReactMouseEvent,
} from "react";

import {
  factoryProjectAtlas,
  type FactoryProjectId,
  type FactoryProjectLocale,
  type FactoryProjectText,
} from "@/data/factoryProjectAtlas";
import { profile } from "@/data/profile";

import { PrecisionPointer, usePrecisionPointer } from "./PrecisionPointer";
import styles from "./JourneyControlDeck.module.css";

const LOCALE_STORAGE_KEY = "felix-portfolio-locale";
const LOCALE_CHANGE_EVENT = "felix-portfolio-locale-change";

const UI_COPY = {
  en: {
    atlasAria: "Felix Zuo factory project atlas",
    inspect: "Inspect",
    identityStatus: "Factory project atlas / 05 systems online",
    language: "Language",
    switchEnglish: "Switch to English",
    switchChinese: "Switch to Chinese",
    email: "Email Felix Zuo",
    returnAria: "Return to the factory journey",
    returnTitle: "Return to journey",
    journey: "Journey",
    operationalSystems: "05 / operational systems",
    selectSignal: "Select a factory signal",
    projectSignals: "Project signals",
    allZonesAria: "Return to all factory project zones",
    allZones: "All zones",
    openFullCase: "Open full case",
    openFullCaseAria: "Open full case study",
    atlas: "Factory project atlas",
    operatingModel: "Five projects / one operating model",
    overviewTitle: "Five systems. One operating rhythm.",
    overviewCopy:
      "Follow the operating chain from demand and WIP through procurement, supplier resilience, and frontline capability.",
    selectableZones: "selectable factory zones",
    projectMap: "Factory project map",
    zonesAria: "Factory project zones",
    projectAtlas: "Project atlas",
    factorySystems: "05 factory systems",
    select: "Select",
    chooseAnother: "Choose another",
    selectHint: "Select a signal",
    resetFocus: "Click the scene to return to all zones",
    briefingAria: "Selected factory project briefing",
  },
  zh: {
    resetFocus: "点击场景空白处返回全部区域",
    atlasAria: "Felix Zuo 工厂项目总览",
    inspect: "查看",
    identityStatus: "工厂项目总览 / 05 个系统在线",
    language: "语言",
    switchEnglish: "切换至英文",
    switchChinese: "切换至中文",
    email: "给 Felix Zuo 发送邮件",
    returnAria: "返回工厂旅程",
    returnTitle: "返回旅程",
    journey: "旅程",
    operationalSystems: "05 / 运营系统",
    selectSignal: "选择一个工厂信号",
    projectSignals: "项目信号",
    allZonesAria: "返回全部工厂项目区域",
    allZones: "全部区域",
    openFullCase: "查看完整案例",
    openFullCaseAria: "查看完整项目案例",
    atlas: "工厂项目总览",
    operatingModel: "五个项目 / 一套运营模型",
    overviewTitle: "五套系统，一种运营节奏。",
    overviewCopy:
      "沿着需求、在制品、采购、供应韧性与一线能力，查看相互连接的工厂运营链。",
    selectableZones: "个可选工厂区域",
    projectMap: "工厂项目地图",
    zonesAria: "工厂项目区域",
    projectAtlas: "项目总览",
    factorySystems: "05 个工厂系统",
    select: "选择",
    chooseAnother: "选择其他项目",
    selectHint: "选择一个信号",
    briefingAria: "已选工厂项目讲解",
  },
} as const;

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

function localize(value: FactoryProjectText, locale: FactoryProjectLocale) {
  return value[locale];
}

function getLocaleSnapshot(): FactoryProjectLocale {
  const storedLocale = window.localStorage.getItem(LOCALE_STORAGE_KEY);
  return storedLocale === "zh" ? "zh" : "en";
}

function getServerLocaleSnapshot(): FactoryProjectLocale {
  return "en";
}

function subscribeToLocale(onStoreChange: () => void) {
  const handleChange = () => onStoreChange();
  window.addEventListener("storage", handleChange);
  window.addEventListener(LOCALE_CHANGE_EVENT, handleChange);
  return () => {
    window.removeEventListener("storage", handleChange);
    window.removeEventListener(LOCALE_CHANGE_EVENT, handleChange);
  };
}

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
  onSelectedProjectChange?: (projectId: FactoryProjectId | null) => void;
  onReturn: () => void;
  selectedProjectId?: FactoryProjectId | null;
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
  onSelectedProjectChange,
  onReturn,
  selectedProjectId,
  visible,
}: JourneyControlDeckProps) {
  const locale = useSyncExternalStore(
    subscribeToLocale,
    getLocaleSnapshot,
    getServerLocaleSnapshot,
  );
  const [internalSelection, setInternalSelection] =
    useState<FactoryProjectId | null>(null);
  const selection =
    selectedProjectId === undefined ? internalSelection : selectedProjectId;
  const [focusChanging, setFocusChanging] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const backdropVideoRef = useRef<HTMLVideoElement>(null);
  const briefingRef = useRef<HTMLDivElement>(null);
  const deckRef = useRef<HTMLElement>(null);
  const focusTimerRef = useRef<number | null>(null);
  const hotspotRefs = useRef(new Map<FactoryProjectId, HTMLButtonElement>());
  const wasActiveRef = useRef(false);

  const selectedProject = useMemo(
    () => factoryProjectAtlas.find((project) => project.id === selection) ?? null,
    [selection],
  );
  const copy = UI_COPY[locale];
  const SelectedIcon = selectedProject ? ZONE_ICONS[selectedProject.id] : null;

  const commitSelection = useCallback(
    (nextSelection: FactoryProjectId | null) => {
      if (selectedProjectId === undefined) {
        setInternalSelection(nextSelection);
      }
      onSelectedProjectChange?.(nextSelection);
    },
    [onSelectedProjectChange, selectedProjectId],
  );

  const deckStyle = {
    "--scene-scale": selectedProject ? "1.09" : "1",
    "--scene-scale-mobile": selectedProject ? "1.055" : "1",
    "--scene-shift-x": selectedProject
      ? `${((50 - selectedProject.scene.x) * 0.09).toFixed(2)}vw`
      : "0vw",
    "--scene-shift-y": selectedProject
      ? `${((50 - selectedProject.scene.y) * 0.065).toFixed(2)}vh`
      : "0vh",
    "--scene-shift-x-mobile": selectedProject
      ? `${((50 - selectedProject.scene.x) * 0.035).toFixed(2)}vw`
      : "0vw",
    "--scene-shift-y-mobile": selectedProject
      ? `${((50 - selectedProject.scene.y) * 0.018).toFixed(2)}vh`
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
    document.documentElement.lang = locale === "zh" ? "zh-CN" : "en";
  }, [locale]);

  useEffect(() => {
    const enteringDeck = active && !wasActiveRef.current;
    wasActiveRef.current = active;

    if (!enteringDeck) return;

    const resetFrame = window.requestAnimationFrame(() => {
      if (selectedProjectId === undefined) {
        setInternalSelection(null);
      }
      setFocusChanging(false);
    });

    return () => window.cancelAnimationFrame(resetFrame);
  }, [active, selectedProjectId]);

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
    };
  }, []);

  useEffect(() => {
    if (!active) return;

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;

      event.preventDefault();
      if (selection) {
        const previousSelection = selection;
        commitSelection(null);
        window.requestAnimationFrame(() => {
          hotspotRefs.current.get(previousSelection)?.focus();
        });
      } else {
        onReturn();
      }
    };

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [active, commitSelection, onReturn, selection]);

  const selectTarget = (targetId: FactoryProjectId) => {
    if (targetId === selection) {
      briefingRef.current?.focus({ preventScroll: true });
      return;
    }

    if (focusTimerRef.current !== null) {
      window.clearTimeout(focusTimerRef.current);
    }
    setFocusChanging(true);
    commitSelection(targetId);
    focusTimerRef.current = window.setTimeout(() => {
      setFocusChanging(false);
      briefingRef.current?.focus({ preventScroll: true });
      focusTimerRef.current = null;
    }, reducedMotion ? 0 : 760);
  };

  const clearSelection = () => {
    if (!selection) return;
    const previousSelection = selection;
    setFocusChanging(true);
    commitSelection(null);
    if (focusTimerRef.current !== null) {
      window.clearTimeout(focusTimerRef.current);
    }
    focusTimerRef.current = window.setTimeout(() => {
      setFocusChanging(false);
      hotspotRefs.current.get(previousSelection)?.focus();
      focusTimerRef.current = null;
    }, reducedMotion ? 0 : 640);
  };

  const handleSceneClick = (event: ReactMouseEvent<HTMLDivElement>) => {
    if (!selection) return;
    if ((event.target as HTMLElement).closest("button, a")) return;
    clearSelection();
  };

  const handleBriefingKeyDown = (
    event: ReactKeyboardEvent<HTMLDivElement>,
  ) => {
    if (!selection || event.target !== event.currentTarget) return;

    if (event.key === "Home" || event.key === "End") {
      event.preventDefault();
      const targetId = event.key === "Home" ? TARGET_ORDER[0] : TARGET_ORDER.at(-1);
      if (targetId) selectTarget(targetId);
      return;
    }

    if (!event.key.startsWith("Arrow")) return;
    const targetId = directionalTarget(selection, event.key);
    if (!targetId) return;

    event.preventDefault();
    selectTarget(targetId);
  };

  const changeLocale = (nextLocale: FactoryProjectLocale) => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, nextLocale);
    window.dispatchEvent(new Event(LOCALE_CHANGE_EVENT));
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

  const { handlePointerLeave, handlePointerMove } = usePrecisionPointer(deckRef, {
    enabled: active,
  });

  return (
    <section
      aria-hidden={!active}
      aria-label={copy.atlasAria}
      className={styles.deck}
      data-active={active || undefined}
      data-focus-changing={focusChanging || undefined}
      data-precision-pointer=""
      data-reduced-motion={reducedMotion || undefined}
      data-selection={selection ?? undefined}
      data-visible={visible || undefined}
      onPointerLeave={handlePointerLeave}
      onPointerMove={handlePointerMove}
      ref={deckRef}
      style={deckStyle}
    >
      <div className={styles.sceneFrame} onClick={handleSceneClick}>
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
              aria-label={`${copy.inspect} ${localize(project.title, locale)}`}
              aria-pressed={selected}
              className={styles.hotspot}
              data-label-side={project.scene.labelSide}
              data-pointer-role="focus"
              data-selected={selected || undefined}
              key={project.id}
              onClick={() => selectTarget(project.id)}
              onKeyDown={(event) => handleHotspotKeyDown(event, project.id)}
              ref={(node) => registerHotspot(project.id, node)}
              style={hotspotStyle}
              tabIndex={active ? 0 : -1}
              title={localize(project.title, locale)}
              type="button"
            >
              <span className={styles.hotspotRing}>
                <Icon aria-hidden="true" size={17} strokeWidth={1.7} />
              </span>
              <span className={styles.hotspotLabel}>
                <small>{project.index}</small>
                <strong>{localize(project.shortLabel, locale)}</strong>
                <span>{localize(project.scope, locale)}</span>
              </span>
            </button>
          );
        })}
      </div>

      <header className={styles.sceneHeader}>
        <div className={styles.identity}>
          <span>Felix Zuo</span>
          <strong>{copy.identityStatus}</strong>
        </div>
        <div className={styles.headerActions}>
          <div
            aria-label={copy.language}
            className={styles.localeSwitch}
            role="group"
          >
            <Languages aria-hidden="true" size={15} />
            <button
              aria-label={copy.switchEnglish}
              aria-pressed={locale === "en"}
              data-active={locale === "en" || undefined}
              data-pointer-role="action"
              onClick={() => changeLocale("en")}
              tabIndex={active ? 0 : -1}
              type="button"
            >
              EN
            </button>
            <button
              aria-label={copy.switchChinese}
              aria-pressed={locale === "zh"}
              data-active={locale === "zh" || undefined}
              data-pointer-role="action"
              onClick={() => changeLocale("zh")}
              tabIndex={active ? 0 : -1}
              type="button"
            >
              中文
            </button>
          </div>
          <a
            aria-label={copy.email}
            data-pointer-role="action"
            href={`mailto:${profile.email}`}
            tabIndex={active ? 0 : -1}
            title={copy.email}
          >
            <Mail aria-hidden="true" size={16} />
          </a>
          <button
            aria-label={copy.returnAria}
            data-pointer-role="action"
            onClick={onReturn}
            tabIndex={active ? 0 : -1}
            title={copy.returnTitle}
            type="button"
          >
            <ArrowLeft aria-hidden="true" size={17} />
            <span>{copy.journey}</span>
          </button>
        </div>
      </header>

      <div aria-live="polite" className={styles.zoneGuidance}>
        <span>{selectedProject ? `${selectedProject.index} / 05` : copy.operationalSystems}</span>
        <strong>
          {selectedProject
            ? localize(selectedProject.label, locale)
            : copy.selectSignal}
        </strong>
      </div>

      {selectedProject && SelectedIcon ? (
        <div
          aria-live="polite"
          aria-label={copy.briefingAria}
          className={styles.lowerThird}
          id="factory-project-briefing"
          key={selectedProject.id}
          onKeyDown={handleBriefingKeyDown}
          ref={briefingRef}
          role="region"
          tabIndex={active ? -1 : undefined}
        >
          <div className={styles.projectSummary}>
            <p className={styles.eyebrow}>
              <SelectedIcon aria-hidden="true" size={15} strokeWidth={1.8} />
              <span>
                {selectedProject.index} / {localize(selectedProject.label, locale)}
              </span>
              <strong>{localize(selectedProject.scope, locale)}</strong>
            </p>
            <div className={styles.briefingGrid}>
              <div>
                <h2>{localize(selectedProject.title, locale)}</h2>
                <p className={styles.summaryCopy}>
                  {localize(selectedProject.description, locale)}
                </p>
                <p className={styles.resetHint}>{copy.resetFocus}</p>
              </div>
              <div className={styles.metricBlock}>
                <strong>{localize(selectedProject.metric, locale)}</strong>
                <span>{localize(selectedProject.metricLabel, locale)}</span>
              </div>
            </div>
            <div className={styles.briefingFooter}>
              <div aria-label={copy.projectSignals} className={styles.signalList}>
                {selectedProject.signals.map((signal) => (
                  <span key={signal.en}>{localize(signal, locale)}</span>
                ))}
              </div>
              <div className={styles.briefingActions}>
                <button
                  aria-label={copy.allZonesAria}
                  className={styles.secondaryAction}
                  data-pointer-role="action"
                  onClick={clearSelection}
                  tabIndex={active ? 0 : -1}
                  type="button"
                >
                  <RotateCcw aria-hidden="true" size={14} />
                  {copy.allZones}
                </button>
                <Link
                  aria-label={`${copy.openFullCaseAria}: ${localize(selectedProject.title, locale)}`}
                  className={styles.primaryAction}
                  data-pointer-role="primary"
                  href={selectedProject.futureHref}
                  tabIndex={active ? 0 : -1}
                >
                  {copy.openFullCase}
                  <ArrowUpRight aria-hidden="true" size={15} />
                </Link>
              </div>
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
              <span>{copy.atlas}</span>
              <strong>{copy.operatingModel}</strong>
            </p>
            <div className={styles.briefingGrid}>
              <div>
                <h2>{copy.overviewTitle}</h2>
                <p className={styles.summaryCopy}>{copy.overviewCopy}</p>
              </div>
              <div className={styles.metricBlock}>
                <strong>05</strong>
                <span>{copy.selectableZones}</span>
              </div>
            </div>
            <div aria-label={copy.projectMap} className={styles.signalList}>
              {factoryProjectAtlas.map((project) => (
                <span key={project.id}>
                  {project.index} / {localize(project.shortLabel, locale)}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      <nav aria-label={copy.zonesAria} className={styles.atlasRail}>
        <div className={styles.railLead}>
          <span>{copy.projectAtlas}</span>
          <strong>
            {selectedProject
              ? localize(selectedProject.shortLabel, locale)
              : copy.factorySystems}
          </strong>
        </div>
        <ol>
          {factoryProjectAtlas.map((project) => {
            const Icon = ZONE_ICONS[project.id];
            const selected = project.id === selection;
            return (
              <li key={project.id}>
                <button
                  aria-label={`${copy.select} ${localize(project.title, locale)}`}
                  aria-pressed={selected}
                  data-pointer-role="waypoint"
                  data-selected={selected || undefined}
                  onClick={() => selectTarget(project.id)}
                  tabIndex={active ? 0 : -1}
                  type="button"
                >
                  <Icon aria-hidden="true" size={14} strokeWidth={1.7} />
                  <span>{project.index}</span>
                  <strong>{localize(project.shortLabel, locale)}</strong>
                </button>
              </li>
            );
          })}
        </ol>
        <div className={styles.railHint}>
          <Crosshair aria-hidden="true" size={14} />
          <span>{selectedProject ? copy.chooseAnother : copy.selectHint}</span>
        </div>
      </nav>

      <PrecisionPointer />
      <span aria-hidden="true" className={styles.focusVeil} />
    </section>
  );
}

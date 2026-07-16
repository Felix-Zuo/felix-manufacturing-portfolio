"use client";

import {
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  Crosshair,
  ExternalLink,
  GitBranch,
  Globe2,
  Mail,
  Pause,
  Play,
  RotateCcw,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react";

import { profile } from "@/data/profile";

import styles from "./RenderedJourney.module.css";

export type RenderedJourneyLink = {
  external?: boolean;
  href: string;
  label: string;
};

export type RenderedJourneyMetric = {
  label: string;
  value: string;
};

export type RenderedJourneyChapter = {
  align?: "left" | "right";
  eyebrow: string;
  id: string;
  label: string;
  links?: readonly RenderedJourneyLink[];
  mediaProgress: number;
  metrics?: readonly RenderedJourneyMetric[];
  summary: string;
  title: string;
};

export type RenderedJourneyProps = {
  ariaLabel?: string;
  chapters?: readonly RenderedJourneyChapter[];
  className?: string;
  desktopSrc?: string;
  initialChapter?: number;
  mobileMediaQuery?: string;
  mobilePosterSrc?: string;
  mobileSrc?: string;
  onChapterChange?: (chapter: RenderedJourneyChapter, index: number) => void;
  posterSrc?: string;
};

type TimelineState = {
  current: number;
  target: number;
};

type TimelineInputSource = "keyboard" | "touch" | "wheel";

type MagneticStopState = {
  releaseDirection: -1 | 0 | 1;
  releaseDistance: number;
  progress: number;
  settledAt: number | null;
  source: TimelineInputSource;
};

type ReleasedMagneticStop = {
  frame: number;
  progress: number;
};

type SceneHotspot = {
  detail: string;
  height?: number;
  href?: string;
  id: string;
  kicker: string;
  kind: "detail" | "screen";
  label: string;
  labelSide?: "left" | "right";
  mobileHeight?: number;
  mobileWidth?: number;
  mobileX: number;
  mobileY: number;
  width?: number;
  x: number;
  y: number;
};

type SceneSegment = {
  endFrame: number;
  hotspots: readonly SceneHotspot[];
  id: string;
  label: string;
};

type EvidenceCue = {
  chapterId: string;
  endFrame: number;
  id: "identity" | "notice" | "takt" | "impact" | "visibility";
  source: "agv" | "grinding" | "hmi" | "inspection" | "scan";
  startFrame: number;
};

type ChapterPresentation = {
  anchorX: number;
  anchorY: number;
  fromX: number;
  fromY: number;
  targetX: number;
  targetY: number;
  tilt: number;
};

const DEFAULT_DESKTOP_SRC = "/media/felix-journey-desktop.mp4";
const DEFAULT_MOBILE_SRC = "/media/felix-journey-mobile.mp4";
const DEFAULT_POSTER_SRC = "/media/felix-journey-poster.webp";
const DEFAULT_MOBILE_POSTER_SRC = "/media/felix-journey-mobile-poster.webp";
const DEFAULT_MOBILE_MEDIA_QUERY = "(max-width: 767px)";
const RENDERED_FPS = 24;
const RENDERED_FRAME_COUNT = 912;
const RENDERED_DURATION_SECONDS = (RENDERED_FRAME_COUNT - 1) / RENDERED_FPS;
const FOLLOW_RATE = 5.4;
const KEYBOARD_STEP_SECONDS = 0.22;
const TOUCH_SECONDS_PER_VIEWPORT = 3.6;
const WHEEL_LINES_PER_NOTCH = 3;
const WHEEL_NOTCH_PIXELS = 100;
const WHEEL_SECONDS_PER_PIXEL = 0.0022;
const MAX_WHEEL_EVENT_SECONDS = 0.32;
const MAGNET_RELEASE_DISTANCE_PX = 28;
const MAGNET_RECAPTURE_LOCKOUT_FRAMES = 18;
const MAGNET_SETTLE_PROGRESS = 0.5 / (RENDERED_FRAME_COUNT - 1);
const SEEK_EPSILON_SECONDS = 1 / 90;
const ENTRY_POSTER_RELEASE_PROGRESS = mediaProgressAtFrame(18);
const FINAL_SUMMARY_FRAME = 904;
const FINAL_SUMMARY_PROGRESS = mediaProgressAtFrame(FINAL_SUMMARY_FRAME);
const HASH_CHAPTER_INDEX: Readonly<Record<string, number>> = {
  about: 0,
  "case-studies": 1,
  impact: 3,
  "project-map": 4,
};

function mediaProgressAtFrame(frame: number) {
  const boundedFrame = clamp(Math.round(frame), 1, RENDERED_FRAME_COUNT);
  return (boundedFrame - 1) / (RENDERED_FRAME_COUNT - 1);
}

const PROJECT_MAGNET_FRAMES = [132, 228, 474, 660] as const;
const PROJECT_MAGNET_PROGRESS = PROJECT_MAGNET_FRAMES.map(mediaProgressAtFrame);

const EVIDENCE_CUES: readonly EvidenceCue[] = [
  { chapterId: "origin", endFrame: 76, id: "identity", source: "agv", startFrame: 25 },
  { chapterId: "notice", endFrame: 150, id: "notice", source: "scan", startFrame: 107 },
  { chapterId: "takt", endFrame: 252, id: "takt", source: "hmi", startFrame: 198 },
  { chapterId: "impact", endFrame: 498, id: "impact", source: "grinding", startFrame: 445 },
  { chapterId: "visibility", endFrame: 702, id: "visibility", source: "inspection", startFrame: 632 },
];

export const DEFAULT_RENDERED_JOURNEY_CHAPTERS: readonly RenderedJourneyChapter[] = [
  {
    align: "left",
    eyebrow: "Manufacturing project coordination",
    id: "origin",
    label: "Entry",
    links: [{ external: true, href: profile.github, label: "View public work" }],
    mediaProgress: mediaProgressAtFrame(1),
    metrics: [{ label: "Operating focus", value: "Launch to delivery" }],
    summary:
      "Manufacturing project chaos, turned into measurable improvement through trial production, workflow control, and operations visibility.",
    title: "Felix Zuo",
  },
  {
    align: "right",
    eyebrow: "Case 01 / scan and release",
    id: "notice",
    label: "Release",
    links: [
      { href: "/case-studies/production-notice-workflow-standardization", label: "Open case study" },
      {
        external: true,
        href: "https://felix-zuo.github.io/factory-production-notice-agent/showcase.html",
        label: "View project",
      },
    ],
    mediaProgress: mediaProgressAtFrame(132),
    metrics: [{ label: "Preparation time", value: "20-40 min -> < 1 min" }],
    summary:
      "A scan result becomes a structured, reviewable release packet while final approval remains human.",
    title: "Production Notice Workflow Standardization",
  },
  {
    align: "left",
    eyebrow: "Case 02 / live HMI simulation",
    id: "takt",
    label: "Simulate",
    links: [
      {
        href: "/case-studies/trial-production-takt-simulation-changeover-improvement",
        label: "Open case study",
      },
      {
        external: true,
        href: "https://felix-zuo.github.io/factory-takt-simulator/?view=showcase",
        label: "Open live simulator",
      },
    ],
    mediaProgress: mediaProgressAtFrame(228),
    metrics: [{ label: "Live signal", value: "Flow / wait / block" }],
    summary:
      "The running HMI exposes bottlenecks, buffers, waiting, and blocking before physical trial-and-error consumes time and material.",
    title: "Trial Production Takt Simulation",
  },
  {
    align: "right",
    eyebrow: "Measured impact / wet grinding",
    id: "impact",
    label: "Improve",
    mediaProgress: mediaProgressAtFrame(474),
    metrics: [
      { label: "Adjustment cycle", value: "3 days -> 1 day" },
      { label: "Trial scrap", value: "~90% less" },
      { label: "Estimated saving", value: "RMB 20,000" },
    ],
    summary:
      "The improvement signal appears at the process contact, where stable evidence replaces repeated physical trial loops.",
    title: "Less trial. Faster proof.",
  },
  {
    align: "right",
    eyebrow: "Case 03 / inspection to operating view",
    id: "visibility",
    label: "See",
    links: [
      {
        href: "/case-studies/supply-production-delivery-operations-visibility",
        label: "Open case study",
      },
      {
        external: true,
        href: "https://felix-zuo.github.io/factory-excel-ops-dashboard/showcase.html",
        label: "View project",
      },
    ],
    mediaProgress: mediaProgressAtFrame(660),
    metrics: [{ label: "Data path", value: "Measure -> normalize -> see" }],
    summary:
      "Inspection records become a consistent operating view for supply, production, delivery, and exception closure.",
    title: "Supply-Production-Delivery Operations Visibility",
  },
];

const CHAPTER_PRESENTATIONS: Readonly<Record<EvidenceCue["id"], ChapterPresentation>> = {
  identity: { anchorX: 50, anchorY: 51, fromX: -7, fromY: 6, targetX: 25, targetY: 70, tilt: -7 },
  notice: { anchorX: 62, anchorY: 45, fromX: 24, fromY: -5, targetX: 75, targetY: 70, tilt: 5 },
  takt: { anchorX: 70, anchorY: 41, fromX: 27, fromY: -8, targetX: 25, targetY: 70, tilt: -5 },
  impact: { anchorX: 42, anchorY: 48, fromX: 24, fromY: -3, targetX: 75, targetY: 70, tilt: 4 },
  visibility: { anchorX: 37, anchorY: 55, fromX: 25, fromY: -5, targetX: 75, targetY: 70, tilt: 4 },
};

const SCENE_SEGMENTS: readonly SceneSegment[] = [
  {
    endFrame: 84,
    hotspots: [
      {
        detail: "The same traceable outer ring remains the visual lead from inbound transport to final release.",
        id: "hero-ring-inbound",
        kicker: "RING_HERO_01 / Inbound",
        kind: "detail",
        label: "Traceable bearing outer ring",
        mobileX: 50,
        mobileY: 47,
        x: 51,
        y: 53,
      },
    ],
    id: "agv-inbound",
    label: "Follow the material",
  },
  {
    endFrame: 150,
    hotspots: [
      {
        detail: "Identity, route, and release status are resolved before the AGV enters the robot cell.",
        id: "release-scanner",
        kicker: "Scan -> validate -> release",
        kind: "detail",
        label: "Release scanner",
        labelSide: "left",
        mobileX: 61,
        mobileY: 42,
        x: 63,
        y: 45,
      },
    ],
    id: "scan-release",
    label: "Scan and release",
  },
  {
    endFrame: 252,
    hotspots: [
      {
        detail: "The only project sourced from a real scene screen: a running, public-safe takt simulation.",
        height: 23,
        href: "https://felix-zuo.github.io/factory-takt-simulator/?view=showcase",
        id: "takt-hmi",
        kicker: "Live HMI / Case 02",
        kind: "screen",
        label: "Factory Takt Simulator",
        mobileHeight: 20,
        mobileWidth: 50,
        mobileX: 68,
        mobileY: 39,
        width: 28,
        x: 70,
        y: 41,
      },
      {
        detail: "The servo parallel gripper closes on compliant pads before lift; the wrist and cable dress follow the load.",
        id: "robot-grip",
        kicker: "Robot transfer",
        kind: "detail",
        label: "Gripper and ring",
        mobileX: 48,
        mobileY: 56,
        x: 49,
        y: 57,
      },
    ],
    id: "robot-pickup",
    label: "Robot pickup",
  },
  {
    endFrame: 342,
    hotspots: [
      {
        detail: "The camera follows the ring through the guarded opening until support shoes, the drive plate, and axial locators establish the grind datum.",
        id: "machine-load",
        kicker: "Material handoff",
        kind: "detail",
        label: "Located and clamped",
        mobileX: 50,
        mobileY: 50,
        x: 54,
        y: 51,
      },
    ],
    id: "machine-loading",
    label: "Enter the machine",
  },
  {
    endFrame: 498,
    hotspots: [
      {
        detail: "Directed coolant, visible rotation, a radial wheel approach, restrained wet sparks, and centrifugal splash meet at one contact arc.",
        id: "wet-grinding-contact",
        kicker: "Outer-ring groove grinding",
        kind: "detail",
        label: "Wet grinding contact",
        labelSide: "left",
        mobileX: 43,
        mobileY: 42,
        x: 42,
        y: 48,
      },
    ],
    id: "wet-grinding",
    label: "Wet groove grinding",
  },
  {
    endFrame: 588,
    hotspots: [
      {
        detail: "An enclosed servo turner lays the ring flat into a restrained carrier; a continuous side-flex belt and two-stage air knives move it through the curved transfer without exposed rollers.",
        id: "air-knife-transfer",
        kicker: "Rinse -> air knife -> transfer",
        kind: "detail",
        label: "Ground and rinsed",
        mobileX: 52,
        mobileY: 48,
        x: 54,
        y: 51,
      },
    ],
    id: "outfeed-transfer",
    label: "Side-flex belt transfer",
  },
  {
    endFrame: 702,
    hotspots: [
      {
        detail: "The ring remains flat on a vertical-axis air-bearing table while an L-shaped stylus enters the bore and traces the internal raceway before the result becomes a normalized record.",
        id: "inspection-trace",
        kicker: "Measurement -> record -> dashboard",
        kind: "detail",
        label: "Inspection data path",
        labelSide: "left",
        mobileX: 38,
        mobileY: 53,
        x: 37,
        y: 55,
      },
    ],
    id: "online-inspection",
    label: "Inspect and normalize",
  },
  {
    endFrame: 798,
    hotspots: [],
    id: "line-reveal",
    label: "Release / Simulate / See",
  },
  {
    endFrame: 882,
    hotspots: [
      {
        detail: "The completed ring returns to AGV_07 and follows the same guide line toward the final interlocked door.",
        id: "finished-ring",
        kicker: "RING_HERO_01 / Outbound",
        kind: "detail",
        label: "Verified part leaving the system",
        mobileX: 50,
        mobileY: 53,
        x: 50,
        y: 55,
      },
    ],
    id: "agv-outbound",
    label: "Follow the result",
  },
  {
    endFrame: RENDERED_FRAME_COUNT,
    hotspots: [],
    id: "black-handoff",
    label: "Sequence handoff",
  },
];

const FINAL_TIMELINE = [
  { index: "01", label: "Release", result: "Reviewable notice packet in under one minute" },
  { index: "02", label: "Simulate", result: "Flow decisions tested before physical trial" },
  { index: "03", label: "Improve", result: "Adjustment cycle reduced from three days to one" },
  { index: "04", label: "See", result: "Supply to delivery in one consistent operating view" },
] as const;

const FINAL_METRICS = [
  { label: "Notice preparation", value: "< 1 min" },
  { label: "Adjustment cycle", value: "3 d to 1 d" },
  { label: "Trial scrap", value: "~90% less" },
] as const;

function clamp(value: number, minimum = 0, maximum = 1) {
  return Math.min(Math.max(value, minimum), maximum);
}

function nearestChapterIndex(
  progress: number,
  chapters: readonly RenderedJourneyChapter[],
) {
  const boundedProgress = clamp(progress);
  let nearestIndex = 0;
  let nearestDistance = Number.POSITIVE_INFINITY;

  chapters.forEach((chapter, index) => {
    const distance = Math.abs(clamp(chapter.mediaProgress) - boundedProgress);
    if (distance >= nearestDistance) return;

    nearestDistance = distance;
    nearestIndex = index;
  });

  return nearestIndex;
}

function frameAtMediaProgress(progress: number) {
  return Math.round(clamp(progress) * (RENDERED_FRAME_COUNT - 1)) + 1;
}

function sceneSegmentIndexAtProgress(progress: number) {
  const frame = frameAtMediaProgress(progress);
  const segmentIndex = SCENE_SEGMENTS.findIndex((segment) => frame <= segment.endFrame);
  return segmentIndex === -1 ? SCENE_SEGMENTS.length - 1 : segmentIndex;
}

function evidenceCueIndexAtProgress(progress: number) {
  const frame = frameAtMediaProgress(progress);
  const cueIndex = EVIDENCE_CUES.findIndex(
    (cue) => frame >= cue.startFrame && frame <= cue.endFrame,
  );
  return cueIndex === -1 ? null : cueIndex;
}

function formatFrameLabel(frame: number) {
  return `F${String(frame).padStart(3, "0")}`;
}

function formatTimecode(frame: number) {
  const frameIndex = clamp(Math.round(frame), 1, RENDERED_FRAME_COUNT) - 1;
  const frames = frameIndex % RENDERED_FPS;
  const totalSeconds = Math.floor(frameIndex / RENDERED_FPS);
  const seconds = totalSeconds % 60;
  const totalMinutes = Math.floor(totalSeconds / 60);
  const minutes = totalMinutes % 60;
  const hours = Math.floor(totalMinutes / 60);

  return [hours, minutes, seconds, frames]
    .map((unit) => String(unit).padStart(2, "0"))
    .join(":");
}

function mediaProgressForSeconds(seconds: number) {
  return seconds / RENDERED_DURATION_SECONDS;
}

function wheelDeltaPixels(event: WheelEvent) {
  if (event.deltaMode === WheelEvent.DOM_DELTA_LINE) {
    return (event.deltaY / WHEEL_LINES_PER_NOTCH) * WHEEL_NOTCH_PIXELS;
  }
  if (event.deltaMode === WheelEvent.DOM_DELTA_PAGE) {
    return Math.sign(event.deltaY) * WHEEL_NOTCH_PIXELS;
  }

  return event.deltaY;
}

function wheelDeltaSeconds(event: WheelEvent) {
  return clamp(
    wheelDeltaPixels(event) * WHEEL_SECONDS_PER_PIXEL,
    -MAX_WHEEL_EVENT_SECONDS,
    MAX_WHEEL_EVENT_SECONDS,
  );
}

function magneticStopBetween(start: number, end: number) {
  const epsilon = 0.25 / (RENDERED_FRAME_COUNT - 1);

  if (end > start) {
    return PROJECT_MAGNET_PROGRESS.find(
      (progress) => progress > start + epsilon && progress <= end + epsilon,
    );
  }

  if (end < start) {
    for (let index = PROJECT_MAGNET_PROGRESS.length - 1; index >= 0; index -= 1) {
      const progress = PROJECT_MAGNET_PROGRESS[index];
      if (progress < start - epsilon && progress >= end - epsilon) return progress;
    }
  }

  return undefined;
}

function useReducedMotionPreference() {
  const [preference, setPreference] = useState<boolean | null>(null);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const updatePreference = () => setPreference(query.matches);

    updatePreference();
    query.addEventListener("change", updatePreference);
    return () => query.removeEventListener("change", updatePreference);
  }, []);

  return preference;
}

function ChapterLink({ link }: { link: RenderedJourneyLink }) {
  const content = (
    <>
      <span>{link.label}</span>
      <ArrowUpRight aria-hidden="true" size={15} strokeWidth={1.8} />
    </>
  );

  if (link.external) {
    return (
      <a
        className={styles.chapterLink}
        data-magnetic="true"
        href={link.href}
        rel="noreferrer"
        target="_blank"
      >
        {content}
      </a>
    );
  }

  if (link.href.startsWith("mailto:") || link.href.startsWith("tel:")) {
    return (
      <a className={styles.chapterLink} data-magnetic="true" href={link.href}>
        {content}
      </a>
    );
  }

  return (
    <Link className={styles.chapterLink} data-magnetic="true" href={link.href}>
      {content}
    </Link>
  );
}

function SceneHotspotMarker({
  hotspot,
  instanceId,
  isOpen,
  onToggle,
}: {
  hotspot: SceneHotspot;
  instanceId: string;
  isOpen: boolean;
  onToggle: () => void;
}) {
  const panelId = `${instanceId}-${hotspot.id}-detail`;
  const hotspotStyle = {
    "--hotspot-height": `${hotspot.height ?? 0}%`,
    "--hotspot-mobile-height": `${hotspot.mobileHeight ?? hotspot.height ?? 0}%`,
    "--hotspot-mobile-width": `${hotspot.mobileWidth ?? hotspot.width ?? 0}%`,
    "--hotspot-mobile-x": `${hotspot.mobileX}%`,
    "--hotspot-mobile-y": `${hotspot.mobileY}%`,
    "--hotspot-width": `${hotspot.width ?? 0}%`,
    "--hotspot-x": `${hotspot.x}%`,
    "--hotspot-y": `${hotspot.y}%`,
  } as CSSProperties;

  if (hotspot.kind === "screen" && hotspot.href) {
    return (
      <a
        aria-label={`Open project: ${hotspot.label}`}
        className={`${styles.sceneHotspot} ${styles.screenHotspot}`}
        data-label-side={hotspot.labelSide ?? "right"}
        data-magnetic="true"
        data-magnetic-strength="0.08"
        data-scene-hotspot="true"
        href={hotspot.href}
        rel="noreferrer"
        style={hotspotStyle}
        target="_blank"
      >
        <span aria-hidden="true" className={styles.screenTarget} />
        <span className={styles.hotspotPanel}>
          <span>{hotspot.kicker}</span>
          <strong>{hotspot.label}</strong>
          <small>{hotspot.detail}</small>
          <span className={styles.hotspotAction}>
            Open project
            <ExternalLink aria-hidden="true" size={13} strokeWidth={1.8} />
          </span>
        </span>
      </a>
    );
  }

  return (
    <div
      className={styles.sceneHotspot}
      data-label-side={hotspot.labelSide ?? "right"}
      data-open={isOpen || undefined}
      data-scene-hotspot="true"
      style={hotspotStyle}
    >
      <button
        aria-describedby={panelId}
        aria-expanded={isOpen}
        aria-label={`Inspect ${hotspot.label}`}
        className={styles.hotspotTrigger}
        data-magnetic="true"
        onClick={onToggle}
        title={hotspot.label}
        type="button"
      >
        <Crosshair aria-hidden="true" size={18} strokeWidth={1.6} />
      </button>
      <span className={styles.hotspotPanel} id={panelId} role="tooltip">
        <span>{hotspot.kicker}</span>
        <strong>{hotspot.label}</strong>
        <small>{hotspot.detail}</small>
      </span>
    </div>
  );
}

export function RenderedJourney({
  ariaLabel = "Felix Zuo rendered manufacturing journey",
  chapters,
  className = "",
  desktopSrc = DEFAULT_DESKTOP_SRC,
  initialChapter = 0,
  mobileMediaQuery = DEFAULT_MOBILE_MEDIA_QUERY,
  mobilePosterSrc = DEFAULT_MOBILE_POSTER_SRC,
  mobileSrc = DEFAULT_MOBILE_SRC,
  onChapterChange,
  posterSrc = DEFAULT_POSTER_SRC,
}: RenderedJourneyProps) {
  const chapterList = useMemo(
    () =>
      chapters && chapters.length >= 2
        ? chapters
        : DEFAULT_RENDERED_JOURNEY_CHAPTERS,
    [chapters],
  );
  const initialIndex = clamp(Math.round(initialChapter), 0, chapterList.length - 1);
  const initialProgress = clamp(chapterList[initialIndex]?.mediaProgress ?? 0);
  const initialEntryPosterVisible = initialProgress < ENTRY_POSTER_RELEASE_PROGRESS;
  const initialCueIndex = evidenceCueIndexAtProgress(initialProgress);
  const initialSceneIndex = sceneSegmentIndexAtProgress(initialProgress);
  const initialFinaleVisible = initialProgress >= FINAL_SUMMARY_PROGRESS;
  const rootStyle = useMemo(
    () =>
      ({
        "--chapter-count": chapterList.length,
        "--journey-progress": initialProgress.toFixed(5),
      }) as CSSProperties,
    [chapterList.length, initialProgress],
  );
  const instanceId = useId().replaceAll(":", "");
  const rootRef = useRef<HTMLElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const frameReadoutRef = useRef<HTMLSpanElement>(null);
  const timecodeReadoutRef = useRef<HTMLSpanElement>(null);
  const durationRef = useRef(0);
  const timelineRef = useRef<TimelineState>({
    current: initialProgress,
    target: initialProgress,
  });
  const magneticStopRef = useRef<MagneticStopState | null>(null);
  const releasedMagneticStopRef = useRef<ReleasedMagneticStop | null>(null);
  const touchYRef = useRef<number | null>(null);
  const chaptersRef = useRef(chapterList);
  const onChapterChangeRef = useRef(onChapterChange);
  const activeIndexRef = useRef(initialIndex);
  const activeCueIndexRef = useRef<number | null>(initialCueIndex);
  const activeSceneIndexRef = useRef(initialSceneIndex);
  const entryPosterVisibleRef = useRef(initialEntryPosterVisible);
  const finaleVisibleRef = useRef(initialFinaleVisible);
  const pausedRef = useRef(false);
  const [activeIndex, setActiveIndex] = useState(initialIndex);
  const [activeCueIndex, setActiveCueIndex] = useState<number | null>(initialCueIndex);
  const [activeHotspotId, setActiveHotspotId] = useState<string | null>(null);
  const [activeSceneIndex, setActiveSceneIndex] = useState(initialSceneIndex);
  const [isEntryPosterVisible, setIsEntryPosterVisible] = useState(
    initialEntryPosterVisible,
  );
  const [isFinaleVisible, setIsFinaleVisible] = useState(initialFinaleVisible);
  const [isPaused, setIsPaused] = useState(false);
  const [magneticStopFrame, setMagneticStopFrame] = useState<number | null>(null);
  const [isVideoReady, setIsVideoReady] = useState(false);
  const [videoFailed, setVideoFailed] = useState(false);
  const reducedMotion = useReducedMotionPreference();
  const isStatic = reducedMotion === true;

  useEffect(() => {
    chaptersRef.current = chapterList;
  }, [chapterList]);

  useEffect(() => {
    onChapterChangeRef.current = onChapterChange;
  }, [onChapterChange]);

  const commitActiveChapter = useCallback((index: number) => {
    const currentChapters = chaptersRef.current;
    const boundedIndex = clamp(Math.round(index), 0, currentChapters.length - 1);

    if (activeIndexRef.current === boundedIndex) return;
    activeIndexRef.current = boundedIndex;
    setActiveIndex(boundedIndex);
    onChapterChangeRef.current?.(currentChapters[boundedIndex], boundedIndex);
  }, []);

  const commitSceneSegment = useCallback((progress: number) => {
    const nextIndex = sceneSegmentIndexAtProgress(progress);
    if (activeSceneIndexRef.current === nextIndex) return;

    activeSceneIndexRef.current = nextIndex;
    setActiveSceneIndex(nextIndex);
    setActiveHotspotId(null);
  }, []);

  const commitEvidenceCue = useCallback((progress: number) => {
    const nextIndex = evidenceCueIndexAtProgress(progress);
    if (activeCueIndexRef.current === nextIndex) return;

    activeCueIndexRef.current = nextIndex;
    setActiveCueIndex(nextIndex);
  }, []);

  const commitEntryPosterVisibility = useCallback((progress: number) => {
    const nextVisible = progress < ENTRY_POSTER_RELEASE_PROGRESS;
    if (entryPosterVisibleRef.current === nextVisible) return;

    entryPosterVisibleRef.current = nextVisible;
    setIsEntryPosterVisible(nextVisible);
  }, []);

  const commitFinaleVisibility = useCallback((progress: number) => {
    const nextVisible = progress >= FINAL_SUMMARY_PROGRESS;
    if (finaleVisibleRef.current === nextVisible) return;

    finaleVisibleRef.current = nextVisible;
    setIsFinaleVisible(nextVisible);
    setActiveHotspotId(null);
  }, []);

  const seekToProgress = useCallback((progress: number) => {
    const video = videoRef.current;
    if (!video || video.readyState < HTMLMediaElement.HAVE_METADATA) return;

    const duration = durationRef.current || video.duration;
    if (!Number.isFinite(duration) || duration <= 0) return;

    const frameDuration = duration / RENDERED_FRAME_COUNT;
    const maximumTime = Math.max(duration - frameDuration, 0);
    const nextTime = maximumTime * clamp(progress);

    if (Math.abs(video.currentTime - nextTime) <= SEEK_EPSILON_SECONDS) return;

    try {
      video.currentTime = nextTime;
    } catch {
      // The selected source can change while a responsive video is loading.
    }
  }, []);

  const updateTimelineReadout = useCallback((progress: number) => {
    const frame = frameAtMediaProgress(progress);

    if (frameReadoutRef.current) {
      frameReadoutRef.current.textContent = `${formatFrameLabel(frame)} / ${RENDERED_FRAME_COUNT}`;
    }
    if (timecodeReadoutRef.current) {
      timecodeReadoutRef.current.textContent = formatTimecode(frame);
    }
  }, []);

  const renderProgressImmediately = useCallback(
    (progress: number) => {
      const boundedProgress = clamp(progress);
      timelineRef.current.current = boundedProgress;
      rootRef.current?.style.setProperty(
        "--journey-progress",
        boundedProgress.toFixed(5),
      );
      seekToProgress(boundedProgress);
      updateTimelineReadout(boundedProgress);
      commitEntryPosterVisibility(boundedProgress);
      commitEvidenceCue(boundedProgress);
      commitSceneSegment(boundedProgress);
      commitFinaleVisibility(boundedProgress);
      commitActiveChapter(
        nearestChapterIndex(boundedProgress, chaptersRef.current),
      );
    },
    [
      commitActiveChapter,
      commitEntryPosterVisibility,
      commitEvidenceCue,
      commitFinaleVisibility,
      commitSceneSegment,
      seekToProgress,
      updateTimelineReadout,
    ],
  );

  const clearMagneticStop = useCallback(() => {
    magneticStopRef.current = null;
    setMagneticStopFrame(null);
  }, []);

  const applyInputDelta = useCallback(
    (
      delta: number,
      source: TimelineInputSource,
      inputDistancePx = MAGNET_RELEASE_DISTANCE_PX,
    ) => {
      if (pausedRef.current || !Number.isFinite(delta) || delta === 0) return;

      const activeStop = magneticStopRef.current;
      if (activeStop) {
        const inputDirection = delta > 0 ? 1 : -1;
        if (activeStop.releaseDirection === inputDirection) {
          activeStop.releaseDistance += Math.abs(inputDistancePx);
        } else {
          activeStop.releaseDirection = inputDirection;
          activeStop.releaseDistance = Math.abs(inputDistancePx);
        }

        if (
          activeStop.settledAt === null ||
          activeStop.releaseDistance < MAGNET_RELEASE_DISTANCE_PX
        ) {
          return;
        }

        releasedMagneticStopRef.current = {
          frame: frameAtMediaProgress(activeStop.progress),
          progress: activeStop.progress,
        };
        clearMagneticStop();
      }

      const start = timelineRef.current.target;
      const end = clamp(start + delta);
      const releasedStop = releasedMagneticStopRef.current;
      if (
        releasedStop &&
        Math.abs(frameAtMediaProgress(start) - releasedStop.frame) >
          MAGNET_RECAPTURE_LOCKOUT_FRAMES
      ) {
        releasedMagneticStopRef.current = null;
      }

      let magneticProgress = magneticStopBetween(start, end);
      if (
        magneticProgress !== undefined &&
        releasedMagneticStopRef.current?.frame ===
          frameAtMediaProgress(magneticProgress)
      ) {
        magneticProgress = undefined;
      }

      if (magneticProgress !== undefined) {
        timelineRef.current.target = magneticProgress;
        magneticStopRef.current = {
          progress: magneticProgress,
          releaseDirection: 0,
          releaseDistance: 0,
          settledAt: null,
          source,
        };
        setMagneticStopFrame(frameAtMediaProgress(magneticProgress));
        return;
      }

      timelineRef.current.target = end;
    },
    [clearMagneticStop],
  );

  const goToProgress = useCallback(
    (progress: number) => {
      const boundedProgress = clamp(progress);
      clearMagneticStop();
      releasedMagneticStopRef.current = null;
      timelineRef.current.target = boundedProgress;

      if (pausedRef.current || reducedMotion === true) {
        renderProgressImmediately(boundedProgress);
      }
    },
    [clearMagneticStop, reducedMotion, renderProgressImmediately],
  );

  const goToChapter = useCallback(
    (index: number) => {
      const chapterCount = chaptersRef.current.length;
      const boundedIndex = clamp(Math.round(index), 0, chapterCount - 1);
      goToProgress(chaptersRef.current[boundedIndex].mediaProgress);
    },
    [goToProgress],
  );

  const goToRelativeChapter = useCallback(
    (direction: -1 | 1) => {
      const currentTargetIndex = nearestChapterIndex(
        timelineRef.current.target,
        chaptersRef.current,
      );
      goToChapter(currentTargetIndex + direction);
    },
    [goToChapter],
  );

  useEffect(() => {
    const followHash = () => {
      const hash = window.location.hash.slice(1);
      const chapterIndex = HASH_CHAPTER_INDEX[hash];
      if (chapterIndex !== undefined) goToChapter(chapterIndex);
    };

    followHash();
    window.addEventListener("hashchange", followHash);
    return () => window.removeEventListener("hashchange", followHash);
  }, [goToChapter]);

  const togglePaused = useCallback(() => {
    setIsPaused((wasPaused) => {
      const nextPaused = !wasPaused;
      pausedRef.current = nextPaused;

      if (nextPaused) {
        timelineRef.current.target = timelineRef.current.current;
        videoRef.current?.pause();
      }

      return nextPaused;
    });
  }, []);

  const restartJourney = useCallback(() => {
    pausedRef.current = false;
    setIsPaused(false);
    clearMagneticStop();
    releasedMagneticStopRef.current = null;
    timelineRef.current.target = 0;
    renderProgressImmediately(0);
    window.requestAnimationFrame(() => rootRef.current?.focus());
  }, [clearMagneticStop, renderProgressImmediately]);

  useEffect(() => {
    if (reducedMotion !== false) return;

    const video = videoRef.current;
    if (!video) return;

    setIsVideoReady(false);
    setVideoFailed(false);
    durationRef.current = 0;
    video.load();
  }, [desktopSrc, mobileMediaQuery, mobileSrc, reducedMotion]);

  useEffect(() => {
    if (reducedMotion !== false) return;

    const root = rootRef.current;
    if (!root) return;

    const onWheel = (event: WheelEvent) => {
      if (event.ctrlKey || Math.abs(event.deltaX) > Math.abs(event.deltaY)) return;
      event.preventDefault();
      if (pausedRef.current) return;

      const deltaPixels = wheelDeltaPixels(event);
      applyInputDelta(
        mediaProgressForSeconds(wheelDeltaSeconds(event)),
        "wheel",
        Math.abs(deltaPixels),
      );
    };

    const onTouchStart = (event: TouchEvent) => {
      if (event.touches.length !== 1) return;
      touchYRef.current = event.touches[0].clientY;
    };

    const onTouchMove = (event: TouchEvent) => {
      if (event.touches.length !== 1 || touchYRef.current === null) return;

      const nextY = event.touches[0].clientY;
      const deltaY = touchYRef.current - nextY;
      touchYRef.current = nextY;
      if (Math.abs(deltaY) < 0.5) return;

      event.preventDefault();
      const viewportHeight = Math.max(window.innerHeight, 480);
      const deltaSeconds = (deltaY / viewportHeight) * TOUCH_SECONDS_PER_VIEWPORT;
      applyInputDelta(
        mediaProgressForSeconds(deltaSeconds),
        "touch",
        Math.abs(deltaY),
      );
    };

    const onTouchEnd = () => {
      touchYRef.current = null;
    };

    root.addEventListener("wheel", onWheel, { passive: false });
    root.addEventListener("touchstart", onTouchStart, { passive: true });
    root.addEventListener("touchmove", onTouchMove, { passive: false });
    root.addEventListener("touchend", onTouchEnd, { passive: true });
    root.addEventListener("touchcancel", onTouchEnd, { passive: true });

    return () => {
      root.removeEventListener("wheel", onWheel);
      root.removeEventListener("touchstart", onTouchStart);
      root.removeEventListener("touchmove", onTouchMove);
      root.removeEventListener("touchend", onTouchEnd);
      root.removeEventListener("touchcancel", onTouchEnd);
    };
  }, [
    applyInputDelta,
    reducedMotion,
  ]);

  useEffect(() => {
    if (reducedMotion !== false) return;

    const root = rootRef.current;
    if (!root) return;

    const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
    const hotspotRadius = 44;
    const maximumPull = 6;

    const clearPointerFeedback = () => {
      delete root.dataset.pointerActive;
      delete root.dataset.cursorMagnetic;
    };

    const onPointerMove = (event: PointerEvent) => {
      if (!finePointer.matches) {
        clearPointerFeedback();
        return;
      }

      const normalizedX = clamp(event.clientX / Math.max(window.innerWidth, 1), 0, 1) * 2 - 1;
      const normalizedY = clamp(event.clientY / Math.max(window.innerHeight, 1), 0, 1) * 2 - 1;
      root.style.setProperty("--parallax-x", normalizedX.toFixed(4));
      root.style.setProperty("--parallax-y", normalizedY.toFixed(4));

      const target = event.target instanceof Element ? event.target : null;
      const sceneTarget = target?.closest<HTMLElement>('[data-scene-hotspot="true"]');
      const conventionalControl = target?.closest(
        'a, button, input, select, textarea, [role="button"]',
      );
      if (conventionalControl && !sceneTarget) {
        clearPointerFeedback();
        return;
      }

      let nearestHotspot: HTMLElement | null = null;
      let nearestDistance = Number.POSITIVE_INFINITY;

      const sceneHotspots = root.querySelectorAll<HTMLElement>(
        '[data-scene-hotspot="true"]',
      );
      for (const hotspot of sceneHotspots) {
        const bounds = hotspot.getBoundingClientRect();
        const nearestX = clamp(event.clientX, bounds.left, bounds.right);
        const nearestY = clamp(event.clientY, bounds.top, bounds.bottom);
        const distance = Math.hypot(event.clientX - nearestX, event.clientY - nearestY);
        if (distance <= hotspotRadius && distance < nearestDistance) {
          nearestDistance = distance;
          nearestHotspot = hotspot;
        }
      }

      if (!nearestHotspot) {
        clearPointerFeedback();
        return;
      }

      const bounds = nearestHotspot.getBoundingClientRect();
      const vectorX = bounds.left + bounds.width / 2 - event.clientX;
      const vectorY = bounds.top + bounds.height / 2 - event.clientY;
      const vectorLength = Math.hypot(vectorX, vectorY) || 1;
      const pull = Math.min(maximumPull, vectorLength * 0.14);
      const pointerX = event.clientX + (vectorX / vectorLength) * pull;
      const pointerY = event.clientY + (vectorY / vectorLength) * pull;

      root.style.setProperty("--pointer-x", `${pointerX.toFixed(1)}px`);
      root.style.setProperty("--pointer-y", `${pointerY.toFixed(1)}px`);
      root.dataset.pointerActive = "true";
      root.dataset.cursorMagnetic = "true";
    };

    const onPointerLeave = () => {
      clearPointerFeedback();
      root.style.setProperty("--parallax-x", "0");
      root.style.setProperty("--parallax-y", "0");
    };

    root.addEventListener("pointermove", onPointerMove, { passive: true });
    root.addEventListener("pointerleave", onPointerLeave, { passive: true });

    return () => {
      root.removeEventListener("pointermove", onPointerMove);
      root.removeEventListener("pointerleave", onPointerLeave);
    };
  }, [reducedMotion]);

  useEffect(() => {
    if (reducedMotion !== false) return;

    const html = document.documentElement;
    const body = document.body;
    const previousHtmlOverflow = html.style.overflow;
    const previousBodyOverflow = body.style.overflow;
    const previousOverscroll = html.style.overscrollBehavior;

    html.style.overflow = "hidden";
    body.style.overflow = "hidden";
    html.style.overscrollBehavior = "none";

    return () => {
      html.style.overflow = previousHtmlOverflow;
      body.style.overflow = previousBodyOverflow;
      html.style.overscrollBehavior = previousOverscroll;
    };
  }, [reducedMotion]);

  useEffect(() => {
    if (reducedMotion !== false) return;

    let frame = 0;
    let previousTime = performance.now();

    const tick = (time: number) => {
      const deltaSeconds = Math.min(Math.max((time - previousTime) / 1000, 0), 0.05);
      previousTime = time;

      if (!pausedRef.current) {
        const timeline = timelineRef.current;
        const distance = timeline.target - timeline.current;
        const follow = 1 - Math.exp(-FOLLOW_RATE * deltaSeconds);

        timeline.current =
          Math.abs(distance) < 0.00005
            ? timeline.target
            : timeline.current + distance * follow;

        const activeStop = magneticStopRef.current;
        if (
          activeStop &&
          Math.abs(activeStop.progress - timeline.current) <= MAGNET_SETTLE_PROGRESS
        ) {
          timeline.current = activeStop.progress;
          timeline.target = activeStop.progress;
          activeStop.settledAt ??= time;
        }
      }

      const progress = timelineRef.current.current;
      rootRef.current?.style.setProperty(
        "--journey-progress",
        progress.toFixed(5),
      );
      seekToProgress(progress);
      updateTimelineReadout(progress);
      commitEntryPosterVisibility(progress);
      commitEvidenceCue(progress);
      commitSceneSegment(progress);
      commitFinaleVisibility(progress);
      commitActiveChapter(
        nearestChapterIndex(progress, chaptersRef.current),
      );
      frame = window.requestAnimationFrame(tick);
    };

    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, [
    commitActiveChapter,
    commitEntryPosterVisibility,
    commitEvidenceCue,
    commitFinaleVisibility,
    commitSceneSegment,
    reducedMotion,
    seekToProgress,
    updateTimelineReadout,
  ]);

  const handleKeyDown = (event: ReactKeyboardEvent<HTMLElement>) => {
    const target = event.target as HTMLElement;

    if (event.key === "Escape") {
      if (activeHotspotId) {
        event.preventDefault();
        setActiveHotspotId(null);
        return;
      }

      if (finaleVisibleRef.current) {
        event.preventDefault();
        goToChapter(chaptersRef.current.length - 1);
        return;
      }
    }

    if (target !== event.currentTarget && target.closest("a, button, input, select, textarea")) {
      return;
    }

    if (event.key === "ArrowDown" || event.key === "ArrowRight" || event.key === "PageDown") {
      event.preventDefault();
      if (isStatic) {
        if (activeIndexRef.current >= chaptersRef.current.length - 1) {
          goToProgress(1);
        } else {
          goToRelativeChapter(1);
        }
      } else {
        applyInputDelta(mediaProgressForSeconds(KEYBOARD_STEP_SECONDS), "keyboard");
      }
      return;
    }

    if (event.key === "ArrowUp" || event.key === "ArrowLeft" || event.key === "PageUp") {
      event.preventDefault();
      if (finaleVisibleRef.current) {
        goToChapter(chaptersRef.current.length - 1);
      } else if (isStatic) {
        goToRelativeChapter(-1);
      } else {
        applyInputDelta(mediaProgressForSeconds(-KEYBOARD_STEP_SECONDS), "keyboard");
      }
      return;
    }

    if (event.key === "Home" || event.key === "End") {
      event.preventDefault();
      goToProgress(event.key === "Home" ? 0 : 1);
      return;
    }

    if (event.key === " " && !isStatic) {
      event.preventDefault();
      togglePaused();
    }
  };

  const safeActiveIndex = clamp(activeIndex, 0, chapterList.length - 1);
  const activeChapter = chapterList[safeActiveIndex];
  const activeCue = activeCueIndex === null ? null : EVIDENCE_CUES[activeCueIndex];
  const activeCardIndex = activeCue
    ? chapterList.findIndex((chapter) => chapter.id === activeCue.chapterId)
    : -1;
  const activeCardChapter = activeCardIndex >= 0 ? chapterList[activeCardIndex] : null;
  const activePresentation = activeCue
    ? CHAPTER_PRESENTATIONS[activeCue.id]
    : CHAPTER_PRESENTATIONS.identity;
  const safeSceneIndex = clamp(activeSceneIndex, 0, SCENE_SEGMENTS.length - 1);
  const activeScene = SCENE_SEGMENTS[safeSceneIndex];
  const chapterTitleId = `${instanceId}-${activeCardChapter?.id ?? activeChapter.id}-title`;
  const finaleTitleId = `${instanceId}-finale-title`;
  const isFirstChapter = safeActiveIndex === 0;
  const isLastChapter = safeActiveIndex === chapterList.length - 1;
  const renderedFrame = frameAtMediaProgress(
    activeCardChapter?.mediaProgress ?? activeChapter.mediaProgress,
  );
  const projectionStyle = {
    "--project-from-x": `${activePresentation.fromX}vw`,
    "--project-from-y": `${activePresentation.fromY}vh`,
    "--project-tilt": `${activePresentation.tilt}deg`,
  } as CSSProperties;
  const mediaState = isStatic
    ? "Static frame"
    : videoFailed
      ? "Poster fallback"
      : isVideoReady
        ? "Rendered media"
        : "Loading media";

  return (
    <section
      aria-label={ariaLabel}
      aria-labelledby={
        isFinaleVisible ? finaleTitleId : activeCardChapter ? chapterTitleId : undefined
      }
      className={`${styles.root} ${isStatic ? styles.reducedMotion : ""} ${className}`.trim()}
      data-finale={isFinaleVisible || undefined}
      data-evidence-cue={activeCue?.id}
      data-magnetic-stop={magneticStopFrame ?? undefined}
      data-paused={isPaused || undefined}
      data-scene={activeScene.id}
      data-reduced-motion={isStatic || undefined}
      onKeyDown={handleKeyDown}
      ref={rootRef}
      style={rootStyle}
      tabIndex={0}
    >
      <div aria-hidden="true" className={styles.media}>
        {/* The poster owns first paint; video loading starts only after motion preference is known. */}
        <picture
          className={`${styles.posterFrame} ${isVideoReady && !isStatic && !isEntryPosterVisible ? styles.posterHidden : ""}`}
        >
          <source media={mobileMediaQuery} srcSet={mobilePosterSrc} />
          <Image
            alt=""
            className={styles.poster}
            fill
            priority
            sizes="100vw"
            src={posterSrc}
          />
        </picture>
        <video
          className={`${styles.video} ${isVideoReady && !isStatic && !isEntryPosterVisible ? styles.videoReady : ""}`}
          muted
          onError={() => {
            setVideoFailed(true);
            setIsVideoReady(false);
          }}
          onLoadedData={() => {
            setVideoFailed(false);
            setIsVideoReady(true);
            seekToProgress(timelineRef.current.current);
          }}
          onLoadedMetadata={(event) => {
            const video = event.currentTarget;
            durationRef.current = Number.isFinite(video.duration) ? video.duration : 0;
            video.pause();
            seekToProgress(timelineRef.current.current);
          }}
          playsInline
          poster={posterSrc}
          preload="metadata"
          ref={videoRef}
          tabIndex={-1}
        >
          <source media={mobileMediaQuery} src={mobileSrc} type="video/mp4" />
          <source src={desktopSrc} type="video/mp4" />
        </video>
        <div className={styles.shade} />
      </div>

      <header className={styles.meta}>
        <span>FZ / Manufacturing operations</span>
        <span>{activeScene.label}</span>
        <span>Sanitized / synthetic</span>
      </header>
      <span aria-live="polite" className={styles.srOnly}>
        {mediaState}
        {magneticStopFrame
          ? `. Project hold at ${formatFrameLabel(magneticStopFrame)}. Continue navigating to release.`
          : ""}
      </span>

      {!isFinaleVisible && (
        <>
          <div className={styles.sceneOverlay} key={activeScene.id}>
            {activeScene.hotspots.map((hotspot) => (
              <SceneHotspotMarker
                hotspot={hotspot}
                instanceId={instanceId}
                isOpen={activeHotspotId === hotspot.id}
                key={hotspot.id}
                onToggle={() =>
                  setActiveHotspotId((current) =>
                    current === hotspot.id ? null : hotspot.id,
                  )
                }
              />
            ))}
          </div>

          {activeCue && activeCardChapter && (
            <div
              className={styles.chapterProjection}
              data-cue={activeCue.id}
              data-source={activeCue.source}
              key={activeCue.id}
              style={projectionStyle}
            >
            <svg
              aria-hidden="true"
              className={styles.projectionBeam}
              preserveAspectRatio="none"
              viewBox="0 0 100 100"
            >
              <line
                x1={activePresentation.anchorX}
                x2={activePresentation.targetX}
                y1={activePresentation.anchorY}
                y2={activePresentation.targetY}
              />
              <circle
                cx={activePresentation.anchorX}
                cy={activePresentation.anchorY}
                r="0.32"
              />
            </svg>

            <article
              aria-atomic="true"
              aria-live="polite"
              className={`${styles.chapter} ${activeCardChapter.align === "right" ? styles.chapterRight : ""}`}
            >
              <p className={styles.eyebrow}>
                <span>
                  {String(activeCardIndex + 1).padStart(2, "0")} /{" "}
                  {String(chapterList.length).padStart(2, "0")}
                </span>
                {activeCardChapter.eyebrow}
              </p>
              <h1 className={styles.title} id={chapterTitleId}>
                {activeCardChapter.title}
              </h1>
              <p className={styles.summary}>{activeCardChapter.summary}</p>

              <div className={styles.evidenceRow}>
                {activeCardChapter.metrics && activeCardChapter.metrics.length > 0 && (
                  <dl className={styles.signal}>
                    {activeCardChapter.metrics.map((metric) => (
                      <div key={metric.label}>
                        <dt>{metric.label}</dt>
                        <dd>{metric.value}</dd>
                      </div>
                    ))}
                  </dl>
                )}

                {activeCardChapter.links && activeCardChapter.links.length > 0 && (
                  <div className={styles.chapterLinks}>
                    {activeCardChapter.links.map((link) => (
                      <ChapterLink key={`${link.href}-${link.label}`} link={link} />
                    ))}
                  </div>
                )}
              </div>

              <footer className={styles.slateFooter}>
                <span>38.000 SEC / 24 FPS</span>
                <span aria-hidden="true" className={styles.slateProgress} />
                <span ref={frameReadoutRef}>
                  {formatFrameLabel(renderedFrame)} / {RENDERED_FRAME_COUNT}
                </span>
                <span ref={timecodeReadoutRef}>{formatTimecode(renderedFrame)}</span>
              </footer>
            </article>
            </div>
          )}
        </>
      )}

      {isFinaleVisible && (
        <section aria-labelledby={finaleTitleId} className={styles.finale}>
          <span aria-hidden="true" className={styles.finaleBlackout} />
          <div className={styles.finaleInner}>
            <header className={styles.finaleHeader}>
              <div>
                <span>FZ / Portfolio summary</span>
                <strong>Manufacturing operations + digital process improvement</strong>
              </div>
              <span>38.000 / Sequence complete</span>
            </header>

            <div className={styles.finaleLead}>
              <div>
                <p>Factory exit / Operating record</p>
                <h1 id={finaleTitleId}>Execution made visible.</h1>
              </div>
              <p>
                From launch risk and trial production to reviewable workflows,
                measurable flow, and public-safe operating evidence.
              </p>
            </div>

            <dl className={styles.finaleMetrics}>
              {FINAL_METRICS.map((metric) => (
                <div key={metric.label}>
                  <dt>{metric.label}</dt>
                  <dd>{metric.value}</dd>
                </div>
              ))}
            </dl>

            <section aria-labelledby={`${instanceId}-timeline-title`} className={styles.finaleTimeline}>
              <div className={styles.finaleSectionHeading}>
                <span>Selected project timeline</span>
                <strong id={`${instanceId}-timeline-title`}>One control logic, four outputs</strong>
              </div>
              <ol>
                {FINAL_TIMELINE.map((item) => (
                  <li key={item.index}>
                    <span>{item.index}</span>
                    <strong>{item.label}</strong>
                    <p>{item.result}</p>
                  </li>
                ))}
              </ol>
            </section>

            <footer className={styles.finaleFooter}>
              <div className={styles.finaleActions}>
                <Link data-magnetic="true" href="/">
                  <Globe2 aria-hidden="true" size={17} />
                  Portfolio home
                </Link>
                <a data-magnetic="true" href={profile.github} rel="noreferrer" target="_blank">
                  <GitBranch aria-hidden="true" size={17} />
                  GitHub
                </a>
                <a data-magnetic="true" href={`mailto:${profile.email}`}>
                  <Mail aria-hidden="true" size={17} />
                  {profile.email}
                </a>
              </div>
              <button data-magnetic="true" onClick={restartJourney} type="button">
                <RotateCcw aria-hidden="true" size={17} />
                Replay journey
              </button>
            </footer>
          </div>
        </section>
      )}

      <div aria-hidden="true" className={styles.viewfinderCursor}>
        <span />
      </div>

      {!isFinaleVisible && <div className={styles.controls}>
        <button
          aria-label="Previous chapter"
          className={styles.iconButton}
          data-magnetic="true"
          disabled={isFirstChapter}
          onClick={() => goToRelativeChapter(-1)}
          title="Previous chapter"
          type="button"
        >
          <ChevronLeft aria-hidden="true" size={18} />
        </button>

        <nav aria-label="Journey chapters" className={styles.chapterNav}>
          <ol>
            {chapterList.map((chapter, index) => (
              <li
                key={chapter.id}
                style={
                  {
                    "--chapter-progress": clamp(chapter.mediaProgress).toFixed(5),
                  } as CSSProperties
                }
              >
                <button
                  aria-current={index === safeActiveIndex ? "step" : undefined}
                  aria-label={`Go to chapter ${index + 1}: ${chapter.label}, ${formatFrameLabel(frameAtMediaProgress(chapter.mediaProgress))}`}
                  className={index === safeActiveIndex ? styles.activeStop : ""}
                  data-magnetic="true"
                  onClick={() => goToChapter(index)}
                  title={chapter.label}
                  type="button"
                />
              </li>
            ))}
          </ol>
        </nav>

        {!isStatic && (
          <button
            aria-label={isPaused ? "Resume journey" : "Pause journey"}
            aria-pressed={isPaused}
            className={styles.iconButton}
            data-magnetic="true"
            onClick={togglePaused}
            title={isPaused ? "Resume journey" : "Pause journey"}
            type="button"
          >
            {isPaused ? (
              <Play aria-hidden="true" size={16} />
            ) : (
              <Pause aria-hidden="true" size={16} />
            )}
          </button>
        )}

        <button
          aria-label={isLastChapter ? "Open portfolio summary" : "Next chapter"}
          className={styles.iconButton}
          data-magnetic="true"
          onClick={() => (isLastChapter ? goToProgress(1) : goToRelativeChapter(1))}
          title={isLastChapter ? "Open portfolio summary" : "Next chapter"}
          type="button"
        >
          <ChevronRight aria-hidden="true" size={18} />
        </button>
      </div>}
    </section>
  );
}

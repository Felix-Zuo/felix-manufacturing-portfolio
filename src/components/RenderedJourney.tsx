"use client";

import {
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
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

import {
  createCinematicAssetManifest,
  type CinematicMediaProfile,
} from "./cinematicAssets";
import { JourneyControlDeck } from "./JourneyControlDeck";
import styles from "./RenderedJourney.module.css";
import { useCinematicPreloader } from "./useCinematicPreloader";

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
  kind?: "intro" | "interlude" | "project" | "finale";
  label: string;
  links?: readonly RenderedJourneyLink[];
  mediaProgress: number;
  metrics?: readonly RenderedJourneyMetric[];
  points?: readonly string[];
  stop?: boolean;
  storyProgress?: number;
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

const DEFAULT_DESKTOP_SRC = "/media/felix-journey-stream-desktop.mp4?v=10";
const DEFAULT_MOBILE_SRC = "/media/felix-journey-stream-mobile.mp4?v=10";
const DEFAULT_POSTER_SRC = "/media/felix-journey-poster.webp?v=10";
const DEFAULT_MOBILE_POSTER_SRC = "/media/felix-journey-mobile-poster.webp?v=10";
const DEFAULT_MOBILE_MEDIA_QUERY = "(max-width: 767px)";
const FOLLOW_RATE = 10;
const MAX_TIMELINE_RATE = 0.22;
const CHAPTER_NAV_FOLLOW_RATE = 8;
const CHAPTER_NAV_MAX_TIMELINE_RATE = 0.32;
const WHEEL_PROGRESS_STEP = 0.034;
const TOUCH_PROGRESS_PER_VIEWPORT = 0.18;
const CONTROL_DECK_REVEAL_START = 0.95;
const CONTROL_DECK_ACTIVE_PROGRESS = 0.9975;
const RENDERED_FPS = 24;
const RENDERED_FRAME_COUNT = 912;
const INITIAL_MEDIA_OFFSET_SECONDS = 0.1;
const MAX_FORWARD_LEAD_SECONDS = 1.8;
const FORWARD_GLIDE_SECONDS = 1.15;
const REVERSE_SEEK_INTERVAL = 42;
const TIMELINE_SETTLE_RADIUS = 0.00005;
const HASH_CHAPTER_INDEX: Readonly<Record<string, number>> = {
  about: 0,
  impact: 1,
  "project-map": 2,
  "case-studies": 3,
  notice: 3,
  takt: 4,
  methodology: 5,
  visibility: 5,
  "portfolio-lab": 6,
  system: 6,
  contact: 7,
};

function mediaProgressAtFrame(frame: number) {
  const boundedFrame = clamp(Math.round(frame), 1, RENDERED_FRAME_COUNT);
  return (boundedFrame - 1) / (RENDERED_FRAME_COUNT - 1);
}

export const DEFAULT_RENDERED_JOURNEY_CHAPTERS: readonly RenderedJourneyChapter[] = [
  {
    align: "left",
    eyebrow: "Manufacturing project coordination",
    id: "origin",
    kind: "intro",
    label: "Entry",
    links: [
      {
        external: true,
        href: profile.github,
        label: "View public work",
      },
    ],
    mediaProgress: mediaProgressAtFrame(1),
    metrics: [{ label: "Operating focus", value: "Launch to delivery" }],
    stop: true,
    storyProgress: 0,
    summary:
      "Manufacturing project chaos, turned into measurable improvement through trial production, workflow control, and operations visibility.",
    title: "Felix Zuo",
  },
  {
    align: "right",
    eyebrow: "Measured impact",
    id: "impact",
    kind: "interlude",
    label: "Signal",
    mediaProgress: mediaProgressAtFrame(169),
    metrics: [{ label: "Notice preparation", value: "< 1 min" }],
    stop: true,
    storyProgress: 0.16,
    summary:
      "Real workflow outcomes, represented with public-safe evidence and synthetic data.",
    title: "Outcomes first. Tools second.",
  },
  {
    align: "left",
    eyebrow: "Trial production / process observation",
    id: "process",
    kind: "interlude",
    label: "Process",
    links: [
      {
        external: true,
        href: "https://felix-zuo.github.io/factory-takt-simulator/?view=showcase",
        label: "Open takt simulator",
      },
    ],
    mediaProgress: mediaProgressAtFrame(301),
    metrics: [{ label: "Decision signal", value: "Observe first" }],
    stop: true,
    storyProgress: 0.3,
    summary:
      "Controlled observation isolates the critical operation and creates a slower decision moment before ramp-up.",
    title: "Observe the process before changing it.",
  },
  {
    align: "left",
    eyebrow: "Case 01 / workflow control",
    id: "notice",
    kind: "project",
    label: "Notice",
    links: [
      {
        href: "/case-studies/production-notice-workflow-standardization",
        label: "Open case study",
      },
      {
        external: true,
        href: "https://felix-zuo.github.io/factory-production-notice-agent/showcase.html",
        label: "View project",
      },
    ],
    mediaProgress: mediaProgressAtFrame(433),
    metrics: [{ label: "Control point", value: "Human final review" }],
    points: [
      "Structured request replaces repeated cross-system collection.",
      "A human control gate keeps final release authority explicit.",
      "The coordinated packet remains reviewable from request to issue.",
    ],
    stop: true,
    storyProgress: 0.44,
    summary:
      "Structured inputs turn repeated cross-system checking into a reviewable release packet while final control stays human.",
    title: "Production Notice Workflow Standardization",
  },
  {
    align: "left",
    eyebrow: "Case 02 / flow simulation",
    id: "takt",
    kind: "project",
    label: "Takt",
    links: [
      {
        href: "/case-studies/trial-production-takt-simulation-changeover-improvement",
        label: "Open case study",
      },
      {
        external: true,
        href: "https://github.com/Felix-Zuo/factory-takt-simulator",
        label: "View source",
      },
    ],
    mediaProgress: mediaProgressAtFrame(553),
    metrics: [{ label: "Adjustment cycle", value: "3 d to 1 d" }],
    points: [
      "Model the full line before changing the physical process.",
      "Expose bottlenecks, blocking, waiting, and buffer behavior.",
      "Compare countermeasures before consuming trial time and material.",
    ],
    stop: true,
    storyProgress: 0.58,
    summary:
      "Full-line simulation exposes bottlenecks, buffers, waiting, and blocking before physical trial-and-error consumes more time and material.",
    title: "Trial Production Takt Simulation",
  },
  {
    align: "right",
    eyebrow: "Case 03 / operations visibility",
    id: "visibility",
    kind: "project",
    label: "Visibility",
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
    mediaProgress: mediaProgressAtFrame(673),
    metrics: [{ label: "Operating span", value: "Supply to delivery" }],
    points: [
      "Classify scattered exports into one operating structure.",
      "Normalize recurring inputs before calculation and review.",
      "Keep supply, production, delivery, and exceptions in one view.",
    ],
    stop: true,
    storyProgress: 0.72,
    summary:
      "Scattered spreadsheet exports become a consistent operating view for supply, production, delivery, and exception closure.",
    title: "Supply-Production-Delivery Visibility",
  },
  {
    align: "left",
    eyebrow: "Connected public systems",
    id: "system",
    kind: "project",
    label: "System",
    links: [
      {
        external: true,
        href: profile.github,
        label: "Explore GitHub",
      },
      {
        external: true,
        href: "https://github.com/Felix-Zuo/HulunGuard",
        label: "Open HulunGuard",
      },
    ],
    mediaProgress: mediaProgressAtFrame(793),
    metrics: [{ label: "Evidence standard", value: "Sanitized + synthetic" }],
    points: [
      "Factory Data Pocket Lab turns shop-floor evidence into reusable analysis.",
      "Six Sigma Study makes improvement methods practical and searchable.",
      "HulunGuard checks whether operational claims match available evidence.",
    ],
    stop: true,
    storyProgress: 0.85,
    summary:
      "Operations intelligence, manufacturing data literacy, Six Sigma learning, and evidence-first verification extend the same control logic.",
    title: "One operating method, several public tools.",
  },
  {
    align: "right",
    eyebrow: "Contact / final frame",
    id: "contact",
    kind: "finale",
    label: "Close",
    links: [
      {
        href: "#control",
        label: "Open control deck",
      },
      {
        href: `mailto:${profile.email}`,
        label: "Email Felix",
      },
    ],
    mediaProgress: mediaProgressAtFrame(877),
    metrics: [{ label: "Working mode", value: "Execution + tooling" }],
    stop: true,
    storyProgress: 0.95,
    summary:
      "The strongest fit is where manufacturing execution, launch readiness, and practical workflow tooling must work together.",
    title: "Build the next improvement loop.",
  },
];

function clamp(value: number, minimum = 0, maximum = 1) {
  return Math.min(Math.max(value, minimum), maximum);
}

function controlDeckProgressAtStoryProgress(progress: number) {
  return clamp(
    (progress - CONTROL_DECK_REVEAL_START) /
      (1 - CONTROL_DECK_REVEAL_START),
  );
}

function smoothstep(progress: number) {
  const bounded = clamp(progress);
  return bounded * bounded * (3 - 2 * bounded);
}

function controlTransitionAtStoryProgress(progress: number) {
  const transition = controlDeckProgressAtStoryProgress(progress);
  const blackout = Math.pow(Math.sin(Math.PI * transition), 0.72);
  const roomOpacity = smoothstep((transition - 0.36) / 0.42);
  const journeyOpacity = 1 - smoothstep(transition / 0.58);

  return { blackout, journeyOpacity, roomOpacity, transition };
}

function storyProgressAtChapter(
  chapter: RenderedJourneyChapter,
  index: number,
  chapterCount: number,
) {
  return clamp(chapter.storyProgress ?? index / Math.max(chapterCount, 1));
}

function mediaProgressAtStoryProgress(
  progress: number,
  chapters: readonly RenderedJourneyChapter[],
) {
  const boundedProgress = clamp(progress);
  const anchors = chapters.map((chapter, index) => ({
    media: clamp(chapter.mediaProgress),
    story: storyProgressAtChapter(chapter, index, chapters.length),
  }));

  if (anchors.length === 0) return boundedProgress;

  const lastAnchor = anchors[anchors.length - 1];
  if (lastAnchor.story < 1) anchors.push({ media: 1, story: 1 });

  const nextIndex = anchors.findIndex(
    (anchor) => anchor.story >= boundedProgress,
  );
  if (nextIndex <= 0) return anchors[0].media;

  const previous = anchors[nextIndex - 1];
  const next = anchors[nextIndex];
  const span = Math.max(next.story - previous.story, Number.EPSILON);
  const localProgress = clamp(
    (boundedProgress - previous.story) / span,
  );

  return previous.media + (next.media - previous.media) * localProgress;
}

function chapterPresentationAtProgress(
  progress: number,
  chapters: readonly RenderedJourneyChapter[],
) {
  const index = nearestChapterIndex(progress, chapters);
  const anchor = storyProgressAtChapter(
    chapters[index],
    index,
    chapters.length,
  );
  const adjacentIndex = progress >= anchor ? index + 1 : index - 1;
  const adjacent = chapters[adjacentIndex];
  const boundaryDistance = adjacent
    ? Math.abs(
        storyProgressAtChapter(adjacent, adjacentIndex, chapters.length) -
          anchor,
      ) / 2
    : Math.max(index === 0 ? anchor + 0.08 : 1 - anchor, 0.08);
  const signedDistance = progress - anchor;
  const distance = clamp(
    Math.abs(signedDistance) / Math.max(boundaryDistance, Number.EPSILON),
  );
  const edge = smoothstep(distance);

  return {
    index,
    opacity: 1 - edge * 0.66,
    shift: clamp(signedDistance / Math.max(boundaryDistance, 0.001), -1, 1),
  };
}

function storyProgressAtMediaProgress(
  progress: number,
  chapters: readonly RenderedJourneyChapter[],
) {
  const target = clamp(progress);
  let minimum = 0;
  let maximum = 1;

  for (let iteration = 0; iteration < 18; iteration += 1) {
    const candidate = (minimum + maximum) / 2;
    if (mediaProgressAtStoryProgress(candidate, chapters) < target) {
      minimum = candidate;
    } else {
      maximum = candidate;
    }
  }

  return (minimum + maximum) / 2;
}

function nearestChapterIndex(
  progress: number,
  chapters: readonly RenderedJourneyChapter[],
) {
  const boundedProgress = clamp(progress);
  let nearestIndex = 0;
  let nearestDistance = Number.POSITIVE_INFINITY;

  chapters.forEach((chapter, index) => {
    const chapterProgress = storyProgressAtChapter(
      chapter,
      index,
      chapters.length,
    );
    const distance = Math.abs(chapterProgress - boundedProgress);
    if (distance >= nearestDistance) return;

    nearestDistance = distance;
    nearestIndex = index;
  });

  return nearestIndex;
}

function frameAtMediaProgress(progress: number) {
  return Math.round(clamp(progress) * (RENDERED_FRAME_COUNT - 1)) + 1;
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

function normalizeWheelDelta(event: WheelEvent) {
  if (event.deltaMode === WheelEvent.DOM_DELTA_LINE) return event.deltaY * 16;
  if (event.deltaMode === WheelEvent.DOM_DELTA_PAGE) return event.deltaY * window.innerHeight;
  return event.deltaY;
}

function wheelProgressDelta(event: WheelEvent) {
  const delta = normalizeWheelDelta(event);
  const direction = Math.sign(delta);
  const magnitude = Math.abs(delta);
  if (direction === 0 || magnitude === 0) return 0;

  const normalizedMagnitude =
    magnitude < 12
      ? magnitude / 12
      : Math.min(1.35, Math.sqrt(magnitude / 100));

  return direction * normalizedMagnitude * WHEEL_PROGRESS_STEP;
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

function useCinematicMediaProfile(mobileMediaQuery: string) {
  const [mediaProfile, setMediaProfile] =
    useState<CinematicMediaProfile | null>(null);

  useEffect(() => {
    const query = window.matchMedia(mobileMediaQuery);
    const updateProfile = () =>
      setMediaProfile(query.matches ? "mobile" : "desktop");

    updateProfile();
    query.addEventListener("change", updateProfile);
    return () => query.removeEventListener("change", updateProfile);
  }, [mobileMediaQuery]);

  return mediaProfile;
}

function ChapterLink({
  link,
  onControlOpen,
}: {
  link: RenderedJourneyLink;
  onControlOpen?: () => void;
}) {
  const content = (
    <>
      <span>{link.label}</span>
      <ArrowUpRight aria-hidden="true" size={15} strokeWidth={1.8} />
    </>
  );

  if (link.external) {
    return (
      <a className={styles.chapterLink} href={link.href} rel="noreferrer" target="_blank">
        {content}
      </a>
    );
  }

  if (
    link.href.startsWith("#") ||
    link.href.startsWith("mailto:") ||
    link.href.startsWith("tel:")
  ) {
    if (link.href === "#control" && onControlOpen) {
      return (
        <button className={styles.chapterLink} onClick={onControlOpen} type="button">
          {content}
        </button>
      );
    }

    return (
      <a className={styles.chapterLink} href={link.href}>
        {content}
      </a>
    );
  }

  return (
    <Link className={styles.chapterLink} href={link.href}>
      {content}
    </Link>
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
  const initialProgress = storyProgressAtChapter(
    chapterList[initialIndex],
    initialIndex,
    chapterList.length,
  );
  const initialPresentation = chapterPresentationAtProgress(
    initialProgress,
    chapterList,
  );
  const initialTransition = controlTransitionAtStoryProgress(initialProgress);
  const initialControlDeckActive =
    initialProgress >= CONTROL_DECK_ACTIVE_PROGRESS;
  const initialControlDeckVisible = initialTransition.transition > 0;
  const reducedMotion = useReducedMotionPreference();
  const isStatic = reducedMotion === true;
  const mediaProfile = useCinematicMediaProfile(mobileMediaQuery);
  const selectedMainSrc =
    mediaProfile === "mobile" ? mobileSrc : desktopSrc;
  const assetManifest = useMemo(
    () =>
      mediaProfile
        ? createCinematicAssetManifest(mediaProfile)
        : [],
    [mediaProfile],
  );
  const preloader = useCinematicPreloader(
    assetManifest,
    reducedMotion === false && mediaProfile !== null,
  );
  const [isVideoReady, setIsVideoReady] = useState(false);
  const [videoFailed, setVideoFailed] = useState(false);
  const supportingAssetsReady =
    isStatic ||
    (mediaProfile !== null &&
      preloader.ready &&
      assetManifest.every((asset) => Boolean(preloader.urls[asset.key])));
  const assetsReady = isStatic || (supportingAssetsReady && isVideoReady);
  const loadingProgress = isStatic
    ? 1
    : clamp(preloader.progress * 0.42 + (isVideoReady ? 0.58 : 0.08));
  const rootStyle = useMemo(
    () =>
      ({
        "--chapter-count": chapterList.length,
        "--chapter-opacity": (
          initialPresentation.opacity * initialTransition.journeyOpacity
        ).toFixed(5),
        "--chapter-shift": `${(initialPresentation.shift * 14).toFixed(2)}px`,
        "--control-blackout": initialTransition.blackout.toFixed(5),
        "--control-progress": initialTransition.transition.toFixed(5),
        "--control-room-opacity": initialTransition.roomOpacity.toFixed(5),
        "--journey-ui-opacity": initialTransition.journeyOpacity.toFixed(5),
        "--journey-progress": initialProgress.toFixed(5),
      }) as CSSProperties,
    [chapterList.length, initialPresentation, initialProgress, initialTransition],
  );
  const instanceId = useId().replaceAll(":", "");
  const rootRef = useRef<HTMLElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const frameReadoutRef = useRef<HTMLSpanElement>(null);
  const timecodeReadoutRef = useRef<HTMLSpanElement>(null);
  const durationRef = useRef(0);
  const lastReverseSeekRef = useRef(0);
  const lastRenderedProgressRef = useRef(Number.NaN);
  const mainPlayPendingRef = useRef(false);
  const timelineRef = useRef<TimelineState>({
    current: initialProgress,
    target: initialProgress,
  });
  const touchYRef = useRef<number | null>(null);
  const chaptersRef = useRef(chapterList);
  const onChapterChangeRef = useRef(onChapterChange);
  const activeIndexRef = useRef(initialIndex);
  const controlDeckActiveRef = useRef(initialControlDeckActive);
  const controlDeckVisibleRef = useRef(initialControlDeckVisible);
  const chapterNavigationRef = useRef(false);
  const [activeIndex, setActiveIndex] = useState(initialIndex);
  const [controlDeckActive, setControlDeckActive] = useState(
    initialControlDeckActive,
  );
  const [controlDeckVisible, setControlDeckVisible] = useState(
    initialControlDeckVisible,
  );
  const resolvedMainSrc = mediaProfile ? selectedMainSrc : undefined;

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

  const commitControlDeckActive = useCallback((active: boolean) => {
    if (controlDeckActiveRef.current === active) return;
    controlDeckActiveRef.current = active;
    setControlDeckActive(active);
  }, []);

  const commitControlDeckVisible = useCallback((visible: boolean) => {
    if (controlDeckVisibleRef.current === visible) return;
    controlDeckVisibleRef.current = visible;
    setControlDeckVisible(visible);
  }, []);

  const updatePresentation = useCallback((progress: number) => {
    const root = rootRef.current;
    if (!root) return;

    const presentation = chapterPresentationAtProgress(
      progress,
      chaptersRef.current,
    );
    const transition = controlTransitionAtStoryProgress(progress);
    root.style.setProperty("--journey-progress", progress.toFixed(5));
    root.style.setProperty(
      "--chapter-opacity",
      (presentation.opacity * transition.journeyOpacity).toFixed(5),
    );
    root.style.setProperty(
      "--chapter-shift",
      `${(presentation.shift * 14).toFixed(2)}px`,
    );
    root.style.setProperty(
      "--control-progress",
      transition.transition.toFixed(5),
    );
    root.style.setProperty(
      "--control-blackout",
      transition.blackout.toFixed(5),
    );
    root.style.setProperty(
      "--control-room-opacity",
      transition.roomOpacity.toFixed(5),
    );
    root.style.setProperty(
      "--journey-ui-opacity",
      transition.journeyOpacity.toFixed(5),
    );
    commitActiveChapter(presentation.index);
    commitControlDeckVisible(transition.transition > 0.01);
    commitControlDeckActive(progress >= CONTROL_DECK_ACTIVE_PROGRESS);
  }, [commitActiveChapter, commitControlDeckActive, commitControlDeckVisible]);

  const seekToProgress = useCallback((progress: number, force = false) => {
    const video = videoRef.current;
    if (!video || video.readyState < HTMLMediaElement.HAVE_METADATA) return;

    const duration = durationRef.current || video.duration;
    if (!Number.isFinite(duration) || duration <= 0) return;

    const mediaProgress = mediaProgressAtStoryProgress(
      progress,
      chaptersRef.current,
    );
    const targetTime =
      progress <= TIMELINE_SETTLE_RADIUS
        ? Math.min(INITIAL_MEDIA_OFFSET_SECONDS, duration)
        : Math.min(
            mediaProgress * duration,
            Math.max(duration - 1 / RENDERED_FPS, 0),
          );
    if (!force && Math.abs(video.currentTime - targetTime) < 1 / RENDERED_FPS) return;

    video.pause();
    video.currentTime = targetTime;
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
      chapterNavigationRef.current = false;
      const mediaProgress = mediaProgressAtStoryProgress(
        boundedProgress,
        chaptersRef.current,
      );
      timelineRef.current.current = boundedProgress;
      timelineRef.current.target = boundedProgress;
      lastRenderedProgressRef.current = boundedProgress;
      updatePresentation(boundedProgress);
      seekToProgress(boundedProgress, true);
      updateTimelineReadout(mediaProgress);
    },
    [
      seekToProgress,
      updatePresentation,
      updateTimelineReadout,
    ],
  );

  const applyInputDelta = useCallback(
    (delta: number) => {
      if (!Number.isFinite(delta) || delta === 0) return;

      const timeline = timelineRef.current;
      chapterNavigationRef.current = false;
      timeline.target = clamp(timeline.target + delta);
    },
    [],
  );

  const goToProgress = useCallback(
    (progress: number) => {
      const boundedProgress = clamp(progress);
      chapterNavigationRef.current = true;
      timelineRef.current.target = boundedProgress;

      if (reducedMotion === true) {
        renderProgressImmediately(boundedProgress);
      }
    },
    [reducedMotion, renderProgressImmediately],
  );

  const goToChapter = useCallback(
    (index: number) => {
      const chapterCount = chaptersRef.current.length;
      const boundedIndex = clamp(Math.round(index), 0, chapterCount - 1);
      const chapter = chaptersRef.current[boundedIndex];
      const progress = storyProgressAtChapter(
        chapter,
        boundedIndex,
        chapterCount,
      );
      goToProgress(progress);
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

  const openControlDeck = useCallback(() => {
    window.history.replaceState(null, "", "#control");
    goToProgress(1);
  }, [goToProgress]);

  const returnFromControlDeck = useCallback(() => {
    goToChapter(chaptersRef.current.length - 1);
    if (window.location.hash === "#control") {
      window.history.replaceState(null, "", "#contact");
    }
  }, [goToChapter]);

  useEffect(() => {
    const followHash = () => {
      const hash = window.location.hash.slice(1);
      if (hash === "control") {
        timelineRef.current.target = 1;
        renderProgressImmediately(1);
        return;
      }

      const chapterIndex = HASH_CHAPTER_INDEX[hash];
      if (chapterIndex === undefined) return;

      const chapter = chaptersRef.current[chapterIndex];
      if (!chapter) return;

      const progress = storyProgressAtChapter(
        chapter,
        chapterIndex,
        chaptersRef.current.length,
      );
      timelineRef.current.target = progress;
      renderProgressImmediately(progress);
    };

    followHash();
    window.addEventListener("hashchange", followHash);
    return () => window.removeEventListener("hashchange", followHash);
  }, [renderProgressImmediately]);

  useEffect(() => {
    if (reducedMotion !== false || !resolvedMainSrc) return;

    const video = videoRef.current;
    if (!video) return;

    setIsVideoReady(false);
    setVideoFailed(false);
    durationRef.current = 0;
    video.pause();
    video.src = resolvedMainSrc;
    video.load();
  }, [reducedMotion, resolvedMainSrc]);

  useEffect(() => {
    if (reducedMotion !== false || !assetsReady) return;

    const root = rootRef.current;
    if (!root) return;

    const onWheel = (event: WheelEvent) => {
      if (event.ctrlKey || Math.abs(event.deltaX) > Math.abs(event.deltaY)) return;
      event.preventDefault();

      applyInputDelta(wheelProgressDelta(event));
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
      applyInputDelta(
        (deltaY / viewportHeight) * TOUCH_PROGRESS_PER_VIEWPORT,
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
    assetsReady,
    reducedMotion,
  ]);

  useEffect(() => {
    if (reducedMotion !== false || !assetsReady) return;

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
  }, [assetsReady, reducedMotion]);

  useEffect(() => {
    if (reducedMotion !== false || !assetsReady) return;

    let frame = 0;
    let previousTime = performance.now();

    const tick = (time: number) => {
      const deltaSeconds = Math.min(Math.max((time - previousTime) / 1000, 0), 0.05);
      previousTime = time;

      if (isVideoReady) {
        const timeline = timelineRef.current;
        const distance = timeline.target - timeline.current;
        const video = videoRef.current;
        const duration = durationRef.current;

        if (video && duration > 0 && distance > 0.00005) {
          const targetMediaProgress = mediaProgressAtStoryProgress(
            timeline.target,
            chaptersRef.current,
          );
          const targetTime = Math.min(
            targetMediaProgress * duration,
            Math.max(duration - 1 / RENDERED_FPS, 0),
          );

          const remainingSeconds = targetTime - video.currentTime;

          if (remainingSeconds > MAX_FORWARD_LEAD_SECONDS && !video.seeking) {
            const glideStart = Math.max(
              targetTime - FORWARD_GLIDE_SECONDS,
              0,
            );
            video.pause();
            video.currentTime = glideStart;
            timeline.current = Math.min(
              timeline.target,
              storyProgressAtMediaProgress(
                glideStart / duration,
                chaptersRef.current,
              ),
            );
          } else if (video.currentTime >= targetTime - 1 / RENDERED_FPS) {
            video.pause();
            video.playbackRate = 1;
            timeline.current = timeline.target;
          } else {
            const playbackCeiling = chapterNavigationRef.current ? 1.65 : 1.42;
            const desiredPlaybackRate = clamp(
              0.96 + remainingSeconds * 0.48,
              0.96,
              playbackCeiling,
            );
            const playbackFollow = 1 - Math.exp(-9 * deltaSeconds);
            video.playbackRate +=
              (desiredPlaybackRate - video.playbackRate) * playbackFollow;
            if (video.paused && !mainPlayPendingRef.current) {
              mainPlayPendingRef.current = true;
              void video
                .play()
                .catch(() => undefined)
                .finally(() => {
                  mainPlayPendingRef.current = false;
                });
            }
            const actualStoryProgress = storyProgressAtMediaProgress(
              video.currentTime / duration,
              chaptersRef.current,
            );
            timeline.current = Math.min(
              timeline.target,
              Math.max(timeline.current, actualStoryProgress),
            );
          }
        } else if (video && duration > 0 && distance < -0.00005) {
          video.pause();
          const navigatingToChapter = chapterNavigationRef.current;
          const followRate = navigatingToChapter
            ? CHAPTER_NAV_FOLLOW_RATE
            : FOLLOW_RATE;
          const maximumRate = navigatingToChapter
            ? timeline.current > CONTROL_DECK_REVEAL_START &&
              timeline.target <= CONTROL_DECK_REVEAL_START
              ? 0.065
              : CHAPTER_NAV_MAX_TIMELINE_RATE
            : MAX_TIMELINE_RATE;
          const follow = 1 - Math.exp(-followRate * deltaSeconds);
          const maximumStep = maximumRate * deltaSeconds;
          const followedStep = clamp(
            distance * follow,
            -maximumStep,
            maximumStep,
          );
          timeline.current += followedStep;

          if (time - lastReverseSeekRef.current >= REVERSE_SEEK_INTERVAL) {
            lastReverseSeekRef.current = time;
            seekToProgress(timeline.current);
          }
        } else {
          if (video && !video.paused) video.pause();
          if (video && video.playbackRate !== 1) video.playbackRate = 1;
          timeline.current = timeline.target;
        }
      }

      const timeline = timelineRef.current;
      const timelineSettled =
        Math.abs(timeline.target - timeline.current) <=
        TIMELINE_SETTLE_RADIUS;

      if (timelineSettled) {
        timeline.current = timeline.target;
        chapterNavigationRef.current = false;
      }

      const progress = timeline.current;
      const progressChanged =
        !Number.isFinite(lastRenderedProgressRef.current) ||
        Math.abs(progress - lastRenderedProgressRef.current) > 0.00001;

      if (progressChanged) {
        lastRenderedProgressRef.current = progress;
        const mediaProgress = mediaProgressAtStoryProgress(
          progress,
          chaptersRef.current,
        );
        updatePresentation(progress);
        updateTimelineReadout(mediaProgress);
      }

      frame = window.requestAnimationFrame(tick);
    };

    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, [
    assetsReady,
    isVideoReady,
    reducedMotion,
    seekToProgress,
    updatePresentation,
    updateTimelineReadout,
  ]);

  const handleKeyDown = (event: ReactKeyboardEvent<HTMLElement>) => {
    const target = event.target as HTMLElement;
    if (target !== event.currentTarget && target.closest("a, button, input, select, textarea")) {
      return;
    }

    if (event.key === "ArrowDown" || event.key === "ArrowRight" || event.key === "PageDown") {
      event.preventDefault();
      goToRelativeChapter(1);
      return;
    }

    if (event.key === "ArrowUp" || event.key === "ArrowLeft" || event.key === "PageUp") {
      event.preventDefault();
      goToRelativeChapter(-1);
      return;
    }

    if (event.key === "Home" || event.key === "End") {
      event.preventDefault();
      goToProgress(event.key === "Home" ? 0 : 1);
      return;
    }

  };

  const safeActiveIndex = clamp(activeIndex, 0, chapterList.length - 1);
  const activeChapter = chapterList[safeActiveIndex];
  const activeSignal = activeChapter.metrics?.[0];
  const activeKind = activeChapter.kind ?? "interlude";
  const isProjectChapter = activeKind === "project";
  const chapterTitleId = `${instanceId}-${activeChapter.id}-title`;
  const isFirstChapter = safeActiveIndex === 0;
  const isLastChapter = safeActiveIndex === chapterList.length - 1;
  const renderedFrame = frameAtMediaProgress(activeChapter.mediaProgress);
  const mediaState = isStatic
    ? "Static frame"
    : !assetsReady
      ? `Loading media ${Math.round(loadingProgress * 100)} percent`
      : videoFailed
        ? "Poster fallback"
        : isVideoReady
          ? "Rendered media"
          : "Loading media";

  return (
    <section
      aria-label={controlDeckActive ? "Felix Zuo operations control deck" : ariaLabel}
      aria-labelledby={controlDeckActive ? undefined : chapterTitleId}
      className={`${styles.root} ${isStatic ? styles.reducedMotion : ""} ${className}`.trim()}
      data-chapter-kind={activeKind}
      data-control-deck={controlDeckActive || undefined}
      data-loading={!assetsReady || undefined}
      data-panel-align={activeChapter.align ?? "left"}
      data-reduced-motion={isStatic || undefined}
      onKeyDown={handleKeyDown}
      ref={rootRef}
      style={rootStyle}
      tabIndex={0}
    >
      {!assetsReady && !isStatic && (
        <div
          aria-label={`正在载入 Felix 的作品集，${Math.round(loadingProgress * 100)}%`}
          aria-live="polite"
          className={styles.loadingGate}
          role="status"
        >
          <div className={styles.loadingIdentity}>
            <span>FZ / Manufacturing operations</span>
            <strong>正在载入 Felix 的作品集</strong>
            <p>
              {preloader.degraded
                ? "正在准备兼容模式"
                : "正在预载运镜、动态节点与控制室"}
            </p>
          </div>
          <div className={styles.loadingProgress}>
            <span
              aria-hidden="true"
              style={{ transform: `scaleX(${loadingProgress})` }}
            />
          </div>
          <output>{Math.round(loadingProgress * 100)}%</output>
        </div>
      )}

      <div
        aria-hidden="true"
        className={styles.media}
      >
        {/* The poster owns first paint; video loading starts only after motion preference is known. */}
        <picture
          className={`${styles.posterFrame} ${isVideoReady && !isStatic ? styles.posterHidden : ""}`}
        >
          <source media={mobileMediaQuery} srcSet={mobilePosterSrc} />
          <Image
            alt=""
            className={styles.poster}
            fill
            priority
            sizes="100vw"
            src={posterSrc}
            unoptimized
          />
        </picture>
        <video
          className={`${styles.video} ${isVideoReady && !isStatic ? styles.videoReady : ""}`}
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
          preload="auto"
          ref={videoRef}
          tabIndex={-1}
        />
        <div className={styles.shade} />
      </div>

      <div aria-hidden="true" className={styles.controlGate} />
      <JourneyControlDeck
        active={controlDeckActive}
        backdropSrc={preloader.urls["control-room"]}
        mediaUrls={preloader.urls}
        onReturn={returnFromControlDeck}
        taktVideoSrc={preloader.urls["takt-live"]}
        visible={controlDeckVisible}
      />

      {!controlDeckActive && (
        <>
      <header className={styles.meta}>
        <span>FZ / Manufacturing operations</span>
        <span>{activeChapter.label}</span>
        <span>Sanitized / synthetic</span>
      </header>
      <span aria-live="polite" className={styles.srOnly}>
        {mediaState}
      </span>

      <article
        aria-atomic="true"
        aria-live="polite"
        className={`${styles.chapter} ${styles[`chapter${activeKind[0].toUpperCase()}${activeKind.slice(1)}`]} ${activeChapter.align === "right" ? styles.chapterRight : ""}`}
        key={activeChapter.id}
      >
        <p className={styles.eyebrow}>
          <span>
            {String(safeActiveIndex + 1).padStart(2, "0")} /{" "}
            {String(chapterList.length).padStart(2, "0")}
          </span>
          {activeChapter.eyebrow}
        </p>
        <h1 className={styles.title} id={chapterTitleId}>
          {activeChapter.title}
        </h1>

        <div className={styles.chapterDetails}>
            <p className={styles.summary}>{activeChapter.summary}</p>

            {activeChapter.points && activeChapter.points.length > 0 && (
              <ol className={styles.projectPoints}>
                {activeChapter.points.map((point, index) => (
                  <li key={point}>
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <p>{point}</p>
                  </li>
                ))}
              </ol>
            )}

            <div className={styles.evidenceRow}>
              {activeSignal && (
                <dl className={styles.signal}>
                  <div>
                    <dt>{activeSignal.label}</dt>
                    <dd>{activeSignal.value}</dd>
                  </div>
                </dl>
              )}

              {activeChapter.links && activeChapter.links.length > 0 && (
                <div className={styles.chapterLinks}>
                  {activeChapter.links.map((link) => (
                    <ChapterLink
                      key={`${link.href}-${link.label}`}
                      link={link}
                      onControlOpen={openControlDeck}
                    />
                  ))}
                </div>
              )}
            </div>

            {(isProjectChapter || activeKind === "finale") && (
              <footer className={styles.slateFooter}>
                <span>38.000 SEC / 24 FPS</span>
                <span aria-hidden="true" className={styles.slateProgress} />
                <span ref={frameReadoutRef}>
                  {formatFrameLabel(renderedFrame)} / {RENDERED_FRAME_COUNT}
                </span>
                <span ref={timecodeReadoutRef}>{formatTimecode(renderedFrame)}</span>
              </footer>
            )}
          </div>
      </article>

      <div className={styles.controls}>
        <button
          aria-label="Previous chapter"
          className={styles.iconButton}
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
                    "--chapter-progress": storyProgressAtChapter(
                      chapter,
                      index,
                      chapterList.length,
                    ).toFixed(5),
                  } as CSSProperties
                }
              >
                <button
                  aria-current={index === safeActiveIndex ? "step" : undefined}
                  aria-label={`Go to chapter ${index + 1}: ${chapter.label}, ${formatFrameLabel(frameAtMediaProgress(chapter.mediaProgress))}`}
                  className={index === safeActiveIndex ? styles.activeStop : ""}
                  onClick={() => goToChapter(index)}
                  title={chapter.label}
                  type="button"
                />
              </li>
            ))}
          </ol>
        </nav>

        <button
          aria-label={isLastChapter ? "Open control deck" : "Next chapter"}
          className={styles.iconButton}
          disabled={isLastChapter && controlDeckActive}
          onClick={() =>
            isLastChapter ? openControlDeck() : goToRelativeChapter(1)
          }
          title={isLastChapter ? "Open control deck" : "Next chapter"}
          type="button"
        >
          <ChevronRight aria-hidden="true" size={18} />
        </button>
      </div>
        </>
      )}
    </section>
  );
}

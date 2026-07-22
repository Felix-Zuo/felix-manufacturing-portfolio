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
  type MouseEvent as ReactMouseEvent,
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
};

type ForwardNavigationState = {
  phase: "playing" | "covering" | "seeking";
  skipHandled: boolean;
  targetIndex: number;
  targetProgress: number;
  targetTime: number;
};

const DEFAULT_DESKTOP_SRC = "/media/felix-journey-stream-desktop.mp4?v=10";
const DEFAULT_MOBILE_SRC = "/media/felix-journey-stream-mobile.mp4?v=10";
const DEFAULT_POSTER_SRC = "/media/felix-journey-poster.webp?v=10";
const DEFAULT_MOBILE_POSTER_SRC = "/media/felix-journey-mobile-poster.webp?v=10";
const DEFAULT_MOBILE_MEDIA_QUERY = "(max-width: 767px)";
const CONTROL_DECK_REVEAL_START = 0.95;
const CONTROL_DECK_ACTIVE_PROGRESS = 0.9975;
const RENDERED_FPS = 24;
const RENDERED_FRAME_COUNT = 912;
const INITIAL_MEDIA_OFFSET_SECONDS = 0.1;
const TIMELINE_SETTLE_RADIUS = 0.00005;
const FRAME_TOLERANCE_SECONDS = 1 / RENDERED_FPS;
const CHAPTER_PLAYBACK_RATE = 1;
const COVER_FADE_MS = 220;
const COVER_SEEK_TIMEOUT_MS = 650;
const ROBOT_CLIP_SKIP_START_SECONDS = 4.38;
const ROBOT_CLIP_SKIP_END_SECONDS = 8.88;
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
  return (boundedFrame - 1) / RENDERED_FRAME_COUNT;
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
    mediaProgress: mediaProgressAtFrame(217),
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
  return clamp(
    Math.round(clamp(progress) * RENDERED_FRAME_COUNT) + 1,
    1,
    RENDERED_FRAME_COUNT,
  );
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
  const lastRenderedProgressRef = useRef(Number.NaN);
  const navigationRef = useRef<ForwardNavigationState | null>(null);
  const navigationTimerRefs = useRef(new Set<number>());
  const mountedRef = useRef(true);
  const isTransitioningRef = useRef(false);
  const timelineRef = useRef<TimelineState>({
    current: initialProgress,
  });
  const chaptersRef = useRef(chapterList);
  const onChapterChangeRef = useRef(onChapterChange);
  const activeIndexRef = useRef(initialIndex);
  const controlDeckActiveRef = useRef(initialControlDeckActive);
  const controlDeckVisibleRef = useRef(initialControlDeckVisible);
  const [activeIndex, setActiveIndex] = useState(initialIndex);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [transitionCoverVisible, setTransitionCoverVisible] = useState(false);
  const [controlDeckActive, setControlDeckActive] = useState(
    initialControlDeckActive,
  );
  const [controlDeckVisible, setControlDeckVisible] = useState(
    initialControlDeckVisible,
  );
  const resolvedMainSrc = mediaProfile ? selectedMainSrc : undefined;

  useEffect(() => {
    mountedRef.current = true;
    const navigationTimers = navigationTimerRefs.current;
    const video = videoRef.current;

    return () => {
      mountedRef.current = false;
      navigationTimers.forEach((timer) => window.clearTimeout(timer));
      navigationTimers.clear();
      video?.pause();
    };
  }, []);

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

  const updatePresentation = useCallback((progress: number, commitChapter = true) => {
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
    if (commitChapter) commitActiveChapter(presentation.index);
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
      const mediaProgress = mediaProgressAtStoryProgress(
        boundedProgress,
        chaptersRef.current,
      );
      timelineRef.current.current = boundedProgress;
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

  const scheduleNavigationTimer = useCallback(
    (callback: () => void, delay: number) => {
      const timer = window.setTimeout(() => {
        navigationTimerRefs.current.delete(timer);
        callback();
      }, delay);
      navigationTimerRefs.current.add(timer);
      return timer;
    },
    [],
  );

  const unlockNavigation = useCallback(() => {
    navigationRef.current = null;
    isTransitioningRef.current = false;
    if (!mountedRef.current) return;
    setIsTransitioning(false);
  }, []);

  const coveredJumpToProgress = useCallback(
    (progress: number) => {
      const boundedProgress = clamp(progress);

      if (reducedMotion === true || !isVideoReady) {
        renderProgressImmediately(boundedProgress);
        return;
      }
      if (isTransitioningRef.current) return;

      isTransitioningRef.current = true;
      setIsTransitioning(true);
      setTransitionCoverVisible(true);
      videoRef.current?.pause();

      scheduleNavigationTimer(() => {
        if (!mountedRef.current) return;
        renderProgressImmediately(boundedProgress);

        scheduleNavigationTimer(() => {
          if (!mountedRef.current) return;
          setTransitionCoverVisible(false);
          scheduleNavigationTimer(unlockNavigation, COVER_FADE_MS);
        }, 50);
      }, COVER_FADE_MS);
    },
    [
      isVideoReady,
      reducedMotion,
      renderProgressImmediately,
      scheduleNavigationTimer,
      unlockNavigation,
    ],
  );

  const playForwardToProgress = useCallback(
    (progress: number, targetIndex: number) => {
      const boundedProgress = clamp(progress);
      const video = videoRef.current;
      const duration = durationRef.current || video?.duration || 0;

      if (
        reducedMotion === true ||
        !isVideoReady ||
        !video ||
        !Number.isFinite(duration) ||
        duration <= 0
      ) {
        renderProgressImmediately(boundedProgress);
        return;
      }
      if (isTransitioningRef.current) return;

      const targetMediaProgress = mediaProgressAtStoryProgress(
        boundedProgress,
        chaptersRef.current,
      );
      const targetTime = Math.min(
        targetMediaProgress * duration,
        Math.max(duration - FRAME_TOLERANCE_SECONDS, 0),
      );

      if (targetTime <= video.currentTime + FRAME_TOLERANCE_SECONDS) {
        coveredJumpToProgress(boundedProgress);
        return;
      }

      navigationRef.current = {
        phase: "playing",
        skipHandled: false,
        targetIndex,
        targetProgress: boundedProgress,
        targetTime,
      };
      isTransitioningRef.current = true;
      setIsTransitioning(true);
      setTransitionCoverVisible(false);
      video.playbackRate = CHAPTER_PLAYBACK_RATE;
      void video
        .play()
        .catch(() => {
          renderProgressImmediately(boundedProgress);
          unlockNavigation();
        });
    },
    [
      coveredJumpToProgress,
      isVideoReady,
      reducedMotion,
      renderProgressImmediately,
      unlockNavigation,
    ],
  );

  const goToChapter = useCallback(
    (index: number) => {
      if (isTransitioningRef.current) return;

      const chapterCount = chaptersRef.current.length;
      const boundedIndex = clamp(Math.round(index), 0, chapterCount - 1);
      const currentIndex = activeIndexRef.current;
      if (boundedIndex === currentIndex && !controlDeckActiveRef.current) return;

      const chapter = chaptersRef.current[boundedIndex];
      const progress = storyProgressAtChapter(
        chapter,
        boundedIndex,
        chapterCount,
      );

      if (boundedIndex === currentIndex + 1 && !controlDeckActiveRef.current) {
        playForwardToProgress(progress, boundedIndex);
        return;
      }

      coveredJumpToProgress(progress);
    },
    [coveredJumpToProgress, playForwardToProgress],
  );

  const goToRelativeChapter = useCallback(
    (direction: -1 | 1) => {
      if (isTransitioningRef.current) return;
      goToChapter(activeIndexRef.current + direction);
    },
    [goToChapter],
  );

  const openControlDeck = useCallback(() => {
    if (isTransitioningRef.current || controlDeckActiveRef.current) return;
    window.history.replaceState(null, "", "#control");
    playForwardToProgress(1, chaptersRef.current.length - 1);
  }, [playForwardToProgress]);

  const returnFromControlDeck = useCallback(() => {
    const chapterIndex = chaptersRef.current.length - 1;
    const chapter = chaptersRef.current[chapterIndex];
    const progress = storyProgressAtChapter(
      chapter,
      chapterIndex,
      chaptersRef.current.length,
    );
    coveredJumpToProgress(progress);
    if (window.location.hash === "#control") {
      window.history.replaceState(null, "", "#contact");
    }
  }, [coveredJumpToProgress]);

  useEffect(() => {
    const followHash = (animate: boolean) => {
      const hash = window.location.hash.slice(1);
      if (hash === "control") {
        if (animate) {
          coveredJumpToProgress(1);
        } else {
          renderProgressImmediately(1);
        }
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
      if (animate) {
        coveredJumpToProgress(progress);
      } else {
        renderProgressImmediately(progress);
      }
    };

    const handleHashChange = () => followHash(true);
    followHash(false);
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, [coveredJumpToProgress, renderProgressImmediately]);

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
      if (event.ctrlKey) return;
      event.preventDefault();
    };

    root.addEventListener("wheel", onWheel, { passive: false });

    return () => {
      root.removeEventListener("wheel", onWheel);
    };
  }, [assetsReady, reducedMotion]);

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
    if (
      reducedMotion !== false ||
      !assetsReady ||
      !isVideoReady ||
      !isTransitioning
    ) {
      return;
    }

    const video = videoRef.current;
    const duration = durationRef.current || video?.duration || 0;
    if (!video || !Number.isFinite(duration) || duration <= 0) return;

    let frame = 0;
    let coverTimer = 0;
    let seekFallbackTimer = 0;
    let seekListener: (() => void) | null = null;
    let skipResumed = false;

    const completeNavigation = () => {
      const navigation = navigationRef.current;
      if (!navigation) return;

      video.pause();
      video.playbackRate = CHAPTER_PLAYBACK_RATE;
      if (
        Math.abs(video.currentTime - navigation.targetTime) >
        FRAME_TOLERANCE_SECONDS
      ) {
        video.currentTime = navigation.targetTime;
      }

      const targetMediaProgress = mediaProgressAtStoryProgress(
        navigation.targetProgress,
        chaptersRef.current,
      );
      timelineRef.current.current = navigation.targetProgress;
      lastRenderedProgressRef.current = navigation.targetProgress;
      updatePresentation(navigation.targetProgress, true);
      updateTimelineReadout(targetMediaProgress);
      setTransitionCoverVisible(false);
      unlockNavigation();
    };

    const resumeAfterRobotSkip = () => {
      if (skipResumed || !mountedRef.current || !navigationRef.current) return;
      skipResumed = true;
      if (seekListener) video.removeEventListener("seeked", seekListener);
      if (seekFallbackTimer) window.clearTimeout(seekFallbackTimer);

      const navigation = navigationRef.current;
      const mediaProgress = clamp(video.currentTime / duration);
      const progress = Math.min(
        navigation.targetProgress,
        storyProgressAtMediaProgress(mediaProgress, chaptersRef.current),
      );
      timelineRef.current.current = progress;
      lastRenderedProgressRef.current = progress;
      updatePresentation(progress, false);
      updateTimelineReadout(mediaProgress);
      setTransitionCoverVisible(false);
      navigation.phase = "playing";

      if (
        video.currentTime >=
        navigation.targetTime - FRAME_TOLERANCE_SECONDS
      ) {
        completeNavigation();
        return;
      }

      void video
        .play()
        .catch(completeNavigation);
    };

    const beginRobotSkip = () => {
      const navigation = navigationRef.current;
      if (!navigation || navigation.skipHandled) return;

      navigation.skipHandled = true;
      navigation.phase = "covering";
      video.pause();
      setTransitionCoverVisible(true);

      coverTimer = window.setTimeout(() => {
        const currentNavigation = navigationRef.current;
        if (!currentNavigation || !mountedRef.current) return;

        currentNavigation.phase = "seeking";
        seekListener = resumeAfterRobotSkip;
        video.addEventListener("seeked", seekListener, { once: true });
        video.currentTime = Math.min(
          ROBOT_CLIP_SKIP_END_SECONDS,
          currentNavigation.targetTime,
        );
        seekFallbackTimer = window.setTimeout(
          resumeAfterRobotSkip,
          COVER_SEEK_TIMEOUT_MS,
        );
      }, COVER_FADE_MS);
    };

    const tick = () => {
      const navigation = navigationRef.current;
      if (!navigation) return;

      if (navigation.phase === "playing") {
        const mediaProgress = clamp(video.currentTime / duration);
        const progress = Math.min(
          navigation.targetProgress,
          storyProgressAtMediaProgress(mediaProgress, chaptersRef.current),
        );
        timelineRef.current.current = progress;

        if (
          !Number.isFinite(lastRenderedProgressRef.current) ||
          Math.abs(progress - lastRenderedProgressRef.current) > 0.00001
        ) {
          lastRenderedProgressRef.current = progress;
          updatePresentation(progress, false);
          updateTimelineReadout(mediaProgress);
        }

        const skipRobotHandoff =
          activeIndexRef.current === 0 &&
          navigation.targetIndex === 1 &&
          navigation.targetTime > ROBOT_CLIP_SKIP_END_SECONDS;

        if (
          skipRobotHandoff &&
          !navigation.skipHandled &&
          video.currentTime >= ROBOT_CLIP_SKIP_START_SECONDS
        ) {
          beginRobotSkip();
        } else if (
          video.currentTime >=
          navigation.targetTime - FRAME_TOLERANCE_SECONDS
        ) {
          completeNavigation();
          return;
        }
      }

      frame = window.requestAnimationFrame(tick);
    };

    frame = window.requestAnimationFrame(tick);
    return () => {
      window.cancelAnimationFrame(frame);
      if (coverTimer) window.clearTimeout(coverTimer);
      if (seekFallbackTimer) window.clearTimeout(seekFallbackTimer);
      if (seekListener) video.removeEventListener("seeked", seekListener);
    };
  }, [
    assetsReady,
    isVideoReady,
    isTransitioning,
    reducedMotion,
    unlockNavigation,
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
      if (activeIndexRef.current === chaptersRef.current.length - 1) {
        openControlDeck();
      } else {
        goToRelativeChapter(1);
      }
      return;
    }

    if (event.key === "ArrowUp" || event.key === "ArrowLeft" || event.key === "PageUp") {
      event.preventDefault();
      goToRelativeChapter(-1);
      return;
    }

    if (event.key === "Home" || event.key === "End") {
      event.preventDefault();
      goToChapter(event.key === "Home" ? 0 : chaptersRef.current.length - 1);
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (activeIndexRef.current === chaptersRef.current.length - 1) {
        openControlDeck();
      } else {
        goToRelativeChapter(1);
      }
    }
  };

  const handleSceneClick = (event: ReactMouseEvent<HTMLElement>) => {
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      isTransitioningRef.current ||
      controlDeckActiveRef.current ||
      !assetsReady
    ) {
      return;
    }

    const target = event.target as HTMLElement;
    if (target.closest("a, button, input, select, textarea, [role='button']")) {
      return;
    }
    if (window.getSelection()?.toString()) return;

    if (activeIndexRef.current === chaptersRef.current.length - 1) {
      openControlDeck();
    } else {
      goToRelativeChapter(1);
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
      data-transition-cover={transitionCoverVisible || undefined}
      data-transitioning={isTransitioning || undefined}
      aria-busy={isTransitioning || !assetsReady}
      onClick={handleSceneClick}
      onKeyDown={handleKeyDown}
      ref={rootRef}
      style={rootStyle}
      tabIndex={0}
    >
      {!assetsReady && !isStatic && (
        <div
          aria-label={`Loading Felix Zuo's portfolio, ${Math.round(loadingProgress * 100)}%`}
          aria-live="polite"
          className={styles.loadingGate}
          role="status"
        >
          <div className={styles.loadingIdentity}>
            <span>FZ / Manufacturing operations</span>
            <strong>Loading Felix Zuo&apos;s portfolio</strong>
            <p>
              {preloader.degraded
                ? "Preparing compatibility mode"
                : "Preloading the film, chapter holds, and control room"}
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

      <div aria-hidden="true" className={styles.chapterCut} />
      <div aria-hidden="true" className={styles.controlGate} />
      <JourneyControlDeck
        active={controlDeckActive}
        backdropSrc={preloader.urls["control-room"]}
        onReturn={returnFromControlDeck}
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
          disabled={isFirstChapter || isTransitioning}
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
                  disabled={isTransitioning}
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
          disabled={isTransitioning || (isLastChapter && controlDeckActive)}
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

"use client";

import {
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  Pause,
  Play,
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

import { JourneyControlDeck } from "./JourneyControlDeck";
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

const DEFAULT_DESKTOP_SRC = "/media/felix-journey-desktop.mp4";
const DEFAULT_MOBILE_SRC = "/media/felix-journey-mobile.mp4";
const DEFAULT_POSTER_SRC = "/media/felix-journey-poster.webp";
const DEFAULT_MOBILE_POSTER_SRC = "/media/felix-journey-mobile-poster.webp";
const DEFAULT_MOBILE_MEDIA_QUERY = "(max-width: 767px)";
const FOLLOW_RATE = 4.2;
const MAX_TIMELINE_RATE = 0.045;
const WHEEL_PROGRESS_STEP = 0.0052;
const TOUCH_PROGRESS_PER_VIEWPORT = 0.12;
const PROJECT_FOCUS_RADIUS = 0.024;
const INPUT_IDLE_MILLISECONDS = 260;
const CONTROL_DECK_REVEAL_START = 0.978;
const CONTROL_DECK_ACTIVE_PROGRESS = 0.988;
const RENDERED_FPS = 24;
const RENDERED_FRAME_COUNT = 912;
const SEEK_EPSILON_SECONDS = 1 / 90;
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
        href: "https://felix-zuo.github.io/HulunGuard/",
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

function storyProgressAtChapter(
  chapter: RenderedJourneyChapter,
  index: number,
  chapterCount: number,
) {
  return clamp(chapter.storyProgress ?? index / Math.max(chapterCount, 1));
}

function pacedEase(progress: number) {
  const bounded = clamp(progress);
  const smooth = bounded * bounded * (3 - 2 * bounded);
  return bounded * 0.35 + smooth * 0.65;
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
  const localProgress = pacedEase(
    (boundedProgress - previous.story) / span,
  );

  return previous.media + (next.media - previous.media) * localProgress;
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

function focusedProjectIndexAtProgress(
  progress: number,
  chapters: readonly RenderedJourneyChapter[],
) {
  let focusedIndex: number | null = null;
  let focusedDistance = PROJECT_FOCUS_RADIUS;

  chapters.forEach((chapter, index) => {
    if (!chapter.stop) return;

    const distance = Math.abs(
      storyProgressAtChapter(chapter, index, chapters.length) - progress,
    );
    if (distance > focusedDistance) return;

    focusedDistance = distance;
    focusedIndex = index;
  });

  return focusedIndex;
}

function crossedProjectStopIndex(
  fromProgress: number,
  toProgress: number,
  chapters: readonly RenderedJourneyChapter[],
) {
  const direction = Math.sign(toProgress - fromProgress);
  if (direction === 0) return null;

  const candidates = chapters
    .map((chapter, index) => ({
      index,
      progress: storyProgressAtChapter(chapter, index, chapters.length),
      stop: chapter.stop === true,
    }))
    .filter(({ progress, stop }) => {
      if (!stop) return false;
      return direction > 0
        ? progress > fromProgress && progress <= toProgress
        : progress < fromProgress && progress >= toProgress;
    })
    .sort((first, second) =>
      direction > 0
        ? first.progress - second.progress
        : second.progress - first.progress,
    );

  return candidates[0]?.index ?? null;
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

function ChapterLink({ link }: { link: RenderedJourneyLink }) {
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
  const initialFocusedProjectIndex = focusedProjectIndexAtProgress(
    initialProgress,
    chapterList,
  );
  const initialControlDeckActive =
    initialProgress >= CONTROL_DECK_ACTIVE_PROGRESS;
  const rootStyle = useMemo(
    () =>
      ({
        "--chapter-count": chapterList.length,
        "--control-progress": controlDeckProgressAtStoryProgress(
          initialProgress,
        ).toFixed(5),
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
  const touchYRef = useRef<number | null>(null);
  const chaptersRef = useRef(chapterList);
  const onChapterChangeRef = useRef(onChapterChange);
  const activeIndexRef = useRef(initialIndex);
  const focusedProjectIndexRef = useRef<number | null>(initialFocusedProjectIndex);
  const magneticStopIndexRef = useRef<number | null>(null);
  const controlDeckActiveRef = useRef(initialControlDeckActive);
  const stopReleaseReadyRef = useRef(false);
  const inputIdleTimerRef = useRef<number | null>(null);
  const pausedRef = useRef(false);
  const [activeIndex, setActiveIndex] = useState(initialIndex);
  const [focusedProjectIndex, setFocusedProjectIndex] = useState<number | null>(
    initialFocusedProjectIndex,
  );
  const [magneticStopIndex, setMagneticStopIndex] = useState<number | null>(null);
  const [controlDeckActive, setControlDeckActive] = useState(
    initialControlDeckActive,
  );
  const [isPaused, setIsPaused] = useState(false);
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

  const commitFocusedProject = useCallback((index: number | null) => {
    if (focusedProjectIndexRef.current === index) return;
    focusedProjectIndexRef.current = index;
    setFocusedProjectIndex(index);
  }, []);

  const commitMagneticStop = useCallback((index: number | null) => {
    if (magneticStopIndexRef.current === index) return;
    magneticStopIndexRef.current = index;
    stopReleaseReadyRef.current = false;
    setMagneticStopIndex(index);
  }, []);

  const commitControlDeckActive = useCallback((active: boolean) => {
    if (controlDeckActiveRef.current === active) return;
    controlDeckActiveRef.current = active;
    setControlDeckActive(active);
  }, []);

  const scheduleInputIdle = useCallback(() => {
    if (inputIdleTimerRef.current !== null) {
      window.clearTimeout(inputIdleTimerRef.current);
    }

    inputIdleTimerRef.current = window.setTimeout(() => {
      inputIdleTimerRef.current = null;
      if (magneticStopIndexRef.current !== null) {
        stopReleaseReadyRef.current = true;
      }
    }, INPUT_IDLE_MILLISECONDS);
  }, []);

  useEffect(
    () => () => {
      if (inputIdleTimerRef.current !== null) {
        window.clearTimeout(inputIdleTimerRef.current);
      }
    },
    [],
  );

  const seekToProgress = useCallback((progress: number) => {
    const video = videoRef.current;
    if (!video || video.readyState < HTMLMediaElement.HAVE_METADATA) return;

    const duration = durationRef.current || video.duration;
    if (!Number.isFinite(duration) || duration <= 0) return;

    const frameDuration = duration / RENDERED_FRAME_COUNT;
    const maximumTime = Math.max(duration - frameDuration, 0);
    const mediaProgress = mediaProgressAtStoryProgress(
      progress,
      chaptersRef.current,
    );
    const nextTime = maximumTime * mediaProgress;

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
      const mediaProgress = mediaProgressAtStoryProgress(
        boundedProgress,
        chaptersRef.current,
      );
      timelineRef.current.current = boundedProgress;
      rootRef.current?.style.setProperty(
        "--journey-progress",
        boundedProgress.toFixed(5),
      );
      rootRef.current?.style.setProperty(
        "--control-progress",
        controlDeckProgressAtStoryProgress(boundedProgress).toFixed(5),
      );
      seekToProgress(boundedProgress);
      updateTimelineReadout(mediaProgress);
      commitActiveChapter(
        nearestChapterIndex(boundedProgress, chaptersRef.current),
      );
      commitFocusedProject(
        focusedProjectIndexAtProgress(
          boundedProgress,
          chaptersRef.current,
        ),
      );
      commitControlDeckActive(
        boundedProgress >= CONTROL_DECK_ACTIVE_PROGRESS,
      );
    },
    [
      commitActiveChapter,
      commitControlDeckActive,
      commitFocusedProject,
      seekToProgress,
      updateTimelineReadout,
    ],
  );

  const applyInputDelta = useCallback(
    (delta: number) => {
      if (pausedRef.current || !Number.isFinite(delta) || delta === 0) return;

      const lockedStop = magneticStopIndexRef.current;
      if (lockedStop !== null) {
        if (!stopReleaseReadyRef.current) {
          scheduleInputIdle();
          return;
        }
        commitMagneticStop(null);
      }

      const timeline = timelineRef.current;
      const nextTarget = clamp(timeline.target + delta);
      const crossedStop = crossedProjectStopIndex(
        timeline.target,
        nextTarget,
        chaptersRef.current,
      );

      if (crossedStop !== null) {
        timeline.target = storyProgressAtChapter(
          chaptersRef.current[crossedStop],
          crossedStop,
          chaptersRef.current.length,
        );
        commitMagneticStop(crossedStop);
      } else {
        timeline.target = nextTarget;
      }

      scheduleInputIdle();
    },
    [commitMagneticStop, scheduleInputIdle],
  );

  const goToProgress = useCallback(
    (progress: number) => {
      const boundedProgress = clamp(progress);
      commitMagneticStop(null);
      timelineRef.current.target = boundedProgress;

      if (pausedRef.current || reducedMotion === true) {
        renderProgressImmediately(boundedProgress);
      }
    },
    [commitMagneticStop, reducedMotion, renderProgressImmediately],
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
      if (chapter.stop) {
        commitMagneticStop(boundedIndex);
        scheduleInputIdle();
      }
    },
    [commitMagneticStop, goToProgress, scheduleInputIdle],
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
        commitMagneticStop(null);
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
      commitMagneticStop(chapter.stop ? chapterIndex : null);
      if (chapter.stop) scheduleInputIdle();
    };

    followHash();
    window.addEventListener("hashchange", followHash);
    return () => window.removeEventListener("hashchange", followHash);
  }, [commitMagneticStop, renderProgressImmediately, scheduleInputIdle]);

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
    reducedMotion,
  ]);

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
        const maximumStep = MAX_TIMELINE_RATE * deltaSeconds;
        const followedStep = clamp(
          distance * follow,
          -maximumStep,
          maximumStep,
        );

        timeline.current =
          Math.abs(distance) < 0.00005
            ? timeline.target
            : timeline.current + followedStep;
      }

      const progress = timelineRef.current.current;
      const mediaProgress = mediaProgressAtStoryProgress(
        progress,
        chaptersRef.current,
      );
      rootRef.current?.style.setProperty(
        "--journey-progress",
        progress.toFixed(5),
      );
      rootRef.current?.style.setProperty(
        "--control-progress",
        controlDeckProgressAtStoryProgress(progress).toFixed(5),
      );
      seekToProgress(progress);
      updateTimelineReadout(mediaProgress);
      commitActiveChapter(
        nearestChapterIndex(progress, chaptersRef.current),
      );
      commitFocusedProject(
        focusedProjectIndexAtProgress(progress, chaptersRef.current),
      );
      commitControlDeckActive(progress >= CONTROL_DECK_ACTIVE_PROGRESS);
      frame = window.requestAnimationFrame(tick);
    };

    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, [
    commitActiveChapter,
    commitControlDeckActive,
    commitFocusedProject,
    reducedMotion,
    seekToProgress,
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

    if (event.key === " " && !isStatic) {
      event.preventDefault();
      togglePaused();
    }
  };

  const safeActiveIndex = clamp(activeIndex, 0, chapterList.length - 1);
  const activeChapter = chapterList[safeActiveIndex];
  const activeSignal = activeChapter.metrics?.[0];
  const activeKind = activeChapter.kind ?? "interlude";
  const isProjectChapter = activeKind === "project";
  const isProjectFocused =
    isProjectChapter && focusedProjectIndex === safeActiveIndex;
  const showChapterDetails = !isProjectChapter || isProjectFocused;
  const chapterTitleId = `${instanceId}-${activeChapter.id}-title`;
  const isFirstChapter = safeActiveIndex === 0;
  const isLastChapter = safeActiveIndex === chapterList.length - 1;
  const renderedFrame = frameAtMediaProgress(activeChapter.mediaProgress);
  const mediaState = isStatic
    ? "Static frame"
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
      data-magnetic-stop={
        magneticStopIndex !== null
          ? chapterList[magneticStopIndex]?.id
          : undefined
      }
      data-panel-align={activeChapter.align ?? "left"}
      data-paused={isPaused || undefined}
      data-project-focused={isProjectFocused || undefined}
      data-reduced-motion={isStatic || undefined}
      onKeyDown={handleKeyDown}
      ref={rootRef}
      style={rootStyle}
      tabIndex={0}
    >
      <div aria-hidden="true" className={styles.media}>
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
          preload="metadata"
          ref={videoRef}
          tabIndex={-1}
        >
          <source media={mobileMediaQuery} src={mobileSrc} type="video/mp4" />
          <source src={desktopSrc} type="video/mp4" />
        </video>
        <div className={styles.shade} />
      </div>

      <div aria-hidden="true" className={styles.controlGate} />
      <JourneyControlDeck
        active={controlDeckActive}
        onReturn={returnFromControlDeck}
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
        data-focused={isProjectFocused || undefined}
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

        {showChapterDetails && (
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
                    <ChapterLink key={`${link.href}-${link.label}`} link={link} />
                  ))}
                </div>
              )}
            </div>

            {(isProjectFocused || activeKind === "finale") && (
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
        )}
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

        {!isStatic && (
          <button
            aria-label={isPaused ? "Resume journey" : "Pause journey"}
            aria-pressed={isPaused}
            className={styles.iconButton}
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
          aria-label={isLastChapter ? "Open control deck" : "Next chapter"}
          className={styles.iconButton}
          disabled={isLastChapter && controlDeckActive}
          onClick={() =>
            isLastChapter ? goToProgress(1) : goToRelativeChapter(1)
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

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

type GestureState = {
  active: boolean;
  direction: -1 | 0 | 1;
  startIndex: number;
  startProgress: number;
};

const DEFAULT_DESKTOP_SRC = "/media/felix-journey-desktop.mp4";
const DEFAULT_MOBILE_SRC = "/media/felix-journey-mobile.mp4";
const DEFAULT_POSTER_SRC = "/media/felix-journey-poster.webp";
const DEFAULT_MOBILE_POSTER_SRC = "/media/felix-journey-mobile-poster.webp";
const DEFAULT_MOBILE_MEDIA_QUERY = "(max-width: 767px)";
const DILATION_STRENGTH = 0.68;
const FOLLOW_RATE = 7.2;
const MINIMUM_GESTURE_PROGRESS = 0.012;
const RENDERED_FRAME_COUNT = 672;
const SEEK_EPSILON_SECONDS = 1 / 90;
const HASH_CHAPTER_INDEX: Readonly<Record<string, number>> = {
  about: 0,
  impact: 1,
  "project-map": 2,
  "case-studies": 3,
  methodology: 5,
  "portfolio-lab": 6,
  contact: 7,
};

function mediaProgressAtFrame(frame: number) {
  return (frame - 1) / (RENDERED_FRAME_COUNT - 1);
}

export const DEFAULT_RENDERED_JOURNEY_CHAPTERS: readonly RenderedJourneyChapter[] = [
  {
    align: "left",
    eyebrow: "Manufacturing project coordination",
    id: "origin",
    label: "Entry",
    links: [
      {
        external: true,
        href: profile.github,
        label: "View public work",
      },
    ],
    mediaProgress: mediaProgressAtFrame(54),
    summary:
      "Manufacturing project chaos, turned into measurable improvement through trial production, workflow control, and operations visibility.",
    title: "Felix Zuo",
  },
  {
    align: "right",
    eyebrow: "Measured impact",
    id: "impact",
    label: "Signal",
    mediaProgress: mediaProgressAtFrame(127),
    metrics: [
      { label: "Notice preparation", value: "< 1 min" },
      { label: "Trial adjustment", value: "3 d to 1 d" },
      { label: "Scrap reduction", value: "about 90%" },
    ],
    summary:
      "Real workflow outcomes, represented with public-safe evidence and synthetic data.",
    title: "Outcomes first. Tools second.",
  },
  {
    align: "left",
    eyebrow: "Trial production / process observation",
    id: "process",
    label: "Process",
    links: [
      {
        external: true,
        href: "https://felix-zuo.github.io/factory-takt-simulator/?view=showcase",
        label: "Open takt simulator",
      },
    ],
    mediaProgress: mediaProgressAtFrame(211),
    summary:
      "Controlled observation isolates the critical operation and creates a slower decision moment before ramp-up.",
    title: "Observe the process before changing it.",
  },
  {
    align: "right",
    eyebrow: "Case 01 / workflow control",
    id: "notice",
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
    mediaProgress: mediaProgressAtFrame(295),
    summary:
      "Structured inputs turn repeated cross-system checking into a reviewable release packet while final control stays human.",
    title: "Production Notice Workflow Standardization",
  },
  {
    align: "left",
    eyebrow: "Case 02 / flow simulation",
    id: "takt",
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
    mediaProgress: mediaProgressAtFrame(379),
    summary:
      "Full-line simulation exposes bottlenecks, buffers, waiting, and blocking before physical trial-and-error consumes more time and material.",
    title: "Trial Production Takt Simulation",
  },
  {
    align: "right",
    eyebrow: "Case 03 / operations visibility",
    id: "visibility",
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
    mediaProgress: mediaProgressAtFrame(463),
    summary:
      "Scattered spreadsheet exports become a consistent operating view for supply, production, delivery, and exception closure.",
    title: "Supply-Production-Delivery Visibility",
  },
  {
    align: "left",
    eyebrow: "Connected public systems",
    id: "system",
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
    mediaProgress: mediaProgressAtFrame(547),
    summary:
      "Operations intelligence, manufacturing data literacy, Six Sigma learning, and evidence-first verification extend the same control logic.",
    title: "One operating method, several public tools.",
  },
  {
    align: "right",
    eyebrow: "Contact / final frame",
    id: "contact",
    label: "Close",
    links: [
      {
        href: `mailto:${profile.email}`,
        label: "Email Felix",
      },
    ],
    mediaProgress: mediaProgressAtFrame(631),
    summary:
      "The strongest fit is where manufacturing execution, launch readiness, and practical workflow tooling must work together.",
    title: "Build the next improvement loop.",
  },
];

function clamp(value: number, minimum = 0, maximum = 1) {
  return Math.min(Math.max(value, minimum), maximum);
}

function chapterStop(index: number, chapterCount: number) {
  if (chapterCount <= 1) return 0;
  return clamp(index, 0, chapterCount - 1) / (chapterCount - 1);
}

function nearestChapterIndex(progress: number, chapterCount: number) {
  return Math.round(clamp(progress) * Math.max(chapterCount - 1, 0));
}

function mapJourneyProgressToMedia(
  journeyProgress: number,
  chapters: readonly RenderedJourneyChapter[],
) {
  if (chapters.length <= 1) return clamp(chapters[0]?.mediaProgress ?? 0);

  const scaled = clamp(journeyProgress) * (chapters.length - 1);
  const startIndex = Math.min(Math.floor(scaled), chapters.length - 2);
  const localProgress = scaled - startIndex;
  const smoothProgress = localProgress * localProgress * (3 - 2 * localProgress);
  const dilatedProgress =
    localProgress + (smoothProgress - localProgress) * DILATION_STRENGTH;
  const start = clamp(chapters[startIndex].mediaProgress);
  const end = clamp(chapters[startIndex + 1].mediaProgress);

  return start + (end - start) * dilatedProgress;
}

function normalizeWheelDelta(event: WheelEvent) {
  if (event.deltaMode === WheelEvent.DOM_DELTA_LINE) return event.deltaY * 16;
  if (event.deltaMode === WheelEvent.DOM_DELTA_PAGE) return event.deltaY * window.innerHeight;
  return event.deltaY;
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

  if (link.href.startsWith("mailto:") || link.href.startsWith("tel:")) {
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
  const initialProgress = chapterStop(initialIndex, chapterList.length);
  const instanceId = useId().replaceAll(":", "");
  const rootRef = useRef<HTMLElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const durationRef = useRef(0);
  const timelineRef = useRef<TimelineState>({
    current: initialProgress,
    target: initialProgress,
  });
  const gestureRef = useRef<GestureState>({
    active: false,
    direction: 0,
    startIndex: initialIndex,
    startProgress: initialProgress,
  });
  const touchYRef = useRef<number | null>(null);
  const snapTimerRef = useRef<number | null>(null);
  const chaptersRef = useRef(chapterList);
  const onChapterChangeRef = useRef(onChapterChange);
  const activeIndexRef = useRef(initialIndex);
  const pausedRef = useRef(false);
  const [activeIndex, setActiveIndex] = useState(initialIndex);
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

  const seekToProgress = useCallback((journeyProgress: number) => {
    const video = videoRef.current;
    if (!video || video.readyState < HTMLMediaElement.HAVE_METADATA) return;

    const duration = durationRef.current || video.duration;
    if (!Number.isFinite(duration) || duration <= 0) return;

    const mediaProgress = mapJourneyProgressToMedia(
      journeyProgress,
      chaptersRef.current,
    );
    const maximumTime = Math.max(duration - 0.04, 0);
    const nextTime = clamp(duration * mediaProgress, 0, maximumTime);

    if (Math.abs(video.currentTime - nextTime) <= SEEK_EPSILON_SECONDS) return;

    try {
      video.currentTime = nextTime;
    } catch {
      // The selected source can change while a responsive video is loading.
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
      commitActiveChapter(
        nearestChapterIndex(boundedProgress, chaptersRef.current.length),
      );
    },
    [commitActiveChapter, seekToProgress],
  );

  const clearSnapTimer = useCallback(() => {
    if (snapTimerRef.current === null) return;
    window.clearTimeout(snapTimerRef.current);
    snapTimerRef.current = null;
  }, []);

  const settleAtChapter = useCallback(() => {
    clearSnapTimer();
    const gesture = gestureRef.current;
    if (!gesture.active) return;

    const chapterCount = chaptersRef.current.length;
    const moved = timelineRef.current.target - gesture.startProgress;
    let nextIndex = nearestChapterIndex(timelineRef.current.target, chapterCount);

    if (
      nextIndex === gesture.startIndex &&
      Math.abs(moved) >= MINIMUM_GESTURE_PROGRESS &&
      gesture.direction !== 0
    ) {
      nextIndex = clamp(
        gesture.startIndex + gesture.direction,
        0,
        chapterCount - 1,
      );
    }

    timelineRef.current.target = chapterStop(nextIndex, chapterCount);
    gesture.active = false;
    gesture.direction = 0;
  }, [clearSnapTimer]);

  const scheduleSettle = useCallback(
    (delay = 190) => {
      clearSnapTimer();
      snapTimerRef.current = window.setTimeout(settleAtChapter, delay);
    },
    [clearSnapTimer, settleAtChapter],
  );

  const applyInputDelta = useCallback((delta: number) => {
    if (pausedRef.current || !Number.isFinite(delta) || delta === 0) return;

    const direction = delta > 0 ? 1 : -1;
    const gesture = gestureRef.current;
    if (!gesture.active) {
      gesture.active = true;
      gesture.startProgress = timelineRef.current.target;
      gesture.startIndex = nearestChapterIndex(
        timelineRef.current.target,
        chaptersRef.current.length,
      );
    }
    gesture.direction = direction;
    timelineRef.current.target = clamp(timelineRef.current.target + delta);
  }, []);

  const goToChapter = useCallback(
    (index: number) => {
      clearSnapTimer();
      const chapterCount = chaptersRef.current.length;
      const boundedIndex = clamp(Math.round(index), 0, chapterCount - 1);
      const progress = chapterStop(boundedIndex, chapterCount);

      gestureRef.current.active = false;
      gestureRef.current.direction = 0;
      timelineRef.current.target = progress;

      if (pausedRef.current || reducedMotion === true) {
        renderProgressImmediately(progress);
      }
    },
    [clearSnapTimer, reducedMotion, renderProgressImmediately],
  );

  const goToRelativeChapter = useCallback(
    (direction: -1 | 1) => {
      const currentTargetIndex = nearestChapterIndex(
        timelineRef.current.target,
        chaptersRef.current.length,
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
        clearSnapTimer();
        gestureRef.current.active = false;
        timelineRef.current.target = timelineRef.current.current;
        videoRef.current?.pause();
      }

      return nextPaused;
    });
  }, [clearSnapTimer]);

  useEffect(() => {
    if (reducedMotion !== false) return;

    const video = videoRef.current;
    if (!video) return;

    setIsVideoReady(false);
    setVideoFailed(false);
    durationRef.current = 0;
    video.preload = "metadata";
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

      const viewportHeight = Math.max(window.innerHeight, 480);
      applyInputDelta(normalizeWheelDelta(event) / (viewportHeight * 3.25));
      scheduleSettle();
    };

    const onTouchStart = (event: TouchEvent) => {
      if (event.touches.length !== 1) return;
      clearSnapTimer();
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
      applyInputDelta(deltaY / (viewportHeight * 3.2));
    };

    const onTouchEnd = () => {
      touchYRef.current = null;
      scheduleSettle(80);
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
    clearSnapTimer,
    reducedMotion,
    scheduleSettle,
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

        timeline.current =
          Math.abs(distance) < 0.00005
            ? timeline.target
            : timeline.current + distance * follow;
      }

      const progress = timelineRef.current.current;
      rootRef.current?.style.setProperty(
        "--journey-progress",
        progress.toFixed(5),
      );
      seekToProgress(progress);
      commitActiveChapter(
        nearestChapterIndex(progress, chaptersRef.current.length),
      );
      frame = window.requestAnimationFrame(tick);
    };

    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, [commitActiveChapter, reducedMotion, seekToProgress]);

  useEffect(
    () => () => {
      clearSnapTimer();
    },
    [clearSnapTimer],
  );

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
      goToChapter(event.key === "Home" ? 0 : chapterList.length - 1);
      return;
    }

    if (event.key === " " && !isStatic) {
      event.preventDefault();
      togglePaused();
    }
  };

  const safeActiveIndex = clamp(activeIndex, 0, chapterList.length - 1);
  const activeChapter = chapterList[safeActiveIndex];
  const chapterTitleId = `${instanceId}-${activeChapter.id}-title`;
  const isFirstChapter = safeActiveIndex === 0;
  const isLastChapter = safeActiveIndex === chapterList.length - 1;
  const rootStyle = {
    "--chapter-count": chapterList.length,
    "--journey-progress": initialProgress.toFixed(5),
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
      aria-labelledby={chapterTitleId}
      className={`${styles.root} ${isStatic ? styles.reducedMotion : ""} ${className}`.trim()}
      data-paused={isPaused || undefined}
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
          preload="none"
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
        <span>{activeChapter.label}</span>
        <span>Sanitized / synthetic</span>
      </header>
      <span aria-live="polite" className={styles.srOnly}>
        {mediaState}
      </span>

      <article
        aria-live="polite"
        className={`${styles.chapter} ${activeChapter.align === "right" ? styles.chapterRight : ""}`}
        key={activeChapter.id}
      >
        <p className={styles.eyebrow}>
          <span>{String(safeActiveIndex + 1).padStart(2, "0")}</span>
          {activeChapter.eyebrow}
        </p>
        <h1 className={styles.title} id={chapterTitleId}>
          {activeChapter.title}
        </h1>
        <p className={styles.summary}>{activeChapter.summary}</p>

        {activeChapter.metrics && activeChapter.metrics.length > 0 && (
          <dl className={styles.metrics}>
            {activeChapter.metrics.map((metric) => (
              <div key={metric.label}>
                <dt>{metric.label}</dt>
                <dd>{metric.value}</dd>
              </div>
            ))}
          </dl>
        )}

        {activeChapter.links && activeChapter.links.length > 0 && (
          <div className={styles.chapterLinks}>
            {activeChapter.links.map((link) => (
              <ChapterLink key={`${link.href}-${link.label}`} link={link} />
            ))}
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
              <li key={chapter.id}>
                <button
                  aria-current={index === safeActiveIndex ? "step" : undefined}
                  aria-label={`Go to chapter ${index + 1}: ${chapter.label}`}
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
          aria-label="Next chapter"
          className={styles.iconButton}
          disabled={isLastChapter}
          onClick={() => goToRelativeChapter(1)}
          title="Next chapter"
          type="button"
        >
          <ChevronRight aria-hidden="true" size={18} />
        </button>
      </div>
    </section>
  );
}

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

const DEFAULT_DESKTOP_SRC = "/media/felix-journey-desktop.mp4";
const DEFAULT_MOBILE_SRC = "/media/felix-journey-mobile.mp4";
const DEFAULT_POSTER_SRC = "/media/felix-journey-poster.webp";
const DEFAULT_MOBILE_POSTER_SRC = "/media/felix-journey-mobile-poster.webp";
const DEFAULT_MOBILE_MEDIA_QUERY = "(max-width: 767px)";
const FOLLOW_RATE = 7.2;
const RENDERED_FPS = 24;
const RENDERED_FRAME_COUNT = 912;
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
  const boundedFrame = clamp(Math.round(frame), 1, RENDERED_FRAME_COUNT);
  return (boundedFrame - 1) / (RENDERED_FRAME_COUNT - 1);
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
    mediaProgress: mediaProgressAtFrame(91),
    metrics: [{ label: "Operating focus", value: "Launch to delivery" }],
    summary:
      "Manufacturing project chaos, turned into measurable improvement through trial production, workflow control, and operations visibility.",
    title: "Felix Zuo",
  },
  {
    align: "right",
    eyebrow: "Measured impact",
    id: "impact",
    label: "Signal",
    mediaProgress: mediaProgressAtFrame(169),
    metrics: [{ label: "Notice preparation", value: "< 1 min" }],
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
    mediaProgress: mediaProgressAtFrame(301),
    metrics: [{ label: "Decision signal", value: "Observe first" }],
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
    mediaProgress: mediaProgressAtFrame(433),
    metrics: [{ label: "Control point", value: "Human final review" }],
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
    mediaProgress: mediaProgressAtFrame(553),
    metrics: [{ label: "Adjustment cycle", value: "3 d to 1 d" }],
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
    mediaProgress: mediaProgressAtFrame(673),
    metrics: [{ label: "Operating span", value: "Supply to delivery" }],
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
    mediaProgress: mediaProgressAtFrame(793),
    metrics: [{ label: "Evidence standard", value: "Sanitized + synthetic" }],
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
    mediaProgress: mediaProgressAtFrame(877),
    metrics: [{ label: "Working mode", value: "Execution + tooling" }],
    summary:
      "The strongest fit is where manufacturing execution, launch readiness, and practical workflow tooling must work together.",
    title: "Build the next improvement loop.",
  },
];

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
  const initialProgress = clamp(chapterList[initialIndex]?.mediaProgress ?? 0);
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
  const touchYRef = useRef<number | null>(null);
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
      commitActiveChapter(
        nearestChapterIndex(boundedProgress, chaptersRef.current),
      );
    },
    [commitActiveChapter, seekToProgress, updateTimelineReadout],
  );

  const applyInputDelta = useCallback((delta: number) => {
    if (pausedRef.current || !Number.isFinite(delta) || delta === 0) return;

    timelineRef.current.target = clamp(timelineRef.current.target + delta);
  }, []);

  const goToProgress = useCallback(
    (progress: number) => {
      const boundedProgress = clamp(progress);
      timelineRef.current.target = boundedProgress;

      if (pausedRef.current || reducedMotion === true) {
        renderProgressImmediately(boundedProgress);
      }
    },
    [reducedMotion, renderProgressImmediately],
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

      const viewportHeight = Math.max(window.innerHeight, 480);
      applyInputDelta(normalizeWheelDelta(event) / (viewportHeight * 3.25));
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
      applyInputDelta(deltaY / (viewportHeight * 3.2));
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
      updateTimelineReadout(progress);
      commitActiveChapter(
        nearestChapterIndex(progress, chaptersRef.current),
      );
      frame = window.requestAnimationFrame(tick);
    };

    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, [commitActiveChapter, reducedMotion, seekToProgress, updateTimelineReadout]);

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
        <span>{activeChapter.label}</span>
        <span>Sanitized / synthetic</span>
      </header>
      <span aria-live="polite" className={styles.srOnly}>
        {mediaState}
      </span>

      <article
        aria-atomic="true"
        aria-live="polite"
        className={`${styles.chapter} ${activeChapter.align === "right" ? styles.chapterRight : ""}`}
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
        <p className={styles.summary}>{activeChapter.summary}</p>

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

        <footer className={styles.slateFooter}>
          <span>38.000 SEC / 24 FPS</span>
          <span aria-hidden="true" className={styles.slateProgress} />
          <span ref={frameReadoutRef}>
            {formatFrameLabel(renderedFrame)} / {RENDERED_FRAME_COUNT}
          </span>
          <span ref={timecodeReadoutRef}>{formatTimecode(renderedFrame)}</span>
        </footer>
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
                    "--chapter-progress": clamp(chapter.mediaProgress).toFixed(5),
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

"use client";

import {
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  MousePointer2,
  Play,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type MouseEvent as ReactMouseEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";

import { profile } from "@/data/profile";

import { JourneyControlDeck } from "./JourneyControlDeck";
import styles from "./CinematicPortfolio.module.css";

type MediaProfile = "desktop" | "mobile";
type ChapterKind =
  | "intro"
  | "metrics"
  | "process"
  | "project"
  | "system"
  | "finale";

type ChapterLink = {
  external?: boolean;
  href: string;
  label: string;
};

type ChapterMetric = {
  before?: string;
  label: string;
  value: string;
};

type Chapter = {
  align: "left" | "right";
  ambient?: {
    desktop: string;
    mobile: string;
  };
  eyebrow: string;
  id: string;
  kind: ChapterKind;
  label: string;
  links?: readonly ChapterLink[];
  metrics?: readonly ChapterMetric[];
  steps?: readonly string[];
  summary: string;
  title: string;
  visualId?: string;
};

type JourneyMotion = {
  fromIndex: number;
  src: string;
  toIndex: number;
};

const CHAPTERS: readonly Chapter[] = [
  {
    align: "left",
    eyebrow: "Manufacturing project coordination",
    id: "origin",
    kind: "intro",
    label: "Entry",
    links: [{ external: true, href: profile.github, label: "View public work" }],
    metrics: [{ label: "Operating focus", value: "Launch to delivery" }],
    summary:
      "Felix Zuo connects trial production, workflow control, and practical digital tools so factory problems become reviewable decisions and measurable improvement.",
    title: "Manufacturing project chaos, turned into measurable improvement.",
  },
  {
    align: "right",
    eyebrow: "Measured operating impact",
    id: "impact",
    kind: "metrics",
    label: "Impact",
    metrics: [
      { before: "20-40 min", label: "Notice preparation", value: "< 1 min" },
      { before: "3 days", label: "Adjustment cycle", value: "1 day" },
      { label: "Trial machining scrap", value: "~90% less" },
      { label: "Estimated changeover saving", value: "RMB 20,000" },
    ],
    summary:
      "The portfolio starts with the operating result, then shows the public-safe systems used to reach it.",
    title: "Outcomes first. Tools second.",
  },
  {
    align: "left",
    ambient: {
      desktop: "/media/holds/process-desktop.mp4?v=15",
      mobile: "/media/holds/process-mobile.mp4?v=15",
    },
    eyebrow: "Trial production / process observation",
    id: "process",
    kind: "process",
    label: "Process",
    metrics: [
      { label: "Decision signal", value: "Observe first" },
      { label: "Improvement loop", value: "Measure / test / verify" },
    ],
    steps: [
      "See the physical constraint before changing the parameter.",
      "Separate machine behavior from material and transfer effects.",
      "Move only after the evidence is reviewable.",
    ],
    summary:
      "A controlled process view slows the decision down at the point where trial cost, quality, and delivery risk meet.",
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
        label: "Live project",
      },
    ],
    metrics: [
      { before: "20-40 min", label: "Preparation", value: "< 1 min" },
      { label: "Release authority", value: "Human final review" },
    ],
    steps: ["Structured request", "Human control gate", "Traceable release packet"],
    summary:
      "Structured inputs replace repeated cross-system collection while final release authority remains explicit and human.",
    title: "Release work, made reviewable.",
  },
  {
    align: "right",
    ambient: {
      desktop: "/media/holds/takt-desktop.mp4?v=14",
      mobile: "/media/holds/takt-mobile.mp4?v=14",
    },
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
        href: "https://felix-zuo.github.io/factory-takt-simulator/?view=showcase",
        label: "Run simulator",
      },
    ],
    metrics: [
      { before: "3 days", label: "Adjustment cycle", value: "1 day" },
      { label: "Model scope", value: "Full production line" },
    ],
    steps: ["Model the line", "Expose the constraint", "Compare countermeasures"],
    summary:
      "The running takt model makes blocking, waiting, buffers, and bottlenecks visible before physical trial-and-error consumes more time and material.",
    title: "See the bottleneck before the trial.",
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
        label: "Live project",
      },
    ],
    metrics: [
      { label: "Operating span", value: "Supply to delivery" },
      { label: "Review model", value: "One consistent view" },
    ],
    steps: ["Classify source", "Normalize recurring inputs", "Review exceptions"],
    summary:
      "Scattered spreadsheet exports become one operating view for supply, production, delivery, and exception closure.",
    title: "Make the operating exception visible.",
  },
  {
    align: "left",
    eyebrow: "Portfolio lab / connected evidence",
    id: "system",
    kind: "system",
    label: "Systems",
    links: [
      { external: true, href: profile.github, label: "Explore GitHub" },
      {
        external: true,
        href: "https://github.com/Felix-Zuo/HulunGuard",
        label: "Open HulunGuard",
      },
    ],
    metrics: [
      { label: "Public systems", value: "7 connected projects" },
      { label: "Evidence boundary", value: "Sanitized + synthetic" },
    ],
    steps: ["Operations intelligence", "Manufacturing data", "Six Sigma", "Reliability"],
    summary:
      "Data literacy, improvement methods, and evidence-first verification extend the same operating discipline beyond the three case studies.",
    title: "Evidence that connects beyond one project.",
  },
  {
    align: "right",
    eyebrow: "Contact / final frame",
    id: "contact",
    kind: "finale",
    label: "Close",
    links: [{ href: `mailto:${profile.email}`, label: "Email Felix" }],
    metrics: [
      { label: "Working mode", value: "Execution + tooling" },
      { label: "Best fit", value: "Launch / flow / visibility" },
    ],
    summary:
      "The strongest fit is where manufacturing execution, launch readiness, and practical workflow tooling must work together.",
    title: "Build the next improvement loop.",
    visualId: "close",
  },
] as const;

const HASH_CHAPTER_INDEX: Readonly<Record<string, number>> = {
  about: 0,
  entry: 0,
  origin: 0,
  impact: 1,
  process: 2,
  "project-map": 2,
  methodology: 2,
  "case-studies": 3,
  notice: 3,
  takt: 4,
  visibility: 5,
  "portfolio-lab": 6,
  system: 6,
  close: 7,
  contact: 7,
};

const TRANSITION_MS = 760;
const START_GATE_MS = 820;
const DOOR_REVEAL_MS = 980;
const DOOR_COMPLETE_MS = 1420;
const MOBILE_QUERY = "(max-width: 767px)";
const MEDIA_VERSION = 17;

function chapterMediaId(chapter: Chapter) {
  return chapter.visualId ?? chapter.id;
}

function chapterImage(chapter: Chapter, profile: MediaProfile) {
  return `/media/chapters/${chapterMediaId(chapter)}-${profile}.webp?v=${MEDIA_VERSION}`;
}

function chapterHold(chapter: Chapter, profile: MediaProfile) {
  return `/media/holds/${chapterMediaId(chapter)}-${profile}.mp4?v=${MEDIA_VERSION}`;
}

function transitionVideoBetween(
  fromIndex: number,
  toIndex: number,
  profile: MediaProfile,
) {
  const from = CHAPTERS[fromIndex];
  const to = CHAPTERS[toIndex];
  return `/media/transitions/${from.id}-to-${to.id}-${profile}.mp4?v=${MEDIA_VERSION}`;
}

function startImage(profile: MediaProfile) {
  return `/media/chapters/start-${profile}.webp?v=14`;
}

function controlRoomVideo(profile: MediaProfile) {
  return profile === "mobile"
    ? "/media/control-room-loop-720p.webm?v=14"
    : "/media/control-room-loop.webm?v=14";
}

function useMediaProfile() {
  const [profile, setProfile] = useState<MediaProfile | null>(null);

  useEffect(() => {
    const query = window.matchMedia(MOBILE_QUERY);
    const update = () => setProfile(query.matches ? "mobile" : "desktop");
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  return profile;
}

function useReducedMotion() {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  return reduced;
}

function useMediaPreloader(profile: MediaProfile | null) {
  const [progress, setProgress] = useState(0);
  const [ready, setReady] = useState(false);
  const [loadedProfile, setLoadedProfile] = useState<MediaProfile | null>(null);

  const assets = useMemo(
    () => {
      if (!profile) return [];

      const images = [
        startImage(profile),
        ...CHAPTERS.map((chapter) => chapterImage(chapter, profile)),
      ];
      const videos = [
        ...CHAPTERS.slice(0, -1).flatMap((_, index) => [
          transitionVideoBetween(index, index + 1, profile),
          transitionVideoBetween(index + 1, index, profile),
        ]),
        ...CHAPTERS.map((chapter) => chapterHold(chapter, profile)),
        controlRoomVideo(profile),
        "/evidence/takt-live-workbench.mp4",
      ];

      return [
        ...images.map((url) => ({ kind: "image" as const, url })),
        ...videos.map((url) => ({ kind: "video" as const, url })),
      ];
    },
    [profile],
  );

  useEffect(() => {
    if (!profile || assets.length === 0) return;

    let cancelled = false;
    let complete = 0;
    const pendingTimers = new Set<number>();

    const markComplete = () => {
      complete += 1;
      if (!cancelled) {
        setLoadedProfile(profile);
        setReady(false);
        setProgress(complete / assets.length);
      }
    };

    const loadImage = (url: string) =>
      new Promise<void>((resolve) => {
        const image = new window.Image();
        let settled = false;
        const finish = () => {
          if (settled) return;
          settled = true;
          markComplete();
          resolve();
        };
        image.onload = finish;
        image.onerror = finish;
        image.src = url;
      });

    const loadVideo = (url: string) =>
      new Promise<void>((resolve) => {
        const video = document.createElement("video");
        let settled = false;
        const finish = () => {
          if (settled) return;
          settled = true;
          window.clearTimeout(timeout);
          pendingTimers.delete(timeout);
          markComplete();
          resolve();
        };
        const timeout = window.setTimeout(finish, 12000);
        pendingTimers.add(timeout);
        video.muted = true;
        video.playsInline = true;
        video.preload = "auto";
        video.oncanplaythrough = finish;
        video.onerror = finish;
        video.src = url;
        video.load();
      });

    void Promise.all(
      assets.map((asset) =>
        asset.kind === "image"
          ? loadImage(asset.url)
          : loadVideo(asset.url),
      ),
    ).then(() => {
      if (cancelled) return;
      setLoadedProfile(profile);
      setProgress(1);
      setReady(true);
    });

    return () => {
      cancelled = true;
      pendingTimers.forEach((timer) => window.clearTimeout(timer));
      pendingTimers.clear();
    };
  }, [assets, profile]);

  const isCurrentProfile = loadedProfile === profile;
  return {
    progress: isCurrentProfile ? progress : 0,
    ready: isCurrentProfile && ready,
  };
}

function ExperienceLink({ link }: { link: ChapterLink }) {
  const content = (
    <>
      <span>{link.label}</span>
      <ArrowUpRight aria-hidden="true" size={16} strokeWidth={1.8} />
    </>
  );

  if (link.external) {
    return (
      <a href={link.href} rel="noreferrer" target="_blank">
        {content}
      </a>
    );
  }

  if (link.href.startsWith("mailto:") || link.href.startsWith("tel:")) {
    return <a href={link.href}>{content}</a>;
  }

  return <Link href={link.href}>{content}</Link>;
}

function SceneImage({
  chapter,
  className,
}: {
  chapter: Chapter;
  className: string;
}) {
  return (
    <picture className={className}>
      <source media={MOBILE_QUERY} srcSet={chapterImage(chapter, "mobile")} />
      <Image
        alt=""
        className={styles.sceneImageAsset}
        fill
        priority
        sizes="100vw"
        src={chapterImage(chapter, "desktop")}
        unoptimized
      />
    </picture>
  );
}

function DoorImage() {
  const chapter = CHAPTERS[CHAPTERS.length - 1];

  return (
    <picture className={styles.doorPicture}>
      <source media={MOBILE_QUERY} srcSet={chapterImage(chapter, "mobile")} />
      <Image
        alt=""
        className={styles.doorImage}
        fill
        loading="eager"
        sizes="100vw"
        src={chapterImage(chapter, "desktop")}
        unoptimized
      />
    </picture>
  );
}

export function CinematicPortfolio() {
  const mediaProfile = useMediaProfile();
  const reducedMotion = useReducedMotion();
  const preloader = useMediaPreloader(mediaProfile);
  const rootRef = useRef<HTMLElement>(null);
  const transitionVideoRef = useRef<HTMLVideoElement>(null);
  const pointerFrameRef = useRef<number | null>(null);
  const timersRef = useRef(new Set<number>());
  const [activeIndex, setActiveIndex] = useState(0);
  const [outgoingIndex, setOutgoingIndex] = useState<number | null>(null);
  const [direction, setDirection] = useState<"forward" | "backward">("forward");
  const [transitionNonce, setTransitionNonce] = useState(0);
  const [transitioning, setTransitioning] = useState(false);
  const [journeyMotion, setJourneyMotion] = useState<JourneyMotion | null>(null);
  const [motionArrival, setMotionArrival] = useState(false);
  const [jumpPhase, setJumpPhase] = useState<"cover" | "reveal" | null>(null);
  const [started, setStarted] = useState(false);
  const [startGateVisible, setStartGateVisible] = useState(true);
  const [startGateLeaving, setStartGateLeaving] = useState(false);
  const [doorOpening, setDoorOpening] = useState(false);
  const [controlDeckVisible, setControlDeckVisible] = useState(false);
  const [controlDeckActive, setControlDeckActive] = useState(false);

  const activeChapter = CHAPTERS[activeIndex];
  const outgoingChapter =
    outgoingIndex === null ? null : CHAPTERS[outgoingIndex];
  const isFirst = activeIndex === 0;
  const isLast = activeIndex === CHAPTERS.length - 1;
  const nextChapter = CHAPTERS[Math.min(activeIndex + 1, CHAPTERS.length - 1)];
  const currentAmbient = mediaProfile && !journeyMotion
    ? chapterHold(activeChapter, mediaProfile)
    : null;

  const schedule = useCallback((callback: () => void, delay: number) => {
    const timer = window.setTimeout(() => {
      timersRef.current.delete(timer);
      callback();
    }, delay);
    timersRef.current.add(timer);
    return timer;
  }, []);

  useEffect(() => {
    const timers = timersRef.current;
    return () => {
      timers.forEach((timer) => window.clearTimeout(timer));
      timers.clear();
      if (pointerFrameRef.current !== null) {
        window.cancelAnimationFrame(pointerFrameRef.current);
      }
    };
  }, []);

  useEffect(() => {
    const html = document.documentElement;
    const body = document.body;
    const htmlOverflow = html.style.overflow;
    const bodyOverflow = body.style.overflow;
    html.style.overflow = "hidden";
    body.style.overflow = "hidden";
    return () => {
      html.style.overflow = htmlOverflow;
      body.style.overflow = bodyOverflow;
    };
  }, []);

  const beginJourney = useCallback(() => {
    if (!preloader.ready || started) return;
    setStarted(true);
    setStartGateLeaving(true);
    schedule(() => setStartGateVisible(false), reducedMotion ? 0 : START_GATE_MS);
    schedule(() => rootRef.current?.focus(), reducedMotion ? 0 : START_GATE_MS + 20);
  }, [preloader.ready, reducedMotion, schedule, started]);

  const jumpTo = useCallback(
    (index: number) => {
      const bounded = Math.min(
        Math.max(Math.round(index), 0),
        CHAPTERS.length - 1,
      );
      if (
        !started ||
        transitioning ||
        doorOpening ||
        controlDeckActive ||
        bounded === activeIndex
      ) {
        return;
      }

      const nextDirection = bounded > activeIndex ? "forward" : "backward";
      setDirection(nextDirection);
      setTransitioning(true);
      setJumpPhase("cover");
      schedule(() => {
        setOutgoingIndex(null);
        setJourneyMotion(null);
        setActiveIndex(bounded);
        setTransitionNonce((value) => value + 1);
        setJumpPhase("reveal");
        window.history.replaceState(null, "", `#${CHAPTERS[bounded].id}`);
      }, reducedMotion ? 0 : 220);
      schedule(() => {
        setJumpPhase(null);
        setOutgoingIndex(null);
        setTransitioning(false);
      }, reducedMotion ? 0 : 640);
    },
    [
      activeIndex,
      controlDeckActive,
      doorOpening,
      reducedMotion,
      schedule,
      started,
      transitioning,
    ],
  );

  const completeJourneyMotion = useCallback(() => {
    if (!journeyMotion) return;

    const targetIndex = journeyMotion.toIndex;
    setMotionArrival(true);
    setActiveIndex(targetIndex);
    window.history.replaceState(null, "", `#${CHAPTERS[targetIndex].id}`);
    rootRef.current?.style.setProperty("--journey-progress", "1");

    schedule(() => {
      setJourneyMotion(null);
      setTransitioning(false);
      rootRef.current?.style.setProperty("--journey-progress", "0");
    }, 90);
    schedule(() => setMotionArrival(false), TRANSITION_MS + 120);
  }, [journeyMotion, schedule]);

  const playSegment = useCallback((targetIndex: number) => {
    if (
      !mediaProfile ||
      !started ||
      transitioning ||
      doorOpening ||
      controlDeckActive ||
      Math.abs(targetIndex - activeIndex) !== 1
    ) {
      return;
    }

    if (reducedMotion) {
      jumpTo(targetIndex);
      return;
    }

    setDirection(targetIndex > activeIndex ? "forward" : "backward");
    setOutgoingIndex(null);
    setMotionArrival(false);
    setTransitioning(true);
    rootRef.current?.style.setProperty("--journey-progress", "0");
    setJourneyMotion({
      fromIndex: activeIndex,
      src: transitionVideoBetween(activeIndex, targetIndex, mediaProfile),
      toIndex: targetIndex,
    });
  }, [
    activeIndex,
    controlDeckActive,
    doorOpening,
    mediaProfile,
    jumpTo,
    reducedMotion,
    started,
    transitioning,
  ]);

  const requestNavigation = useCallback((index: number) => {
    const bounded = Math.min(Math.max(Math.round(index), 0), CHAPTERS.length - 1);
    if (bounded === activeIndex) return;
    if (Math.abs(bounded - activeIndex) === 1) {
      playSegment(bounded);
      return;
    }
    jumpTo(bounded);
  }, [activeIndex, jumpTo, playSegment]);

  const playNextSegment = useCallback(() => {
    if (activeIndex < CHAPTERS.length - 1) playSegment(activeIndex + 1);
  }, [activeIndex, playSegment]);

  const playPreviousSegment = useCallback(() => {
    if (activeIndex > 0) playSegment(activeIndex - 1);
  }, [activeIndex, playSegment]);

  useEffect(() => {
    if (!journeyMotion) return;
    const video = transitionVideoRef.current;
    if (!video) return;

    const play = () => {
      video.currentTime = 0;
      void video.play().catch(completeJourneyMotion);
    };

    if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
      play();
    } else {
      video.addEventListener("canplay", play, { once: true });
    }

    return () => video.removeEventListener("canplay", play);
  }, [completeJourneyMotion, journeyMotion]);

  const openControlDeck = useCallback(() => {
    if (transitioning || doorOpening || controlDeckActive) return;
    window.history.replaceState(null, "", "#control");
    if (reducedMotion) {
      setControlDeckVisible(true);
      setControlDeckActive(true);
      return;
    }

    setDoorOpening(true);
    setTransitioning(true);
    schedule(() => {
      setControlDeckVisible(true);
      setControlDeckActive(true);
    }, DOOR_REVEAL_MS);
    schedule(() => {
      setDoorOpening(false);
      setTransitioning(false);
    }, DOOR_COMPLETE_MS);
  }, [controlDeckActive, doorOpening, reducedMotion, schedule, transitioning]);

  const returnFromControlDeck = useCallback(() => {
    setControlDeckActive(false);
    setControlDeckVisible(false);
    setDoorOpening(false);
    setJourneyMotion(null);
    setTransitioning(false);
    window.history.replaceState(null, "", "#contact");
  }, []);

  const goForward = useCallback(() => {
    if (isLast) {
      openControlDeck();
    } else {
      playNextSegment();
    }
  }, [isLast, openControlDeck, playNextSegment]);

  useEffect(() => {
    const followHash = () => {
      const hash = window.location.hash.slice(1);
      if (!hash) return;
      if (hash === "control") {
        setStarted(true);
        setStartGateVisible(false);
        setActiveIndex(CHAPTERS.length - 1);
        setControlDeckVisible(true);
        setControlDeckActive(true);
        return;
      }

      const index = HASH_CHAPTER_INDEX[hash];
      if (index === undefined) return;
      setStarted(true);
      setStartGateVisible(false);
      setActiveIndex(index);
      setOutgoingIndex(null);
      setJourneyMotion(null);
      setTransitioning(false);
    };

    followHash();
    window.addEventListener("hashchange", followHash);
    return () => window.removeEventListener("hashchange", followHash);
  }, []);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const preventWheel = (event: WheelEvent) => {
      if (!event.ctrlKey) event.preventDefault();
    };
    root.addEventListener("wheel", preventWheel, { passive: false });
    return () => root.removeEventListener("wheel", preventWheel);
  }, []);

  const handleKeyDown = (event: ReactKeyboardEvent<HTMLElement>) => {
    const target = event.target as HTMLElement;
    if (target !== event.currentTarget && target.closest("a, button, input, textarea, select")) {
      return;
    }
    if (!started) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        beginJourney();
      }
      return;
    }

    if (event.key === "ArrowRight" || event.key === "ArrowDown" || event.key === "PageDown") {
      event.preventDefault();
      goForward();
    } else if (
      event.key === "ArrowLeft" ||
      event.key === "ArrowUp" ||
      event.key === "PageUp"
    ) {
      event.preventDefault();
      playPreviousSegment();
    } else if (event.key === "Home" || event.key === "End") {
      event.preventDefault();
      requestNavigation(event.key === "Home" ? 0 : CHAPTERS.length - 1);
    }
  };

  const handleSceneClick = (event: ReactMouseEvent<HTMLElement>) => {
    if (!started || transitioning || controlDeckActive) return;
    const target = event.target as HTMLElement;
    if (target.closest("a, button, input, textarea, select, [role='button']")) return;
    if (window.getSelection()?.toString()) return;
    goForward();
  };

  const handlePointerMove = (event: ReactPointerEvent<HTMLElement>) => {
    if (event.pointerType === "touch") return;
    const root = rootRef.current;
    if (!root) return;
    const x = event.clientX;
    const y = event.clientY;
    const target = event.target as HTMLElement;
    const interactive = Boolean(target.closest("a, button, [role='button']"));
    if (pointerFrameRef.current !== null) {
      window.cancelAnimationFrame(pointerFrameRef.current);
    }
    pointerFrameRef.current = window.requestAnimationFrame(() => {
      const width = Math.max(root.clientWidth, 1);
      const height = Math.max(root.clientHeight, 1);
      root.style.setProperty("--pointer-x", `${x}px`);
      root.style.setProperty("--pointer-y", `${y}px`);
      root.style.setProperty("--panel-tilt-x", `${((0.5 - y / height) * 1.1).toFixed(3)}deg`);
      root.style.setProperty("--panel-tilt-y", `${((x / width - 0.5) * 1.35).toFixed(3)}deg`);
      root.toggleAttribute("data-pointer-interactive", interactive);
      pointerFrameRef.current = null;
    });
  };

  const handlePointerLeave = () => {
    const root = rootRef.current;
    root?.style.setProperty("--panel-tilt-x", "0deg");
    root?.style.setProperty("--panel-tilt-y", "0deg");
    root?.removeAttribute("data-pointer-interactive");
  };

  return (
    <section
      aria-busy={!preloader.ready || transitioning}
      aria-label={controlDeckActive ? "Felix Zuo operations control deck" : "Felix Zuo manufacturing portfolio"}
      className={styles.root}
      data-chapter={activeChapter.id}
      data-control-deck={controlDeckActive || undefined}
      data-direction={direction}
      data-door-opening={doorOpening || undefined}
      data-motion-arrival={motionArrival || undefined}
      data-motion-playing={journeyMotion ? true : undefined}
      data-started={started || undefined}
      data-transitioning={transitioning || undefined}
      onClick={handleSceneClick}
      onKeyDown={handleKeyDown}
      onPointerLeave={handlePointerLeave}
      onPointerMove={handlePointerMove}
      ref={rootRef}
      tabIndex={0}
    >
      <div aria-hidden="true" className={styles.sceneStage}>
        {outgoingChapter && (
          <SceneImage
            chapter={outgoingChapter}
            className={`${styles.sceneImage} ${styles.sceneOutgoing}`}
          />
        )}

        <SceneImage
          chapter={activeChapter}
          className={`${styles.sceneImage} ${styles.sceneActive}`}
          key={`${activeChapter.id}-${transitionNonce}`}
        />

        {currentAmbient && started && !reducedMotion && (
          <video
            autoPlay
            className={styles.ambientVideo}
            key={`${activeChapter.id}-${mediaProfile}`}
            loop
            muted
            playsInline
            poster={chapterImage(activeChapter, mediaProfile ?? "desktop")}
            preload="auto"
            src={currentAmbient}
            tabIndex={-1}
          />
        )}
        {journeyMotion && mediaProfile && (
          <video
            autoPlay
            className={styles.transitionVideo}
            key={journeyMotion.src}
            muted
            onEnded={completeJourneyMotion}
            onError={completeJourneyMotion}
            onTimeUpdate={(event) => {
              const video = event.currentTarget;
              const progress = video.duration > 0
                ? Math.min(video.currentTime / video.duration, 1)
                : 0;
              rootRef.current?.style.setProperty(
                "--journey-progress",
                progress.toFixed(4),
              );
            }}
            playsInline
            poster={chapterImage(CHAPTERS[journeyMotion.fromIndex], mediaProfile)}
            preload="auto"
            ref={transitionVideoRef}
            src={journeyMotion.src}
            tabIndex={-1}
          />
        )}
        <span className={styles.sceneShade} />
      </div>

      {jumpPhase && (
        <span aria-hidden="true" className={styles.jumpVeil} data-phase={jumpPhase} />
      )}

      {startGateVisible && (
        <div
          className={styles.startGate}
          data-leaving={startGateLeaving || undefined}
          onClick={beginJourney}
        >
          <picture className={styles.startVisual}>
            <source media={MOBILE_QUERY} srcSet={startImage("mobile")} />
            <Image
              alt=""
              className={styles.startVisualImage}
              fill
              priority
              sizes="100vw"
              src={startImage("desktop")}
              unoptimized
            />
          </picture>
          <span aria-hidden="true" className={styles.startShade} />

          <div className={styles.startContent}>
            <p>Felix Zuo / Manufacturing operations</p>
            <h1>From the plant floor to reviewable evidence.</h1>
            <span className={styles.startSummary}>
              An eight-chapter portfolio across launch readiness, process improvement,
              and factory workflow systems.
            </span>

            <button
              aria-label={preloader.ready ? "Begin the portfolio journey" : "Portfolio is loading"}
              className={styles.startButton}
              disabled={!preloader.ready}
              onClick={(event) => {
                event.stopPropagation();
                beginJourney();
              }}
              type="button"
            >
              <span className={styles.playButton}>
                <Play aria-hidden="true" fill="currentColor" size={19} />
              </span>
              <span>
                <small>{preloader.ready ? "Click anywhere to begin" : "Loading portfolio"}</small>
                <strong>{preloader.ready ? "One click advances one scene" : `${Math.round(preloader.progress * 100)}%`}</strong>
              </span>
            </button>

            <div className={styles.startProgress} aria-hidden="true">
              <span style={{ transform: `scaleX(${preloader.progress})` }} />
            </div>
          </div>
        </div>
      )}

      {!controlDeckActive && started && (
        <>
          <header className={styles.sceneMeta}>
            <span>FZ / Manufacturing operations</span>
            <span>{activeChapter.label}</span>
            <span>Public-safe / synthetic</span>
          </header>

          <article
            aria-atomic="true"
            aria-live="polite"
            className={styles.chapterPanel}
            data-align={activeChapter.align}
            data-kind={activeChapter.kind}
            key={activeChapter.id}
          >
            <div className={styles.panelLayer}>
            <p className={styles.eyebrow}>
              <span>
                {String(activeIndex + 1).padStart(2, "0")} / {String(CHAPTERS.length).padStart(2, "0")}
              </span>
              {activeChapter.eyebrow}
            </p>

            <h1>{activeChapter.title}</h1>
            <p className={styles.chapterSummary}>{activeChapter.summary}</p>

            {activeChapter.kind === "metrics" && activeChapter.metrics && (
              <dl className={styles.impactMetrics}>
                {activeChapter.metrics.map((metric) => (
                  <div key={metric.label}>
                    <dt>{metric.label}</dt>
                    <dd>
                      {metric.before && <span>{metric.before}</span>}
                      <strong>{metric.value}</strong>
                    </dd>
                  </div>
                ))}
              </dl>
            )}

            {activeChapter.kind === "process" && activeChapter.steps && (
              <ol className={styles.evidenceFlow}>
                {activeChapter.steps.map((step, index) => (
                  <li key={step}>
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <strong>{step}</strong>
                  </li>
                ))}
              </ol>
            )}

            {activeChapter.kind !== "metrics" && activeChapter.metrics && (
              <dl className={styles.chapterMetrics}>
                {activeChapter.metrics.map((metric) => (
                  <div key={metric.label}>
                    <dt>{metric.label}</dt>
                    <dd>
                      {metric.before && <span>{metric.before}</span>}
                      <strong>{metric.value}</strong>
                    </dd>
                  </div>
                ))}
              </dl>
            )}

            <div className={styles.chapterActions}>
              {isLast && (
                <button onClick={openControlDeck} type="button">
                  <span>Open control room</span>
                  <ArrowUpRight aria-hidden="true" size={16} />
                </button>
              )}
              {activeChapter.links?.map((link) => (
                <ExperienceLink key={`${link.href}-${link.label}`} link={link} />
              ))}
            </div>
            </div>
          </article>

          <div aria-hidden="true" className={styles.sceneAdvanceHint}>
            <MousePointer2 size={16} strokeWidth={1.8} />
            <span>
              <small>{mediaProfile === "mobile" ? "Tap the scene" : "Click the scene"}</small>
              <strong>{isLast ? "Open control room" : `Play to ${nextChapter.label}`}</strong>
            </span>
          </div>

          <footer className={styles.transport}>
            <button
              aria-label="Previous chapter"
              className={styles.transportBack}
              disabled={isFirst || transitioning}
              onClick={playPreviousSegment}
              title="Previous chapter"
              type="button"
            >
              <ArrowLeft aria-hidden="true" size={19} />
            </button>

            <div className={styles.routeReadout}>
              <span>{String(activeIndex + 1).padStart(2, "0")}</span>
              <strong>{activeChapter.label}</strong>
            </div>

            <nav aria-label="Portfolio route" className={styles.chapterRail}>
              <ol>
                {CHAPTERS.map((chapter, index) => (
                  <li key={chapter.id}>
                    <button
                      aria-current={index === activeIndex ? "step" : undefined}
                      aria-label={`Go to chapter ${index + 1}: ${chapter.label}`}
                      disabled={transitioning || index === activeIndex}
                      onClick={() => requestNavigation(index)}
                      title={chapter.label}
                      type="button"
                    >
                      {String(index + 1).padStart(2, "0")}
                    </button>
                  </li>
                ))}
              </ol>
            </nav>

            <button
              aria-label={isLast ? "Open control room" : `Next chapter: ${nextChapter.label}`}
              className={styles.transportNext}
              disabled={transitioning}
              onClick={goForward}
              type="button"
            >
              <span>
                <small>{isLast ? "Finale" : "Play next scene"}</small>
                <strong>{isLast ? "Control room" : nextChapter.label}</strong>
              </span>
              <ArrowRight aria-hidden="true" size={19} />
            </button>
          </footer>
        </>
      )}

      {journeyMotion && (
        <div aria-live="polite" className={styles.motionHud}>
          <span>
            <small>Camera in motion</small>
            <strong>{CHAPTERS[journeyMotion.toIndex].label}</strong>
          </span>
          <i aria-hidden="true" className={styles.motionProgress} />
        </div>
      )}

      {!controlDeckActive && started && (
        <span aria-hidden="true" className={styles.pointerFollower}>
          <MousePointer2 size={18} strokeWidth={1.7} />
        </span>
      )}

      {doorOpening && (
        <div aria-hidden="true" className={styles.doorTransition}>
          <span className={`${styles.doorHalf} ${styles.doorLeft}`}>
            <DoorImage />
          </span>
          <span className={`${styles.doorHalf} ${styles.doorRight}`}>
            <DoorImage />
          </span>
        </div>
      )}

      <JourneyControlDeck
        active={controlDeckActive}
        backdropSrc={controlRoomVideo(mediaProfile ?? "desktop")}
        onReturn={returnFromControlDeck}
        visible={controlDeckVisible}
      />
    </section>
  );
}

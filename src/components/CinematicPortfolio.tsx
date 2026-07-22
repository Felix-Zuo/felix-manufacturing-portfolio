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
  useRef,
  useState,
  useSyncExternalStore,
  type KeyboardEvent as ReactKeyboardEvent,
  type MouseEvent as ReactMouseEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";

import { profile } from "@/data/profile";

import { JourneyControlDeck } from "./JourneyControlDeck";
import styles from "./CinematicPortfolio.module.css";

type MediaProfile = "desktop" | "mobile";
type Locale = "en" | "zh";
type LocalizedText = Readonly<Record<Locale, string>>;
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
  label: LocalizedText;
};

type ChapterMetric = {
  before?: LocalizedText;
  label: LocalizedText;
  value: LocalizedText;
};

type Chapter = {
  align: "left" | "right";
  ambient?: {
    desktop: string;
    mobile: string;
  };
  eyebrow: LocalizedText;
  id: string;
  kind: ChapterKind;
  label: LocalizedText;
  links?: readonly ChapterLink[];
  metrics?: readonly ChapterMetric[];
  steps?: readonly LocalizedText[];
  summary: LocalizedText;
  title: LocalizedText;
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
    eyebrow: {
      en: "Manufacturing project coordination",
      zh: "制造项目协同",
    },
    id: "origin",
    kind: "intro",
    label: { en: "Entry", zh: "起点" },
    links: [
      {
        external: true,
        href: profile.github,
        label: { en: "View public work", zh: "查看公开作品" },
      },
    ],
    metrics: [
      {
        label: { en: "Operating focus", zh: "核心范围" },
        value: { en: "Launch to delivery", zh: "从导入到交付" },
      },
    ],
    summary: {
      en: "Felix Zuo connects trial production, workflow control, and practical digital tools so factory problems become reviewable decisions and measurable improvement.",
      zh: "Felix Zuo 将试生产、流程控制与实用数字工具连接起来，让工厂问题转化为可复核的决策与可衡量的改善。",
    },
    title: {
      en: "Manufacturing project chaos, turned into measurable improvement.",
      zh: "让制造项目的混乱，变成可衡量的改善。",
    },
  },
  {
    align: "right",
    ambient: {
      desktop: "/media/holds/robot-desktop.mp4?v=18",
      mobile: "/media/holds/robot-mobile.mp4?v=18",
    },
    eyebrow: { en: "Measured operating impact", zh: "可量化的运营成果" },
    id: "impact",
    kind: "metrics",
    label: { en: "Impact", zh: "成果" },
    metrics: [
      {
        before: { en: "20-40 min", zh: "20-40 分钟" },
        label: { en: "Notice preparation", zh: "通知单准备" },
        value: { en: "< 1 min", zh: "< 1 分钟" },
      },
      {
        before: { en: "3 days", zh: "3 天" },
        label: { en: "Adjustment cycle", zh: "调整周期" },
        value: { en: "1 day", zh: "1 天" },
      },
      {
        label: { en: "Trial machining scrap", zh: "试加工废料" },
        value: { en: "~90% less", zh: "减少约 90%" },
      },
      {
        label: { en: "Estimated changeover saving", zh: "预计换型节省" },
        value: { en: "RMB 20,000", zh: "人民币 20,000" },
      },
    ],
    summary: {
      en: "The portfolio starts with the operating result, then shows the public-safe systems used to reach it.",
      zh: "作品集先呈现运营成果，再展示支撑这些成果的公开安全系统。",
    },
    title: { en: "Outcomes first. Tools second.", zh: "先看成果，再看工具。" },
  },
  {
    align: "left",
    ambient: {
      desktop: "/media/holds/process-desktop.mp4?v=18",
      mobile: "/media/holds/process-mobile.mp4?v=18",
    },
    eyebrow: { en: "Trial production / process observation", zh: "试生产 / 过程观察" },
    id: "process",
    kind: "process",
    label: { en: "Process", zh: "过程" },
    metrics: [
      {
        label: { en: "Decision signal", zh: "决策信号" },
        value: { en: "Observe first", zh: "先观察" },
      },
      {
        label: { en: "Improvement loop", zh: "改善闭环" },
        value: { en: "Measure / test / verify", zh: "测量 / 试验 / 验证" },
      },
    ],
    steps: [
      {
        en: "See the physical constraint before changing the parameter.",
        zh: "调整参数之前，先看清真实的物理约束。",
      },
      {
        en: "Separate machine behavior from material and transfer effects.",
        zh: "区分设备行为、材料影响与转运影响。",
      },
      {
        en: "Move only after the evidence is reviewable.",
        zh: "证据可复核之后，再推进下一步。",
      },
    ],
    summary: {
      en: "A controlled process view slows the decision down at the point where trial cost, quality, and delivery risk meet.",
      zh: "在试制成本、质量与交付风险交汇的位置，用受控观察为决策留出必要的判断时间。",
    },
    title: {
      en: "Observe the process before changing it.",
      zh: "改变之前，先看清过程。",
    },
  },
  {
    align: "left",
    eyebrow: { en: "Case 01 / workflow control", zh: "案例 01 / 流程控制" },
    id: "notice",
    kind: "project",
    label: { en: "Notice", zh: "通知单" },
    links: [
      {
        href: "/case-studies/production-notice-workflow-standardization",
        label: { en: "Open case study", zh: "查看完整案例" },
      },
      {
        external: true,
        href: "https://felix-zuo.github.io/factory-production-notice-agent/showcase.html",
        label: { en: "Live project", zh: "打开在线项目" },
      },
    ],
    metrics: [
      {
        before: { en: "20-40 min", zh: "20-40 分钟" },
        label: { en: "Preparation", zh: "准备时间" },
        value: { en: "< 1 min", zh: "< 1 分钟" },
      },
      {
        label: { en: "Release authority", zh: "发布权限" },
        value: { en: "Human final review", zh: "人工最终审核" },
      },
    ],
    steps: [
      { en: "Structured request", zh: "结构化需求" },
      { en: "Human control gate", zh: "人工控制关口" },
      { en: "Traceable release packet", zh: "可追溯发布包" },
    ],
    summary: {
      en: "Structured inputs replace repeated cross-system collection while final release authority remains explicit and human.",
      zh: "用结构化输入替代跨系统反复收集，同时明确保留人工最终发布权限。",
    },
    title: { en: "Release work, made reviewable.", zh: "让任务发布可审核、可追溯。" },
  },
  {
    align: "right",
    eyebrow: { en: "Case 02 / flow simulation", zh: "案例 02 / 流动仿真" },
    id: "takt",
    kind: "project",
    label: { en: "Takt", zh: "节拍" },
    links: [
      {
        href: "/case-studies/trial-production-takt-simulation-changeover-improvement",
        label: { en: "Open case study", zh: "查看完整案例" },
      },
      {
        external: true,
        href: "https://felix-zuo.github.io/factory-takt-simulator/?view=showcase",
        label: { en: "Run simulator", zh: "启动仿真" },
      },
    ],
    metrics: [
      {
        before: { en: "3 days", zh: "3 天" },
        label: { en: "Adjustment cycle", zh: "调整周期" },
        value: { en: "1 day", zh: "1 天" },
      },
      {
        label: { en: "Model scope", zh: "模型范围" },
        value: { en: "Full production line", zh: "完整生产线" },
      },
    ],
    steps: [
      { en: "Model the line", zh: "建立产线模型" },
      { en: "Expose the constraint", zh: "暴露关键约束" },
      { en: "Compare countermeasures", zh: "比较改善方案" },
    ],
    summary: {
      en: "The running takt model makes blocking, waiting, buffers, and bottlenecks visible before physical trial-and-error consumes more time and material.",
      zh: "运行中的节拍模型让阻塞、等待、缓冲与瓶颈提前显现，避免更多时间和物料消耗在实体试错中。",
    },
    title: { en: "See the bottleneck before the trial.", zh: "试产之前，先看见瓶颈。" },
  },
  {
    align: "right",
    eyebrow: { en: "Case 03 / operations visibility", zh: "案例 03 / 运营可视化" },
    id: "visibility",
    kind: "project",
    label: { en: "Visibility", zh: "运营可视" },
    links: [
      {
        href: "/case-studies/supply-production-delivery-operations-visibility",
        label: { en: "Open case study", zh: "查看完整案例" },
      },
      {
        external: true,
        href: "https://felix-zuo.github.io/factory-excel-ops-dashboard/showcase.html",
        label: { en: "Live project", zh: "打开在线项目" },
      },
    ],
    metrics: [
      {
        label: { en: "Operating span", zh: "运营范围" },
        value: { en: "Supply to delivery", zh: "从供应到交付" },
      },
      {
        label: { en: "Review model", zh: "复盘模型" },
        value: { en: "One consistent view", zh: "一套一致视图" },
      },
    ],
    steps: [
      { en: "Classify source", zh: "分类数据来源" },
      { en: "Normalize recurring inputs", zh: "标准化重复输入" },
      { en: "Review exceptions", zh: "复盘运营异常" },
    ],
    summary: {
      en: "Scattered spreadsheet exports become one operating view for supply, production, delivery, and exception closure.",
      zh: "将分散的表格导出汇聚成统一运营视图，覆盖供应、生产、交付与异常闭环。",
    },
    title: {
      en: "Make the operating exception visible.",
      zh: "让运营异常被及时看见。",
    },
  },
  {
    align: "left",
    eyebrow: { en: "Portfolio lab / connected evidence", zh: "作品实验室 / 互联证据" },
    id: "system",
    kind: "system",
    label: { en: "Systems", zh: "系统" },
    links: [
      {
        external: true,
        href: profile.github,
        label: { en: "Explore GitHub", zh: "探索 GitHub" },
      },
      {
        external: true,
        href: "https://github.com/Felix-Zuo/HulunGuard",
        label: { en: "Open HulunGuard", zh: "查看 HulunGuard" },
      },
    ],
    metrics: [
      {
        label: { en: "Public systems", zh: "公开系统" },
        value: { en: "7 connected projects", zh: "7 个互联项目" },
      },
      {
        label: { en: "Evidence boundary", zh: "证据边界" },
        value: { en: "Sanitized + synthetic", zh: "脱敏 + 合成" },
      },
    ],
    steps: [
      { en: "Operations intelligence", zh: "运营智能" },
      { en: "Manufacturing data", zh: "制造数据" },
      { en: "Six Sigma", zh: "六西格玛" },
      { en: "Reliability", zh: "可靠性" },
    ],
    summary: {
      en: "Data literacy, improvement methods, and evidence-first verification extend the same operating discipline beyond the three case studies.",
      zh: "数据能力、改善方法与证据优先的验证方式，将同一套运营纪律延伸到三个案例之外。",
    },
    title: {
      en: "Evidence that connects beyond one project.",
      zh: "让证据跨越单个项目，形成体系。",
    },
  },
  {
    align: "right",
    eyebrow: { en: "Contact / final frame", zh: "联系 / 最终画面" },
    id: "contact",
    kind: "finale",
    label: { en: "Close", zh: "收束" },
    links: [
      {
        href: `mailto:${profile.email}`,
        label: { en: "Email Felix", zh: "联系 Felix" },
      },
    ],
    metrics: [
      {
        label: { en: "Working mode", zh: "工作方式" },
        value: { en: "Execution + tooling", zh: "落地执行 + 工具构建" },
      },
      {
        label: { en: "Best fit", zh: "最佳匹配" },
        value: { en: "Launch / flow / visibility", zh: "导入 / 流动 / 可视化" },
      },
    ],
    summary: {
      en: "The strongest fit is where manufacturing execution, launch readiness, and practical workflow tooling must work together.",
      zh: "最适合的场景，是制造执行、项目导入准备与实用流程工具必须协同工作的地方。",
    },
    title: { en: "Build the next improvement loop.", zh: "开启下一轮改善闭环。" },
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
const MEDIA_VERSION = 18;
const CRITICAL_PRELOAD_TIMEOUT_MS = 8000;
const BACKGROUND_PRELOAD_DELAY_MS = 100;
const LOCALE_STORAGE_KEY = "felix-portfolio-locale";
const LOCALE_CHANGE_EVENT = "felix-portfolio-locale-change";

const UI_COPY = {
  en: {
    cameraInMotion: "Camera in motion",
    chapterTransition: "Changing chapter",
    clickScene: "Click the scene",
    controlDeckAria: "Felix Zuo operations control deck",
    controlRoom: "Control room",
    finale: "Finale",
    goToChapter: (index: number, label: string) =>
      `Go to chapter ${index}: ${label}`,
    language: "Language",
    loadingAria: "Portfolio is loading",
    loadingPortfolio: "Loading Felix's portfolio",
    nextChapter: (label: string) => `Next chapter: ${label}`,
    openControlRoom: "Open control room",
    operationsMeta: "FZ / Manufacturing operations",
    playNextScene: "Play next scene",
    playTo: (label: string) => `Play to ${label}`,
    portfolioAria: "Felix Zuo manufacturing portfolio",
    previousChapter: "Previous chapter",
    publicSafeMeta: "Public-safe / synthetic",
    routeAria: "Portfolio route",
    startAria: "Begin the portfolio journey",
    startEyebrow: "Felix Zuo / Manufacturing operations",
    startHint: "Click anywhere to begin",
    startSummary:
      "An eight-chapter portfolio across launch readiness, process improvement, and factory workflow systems.",
    startTitle: "From the plant floor to reviewable evidence.",
    startValue: "One click advances one scene",
    switchChinese: "Switch to Chinese",
    switchEnglish: "Switch to English",
    tapScene: "Tap the scene",
  },
  zh: {
    cameraInMotion: "镜头运动中",
    chapterTransition: "正在切换章节",
    clickScene: "点击场景",
    controlDeckAria: "Felix Zuo 工厂项目控制台",
    controlRoom: "项目控制台",
    finale: "终章",
    goToChapter: (index: number, label: string) =>
      `前往第 ${index} 章：${label}`,
    language: "语言",
    loadingAria: "作品集正在载入",
    loadingPortfolio: "正在载入 Felix 的作品集",
    nextChapter: (label: string) => `下一章：${label}`,
    openControlRoom: "进入项目控制台",
    operationsMeta: "FZ / 制造运营",
    playNextScene: "播放下一场景",
    playTo: (label: string) => `播放至 ${label}`,
    portfolioAria: "Felix Zuo 制造业作品集",
    previousChapter: "上一章",
    publicSafeMeta: "公开安全 / 脱敏合成",
    routeAria: "作品集章节导航",
    startAria: "开始浏览作品集",
    startEyebrow: "Felix Zuo / 制造运营",
    startHint: "点击任意位置开始",
    startSummary: "一部横跨项目导入准备、过程改善与工厂流程系统的八章作品集。",
    startTitle: "从车间现场，到可复核的证据。",
    startValue: "每次点击，推进一个场景",
    switchChinese: "切换为中文",
    switchEnglish: "切换为英文",
    tapScene: "轻触场景",
  },
} as const;

function localize(value: LocalizedText, locale: Locale) {
  return value[locale];
}

function getLocaleSnapshot(): Locale {
  const storedLocale = window.localStorage.getItem(LOCALE_STORAGE_KEY);
  return storedLocale === "zh" ? "zh" : "en";
}

function getServerLocaleSnapshot(): Locale {
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

function chapterMediaId(chapter: Chapter) {
  return chapter.visualId ?? chapter.id;
}

function chapterImage(chapter: Chapter, profile: MediaProfile) {
  return `/media/chapters/${chapterMediaId(chapter)}-${profile}.webp?v=${MEDIA_VERSION}`;
}

function chapterHold(chapter: Chapter, profile: MediaProfile) {
  return chapter.ambient?.[profile] ?? null;
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

function chapterNeighborhoodAssets(
  activeIndex: number,
  profile: MediaProfile,
) {
  const neighborIndexes = [activeIndex - 1, activeIndex, activeIndex + 1]
    .filter((index) => index >= 0 && index < CHAPTERS.length);
  const images = neighborIndexes.map((index) =>
    chapterImage(CHAPTERS[index], profile),
  );
  const videos: string[] = [];
  const activeHold = chapterHold(CHAPTERS[activeIndex], profile);
  if (activeHold) videos.push(activeHold);

  neighborIndexes.forEach((index) => {
    if (index === activeIndex) return;
    videos.push(transitionVideoBetween(activeIndex, index, profile));
    const neighborHold = chapterHold(CHAPTERS[index], profile);
    if (neighborHold) videos.push(neighborHold);
  });

  if (neighborIndexes.includes(CHAPTERS.length - 1)) {
    videos.push(controlRoomVideo(profile));
  }

  return {
    images: [...new Set(images)],
    videos: [...new Set(videos)],
  };
}

function releaseWarmVideo(video: HTMLVideoElement) {
  video.pause();
  video.removeAttribute("src");
  video.load();
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

function useMediaPreloader(
  profile: MediaProfile | null,
  activeIndex: number,
) {
  const [progress, setProgress] = useState(0);
  const [ready, setReady] = useState(false);
  const [loadedProfile, setLoadedProfile] = useState<MediaProfile | null>(null);
  const backgroundImagesRef = useRef(new Map<string, HTMLImageElement>());
  const backgroundVideosRef = useRef(new Map<string, HTMLVideoElement>());

  useEffect(() => {
    backgroundImagesRef.current.clear();
    backgroundVideosRef.current.forEach(releaseWarmVideo);
    backgroundVideosRef.current.clear();

    if (!profile) return;

    let cancelled = false;
    let complete = 0;
    const pendingTimers = new Set<number>();
    const pendingImages = new Set<HTMLImageElement>();
    const criticalImages = [
      startImage(profile),
      chapterImage(CHAPTERS[0], profile),
    ];

    const markComplete = () => {
      complete += 1;
      if (!cancelled) {
        setLoadedProfile(profile);
        setProgress(complete / criticalImages.length);
        setReady(complete === criticalImages.length);
      }
    };

    criticalImages.forEach((url) => {
      const image = new window.Image();
      let settled = false;
      const finish = () => {
        if (settled) return;
        settled = true;
        window.clearTimeout(timeout);
        pendingTimers.delete(timeout);
        pendingImages.delete(image);
        image.onload = null;
        image.onerror = null;
        markComplete();
      };
      const timeout = window.setTimeout(
        finish,
        CRITICAL_PRELOAD_TIMEOUT_MS,
      );
      pendingTimers.add(timeout);
      pendingImages.add(image);
      image.onload = finish;
      image.onerror = finish;
      image.src = url;
    });

    return () => {
      cancelled = true;
      pendingTimers.forEach((timer) => window.clearTimeout(timer));
      pendingTimers.clear();
      pendingImages.forEach((image) => {
        image.onload = null;
        image.onerror = null;
      });
      pendingImages.clear();
    };
  }, [profile]);

  useEffect(() => {
    if (!profile || loadedProfile !== profile || !ready) return;

    const timer = window.setTimeout(() => {
      const assets = chapterNeighborhoodAssets(activeIndex, profile);
      const wantedImages = new Set(assets.images);
      const wantedVideos = new Set(assets.videos);

      backgroundImagesRef.current.forEach((image, url) => {
        if (wantedImages.has(url)) return;
        image.onload = null;
        image.onerror = null;
        backgroundImagesRef.current.delete(url);
      });
      wantedImages.forEach((url) => {
        if (backgroundImagesRef.current.has(url)) return;
        const image = new window.Image();
        image.decoding = "async";
        image.src = url;
        backgroundImagesRef.current.set(url, image);
      });

      backgroundVideosRef.current.forEach((video, url) => {
        if (wantedVideos.has(url)) return;
        releaseWarmVideo(video);
        backgroundVideosRef.current.delete(url);
      });
      wantedVideos.forEach((url) => {
        if (backgroundVideosRef.current.has(url)) return;
        const video = document.createElement("video");
        video.muted = true;
        video.playsInline = true;
        video.preload = "auto";
        video.src = url;
        video.load();
        backgroundVideosRef.current.set(url, video);
      });
    }, BACKGROUND_PRELOAD_DELAY_MS);

    return () => window.clearTimeout(timer);
  }, [activeIndex, loadedProfile, profile, ready]);

  useEffect(() => () => {
    backgroundImagesRef.current.clear();
    backgroundVideosRef.current.forEach(releaseWarmVideo);
    backgroundVideosRef.current.clear();
  }, []);

  const isCurrentProfile = loadedProfile === profile;
  return {
    progress: isCurrentProfile ? progress : 0,
    ready: isCurrentProfile && ready,
  };
}

function LocaleSwitch({
  className,
  locale,
  onChange,
}: {
  className?: string;
  locale: Locale;
  onChange: (locale: Locale) => void;
}) {
  const copy = UI_COPY[locale];

  return (
    <div
      aria-label={copy.language}
      className={`${styles.localeSwitch}${className ? ` ${className}` : ""}`}
      onClick={(event) => event.stopPropagation()}
      role="group"
    >
      <button
        aria-pressed={locale === "en"}
        data-active={locale === "en" || undefined}
        lang="en"
        onClick={() => onChange("en")}
        title={copy.switchEnglish}
        type="button"
      >
        EN
      </button>
      <button
        aria-pressed={locale === "zh"}
        data-active={locale === "zh" || undefined}
        lang="zh-CN"
        onClick={() => onChange("zh")}
        title={copy.switchChinese}
        type="button"
      >
        中文
      </button>
    </div>
  );
}

function ExperienceLink({
  link,
  locale,
}: {
  link: ChapterLink;
  locale: Locale;
}) {
  const content = (
    <>
      <span>{localize(link.label, locale)}</span>
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
  const locale = useSyncExternalStore(
    subscribeToLocale,
    getLocaleSnapshot,
    getServerLocaleSnapshot,
  );
  const mediaProfile = useMediaProfile();
  const reducedMotion = useReducedMotion();
  const rootRef = useRef<HTMLElement>(null);
  const transitionVideoRef = useRef<HTMLVideoElement>(null);
  const pointerFrameRef = useRef<number | null>(null);
  const timersRef = useRef(new Set<number>());
  const [activeIndex, setActiveIndex] = useState(0);
  const preloader = useMediaPreloader(mediaProfile, activeIndex);
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

  const copy = UI_COPY[locale];
  const activeChapter = CHAPTERS[activeIndex];
  const outgoingChapter =
    outgoingIndex === null ? null : CHAPTERS[outgoingIndex];
  const isFirst = activeIndex === 0;
  const isLast = activeIndex === CHAPTERS.length - 1;
  const nextChapter = CHAPTERS[Math.min(activeIndex + 1, CHAPTERS.length - 1)];
  const activeChapterLabel = localize(activeChapter.label, locale);
  const nextChapterLabel = localize(nextChapter.label, locale);
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

  const changeLocale = useCallback((nextLocale: Locale) => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, nextLocale);
    window.dispatchEvent(new Event(LOCALE_CHANGE_EVENT));
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

  useEffect(() => {
    document.documentElement.lang = locale === "zh" ? "zh-CN" : "en";
  }, [locale]);

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
      aria-label={controlDeckActive ? copy.controlDeckAria : copy.portfolioAria}
      className={styles.root}
      data-chapter={activeChapter.id}
      data-control-deck={controlDeckActive || undefined}
      data-direction={direction}
      data-door-opening={doorOpening || undefined}
      data-locale={locale}
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
            data-ambient-bridge={
              CHAPTERS[journeyMotion.fromIndex].ambient ? true : undefined
            }
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
        <>
          <span aria-hidden="true" className={styles.jumpVeil} data-phase={jumpPhase} />
          <span className={styles.srOnly} role="status">
            {copy.chapterTransition}
          </span>
        </>
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

          <LocaleSwitch
            className={styles.startLocaleSwitch}
            locale={locale}
            onChange={changeLocale}
          />

          <div className={styles.startContent}>
            <p>{copy.startEyebrow}</p>
            <h1>{copy.startTitle}</h1>
            <span className={styles.startSummary}>{copy.startSummary}</span>

            <button
              aria-label={preloader.ready ? copy.startAria : copy.loadingAria}
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
                <small>
                  {preloader.ready ? copy.startHint : copy.loadingPortfolio}
                </small>
                <strong>
                  {preloader.ready
                    ? copy.startValue
                    : `${Math.round(preloader.progress * 100)}%`}
                </strong>
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
            <span>{copy.operationsMeta}</span>
            <span>{activeChapterLabel}</span>
            <span>{copy.publicSafeMeta}</span>
            <LocaleSwitch
              className={styles.sceneLocaleSwitch}
              locale={locale}
              onChange={changeLocale}
            />
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
              {localize(activeChapter.eyebrow, locale)}
            </p>

            <h1>{localize(activeChapter.title, locale)}</h1>
            <p className={styles.chapterSummary}>
              {localize(activeChapter.summary, locale)}
            </p>

            {activeChapter.kind === "metrics" && activeChapter.metrics && (
              <dl className={styles.impactMetrics}>
                {activeChapter.metrics.map((metric, index) => (
                  <div key={`${activeChapter.id}-impact-${index}`}>
                    <dt>{localize(metric.label, locale)}</dt>
                    <dd>
                      {metric.before && (
                        <span>{localize(metric.before, locale)}</span>
                      )}
                      <strong>{localize(metric.value, locale)}</strong>
                    </dd>
                  </div>
                ))}
              </dl>
            )}

            {activeChapter.kind === "process" && activeChapter.steps && (
              <ol className={styles.evidenceFlow}>
                {activeChapter.steps.map((step, index) => (
                  <li key={`${activeChapter.id}-step-${index}`}>
                    <span>{String(index + 1).padStart(2, "0")}</span>
                    <strong>{localize(step, locale)}</strong>
                  </li>
                ))}
              </ol>
            )}

            {activeChapter.kind !== "metrics" && activeChapter.metrics && (
              <dl className={styles.chapterMetrics}>
                {activeChapter.metrics.map((metric, index) => (
                  <div key={`${activeChapter.id}-metric-${index}`}>
                    <dt>{localize(metric.label, locale)}</dt>
                    <dd>
                      {metric.before && (
                        <span>{localize(metric.before, locale)}</span>
                      )}
                      <strong>{localize(metric.value, locale)}</strong>
                    </dd>
                  </div>
                ))}
              </dl>
            )}

            <div className={styles.chapterActions}>
              {isLast && (
                <button onClick={openControlDeck} type="button">
                  <span>{copy.openControlRoom}</span>
                  <ArrowUpRight aria-hidden="true" size={16} />
                </button>
              )}
              {activeChapter.links?.map((link) => (
                <ExperienceLink
                  key={link.href}
                  link={link}
                  locale={locale}
                />
              ))}
            </div>
            </div>
          </article>

          <div aria-hidden="true" className={styles.sceneAdvanceHint}>
            <MousePointer2 size={16} strokeWidth={1.8} />
            <span>
              <small>
                {mediaProfile === "mobile" ? copy.tapScene : copy.clickScene}
              </small>
              <strong>
                {isLast ? copy.openControlRoom : copy.playTo(nextChapterLabel)}
              </strong>
            </span>
          </div>

          <footer className={styles.transport}>
            <button
              aria-label={copy.previousChapter}
              className={styles.transportBack}
              disabled={isFirst || transitioning}
              onClick={playPreviousSegment}
              title={copy.previousChapter}
              type="button"
            >
              <ArrowLeft aria-hidden="true" size={19} />
            </button>

            <div className={styles.routeReadout}>
              <span>{String(activeIndex + 1).padStart(2, "0")}</span>
              <strong>{activeChapterLabel}</strong>
            </div>

            <nav aria-label={copy.routeAria} className={styles.chapterRail}>
              <ol>
                {CHAPTERS.map((chapter, index) => (
                  <li key={chapter.id}>
                    <button
                      aria-current={index === activeIndex ? "step" : undefined}
                      aria-label={copy.goToChapter(
                        index + 1,
                        localize(chapter.label, locale),
                      )}
                      disabled={transitioning || index === activeIndex}
                      onClick={() => requestNavigation(index)}
                      title={localize(chapter.label, locale)}
                      type="button"
                    >
                      {String(index + 1).padStart(2, "0")}
                    </button>
                  </li>
                ))}
              </ol>
            </nav>

            <button
              aria-label={isLast ? copy.openControlRoom : copy.nextChapter(nextChapterLabel)}
              className={styles.transportNext}
              disabled={transitioning}
              onClick={goForward}
              type="button"
            >
              <span>
                <small>{isLast ? copy.finale : copy.playNextScene}</small>
                <strong>{isLast ? copy.controlRoom : nextChapterLabel}</strong>
              </span>
              <ArrowRight aria-hidden="true" size={19} />
            </button>
          </footer>
        </>
      )}

      {journeyMotion && (
        <div aria-live="polite" className={styles.motionHud}>
          <span>
            <small>{copy.cameraInMotion}</small>
            <strong>
              {localize(CHAPTERS[journeyMotion.toIndex].label, locale)}
            </strong>
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

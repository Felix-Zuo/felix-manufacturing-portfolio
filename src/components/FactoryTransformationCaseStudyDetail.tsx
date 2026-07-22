"use client";

import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
  Boxes,
  CalendarRange,
  CheckCircle2,
  CircleDot,
  Clock3,
  Database,
  Factory,
  GraduationCap,
  Languages,
  Layers3,
  ListChecks,
  Network,
  PackageSearch,
  Route,
  ShieldCheck,
  Target,
  Workflow,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useRef,
  useSyncExternalStore,
  type CSSProperties,
} from "react";

import {
  factoryTransformationCaseStudies,
  type FactoryTransformationCaseStudy,
  type FactoryTransformationCaseStudyId,
  type FactoryTransformationLocale,
  type FlowNodeKind,
  type LocalizedText,
  type VisualizationKind,
} from "@/data/factoryTransformationCaseStudies";

import styles from "./FactoryTransformationCaseStudyDetail.module.css";

const LOCALE_STORAGE_KEY = "felix-portfolio-locale";
const LOCALE_CHANGE_EVENT = "felix-portfolio-locale-change";

const CASE_ICONS: Readonly<
  Record<FactoryTransformationCaseStudyId, LucideIcon>
> = {
  planning: CalendarRange,
  wip: Boxes,
  procurement: PackageSearch,
  resilience: ShieldCheck,
  skills: GraduationCap,
};

const FLOW_ICONS: Readonly<Record<FlowNodeKind, LucideIcon>> = {
  input: Database,
  process: Wrench,
  decision: Target,
  control: ShieldCheck,
  output: CheckCircle2,
  feedback: Route,
};

const HERO_MEDIA: Readonly<
  Record<FactoryTransformationCaseStudyId, { desktop: string; mobile: string }>
> = {
  planning: {
    desktop: "/media/chapters/impact-desktop.webp",
    mobile: "/media/chapters/impact-mobile.webp",
  },
  wip: {
    desktop: "/media/chapters/visibility-desktop.webp",
    mobile: "/media/chapters/visibility-mobile.webp",
  },
  procurement: {
    desktop: "/media/chapters/process-desktop.webp",
    mobile: "/media/chapters/process-mobile.webp",
  },
  resilience: {
    desktop: "/media/chapters/system-desktop.webp",
    mobile: "/media/chapters/system-mobile.webp",
  },
  skills: {
    desktop: "/media/chapters/close-desktop.webp",
    mobile: "/media/chapters/close-mobile.webp",
  },
};

const PRIMARY_VISUALIZATION_INDEX: Readonly<
  Record<FactoryTransformationCaseStudyId, number>
> = {
  planning: 2,
  wip: 0,
  procurement: 2,
  resilience: 2,
  skills: 1,
};

const VISUALIZATION_ICONS: Readonly<Record<VisualizationKind, LucideIcon>> = {
  "before-after": Layers3,
  "decision-tree": Target,
  flow: Workflow,
  gantt: CalendarRange,
  heatmap: Boxes,
  matrix: ListChecks,
  network: Network,
  "risk-map": ShieldCheck,
  timeline: Clock3,
};

const UI_COPY = {
  en: {
    back: "Return to portfolio",
    caseFile: "Factory transformation case",
    publicSafe: "Public-safe evidence",
    localeLabel: "Language",
    overview: "Operating context",
    overviewIntro:
      "The operating condition, control gap, and transformation intent behind the system.",
    facts: "Fact register",
    factNote:
      "Measured results stay separate from structural operating parameters.",
    measured: "Measured",
    approximate: "Approximate",
    structural: "Operating parameter",
    challenge: "Control gaps",
    method: "System response",
    logic: "Operating logic",
    logicIntro:
      "The end-to-end information and decision path used to keep execution connected.",
    linkRegister: "Control and feedback links",
    phases: "Operating cadence",
    phasesIntro:
      "Sequence and trigger points are shown without inventing calendar dates.",
    visual: "Decision visual",
    illustrative: "Illustrative structure / synthetic data",
    fields: "Fields in view",
    visualIndex: "Visualization register",
    implementation: "Implementation record",
    actions: "Key actions",
    outcomes: "Outcome evidence",
    evidenceBoundary: "Evidence boundary",
    quantitative: "Quantitative result",
    qualitative: "Qualitative result",
    role: "Felix's operating role",
    previous: "Previous case",
    next: "Next case",
    openCase: "Open case",
    phase: "Phase",
    node: "Node",
    flowKinds: {
      input: "Input",
      process: "Process",
      decision: "Decision",
      control: "Control",
      output: "Output",
      feedback: "Feedback",
    },
    planningBranches: [
      "Continue the current family",
      "Use the next changeover window",
      "Escalate for immediate review",
    ],
    riskAxes: {
      x: "Response room",
      y: "Production impact",
      low: "Monitor",
      medium: "Prepare",
      high: "Act",
    },
    supplierDimensions: [
      "Quality",
      "Cost",
      "Delivery",
      "Packaging",
      "Technical",
      "Service",
      "Risk",
    ],
    supplierStates: ["Verified", "Review", "Action"],
    skillColumns: ["Day A", "Night A", "Day B", "Night B"],
    skillStates: ["Qualified", "Coached", "Planned"],
    networkCore: "Integrity control",
  },
  zh: {
    back: "返回作品集",
    caseFile: "工厂改善案例",
    publicSafe: "公开安全证据",
    localeLabel: "语言",
    overview: "运营背景",
    overviewIntro: "说明体系改善前的运行状态、控制缺口与改造意图。",
    facts: "事实指标",
    factNote: "量化结果与结构性运行参数严格分开呈现。",
    measured: "实测结果",
    approximate: "约数结果",
    structural: "运行参数",
    challenge: "控制缺口",
    method: "体系响应",
    logic: "运行逻辑",
    logicIntro: "展示信息、判断与现场反馈如何连接成完整执行链。",
    linkRegister: "控制与反馈关系",
    phases: "运行节奏",
    phasesIntro: "仅呈现先后关系与触发条件，不虚构日历日期。",
    visual: "决策图谱",
    illustrative: "结构示意 / 合成数据",
    fields: "图中字段",
    visualIndex: "可视化索引",
    implementation: "实施记录",
    actions: "关键动作",
    outcomes: "成果证据",
    evidenceBoundary: "证据边界",
    quantitative: "量化结果",
    qualitative: "定性结果",
    role: "Felix 的项目职责",
    previous: "上一个案例",
    next: "下一个案例",
    openCase: "打开案例",
    phase: "阶段",
    node: "节点",
    flowKinds: {
      input: "输入",
      process: "处理",
      decision: "判断",
      control: "控制",
      output: "输出",
      feedback: "反馈",
    },
    planningBranches: [
      "延续当前型号族",
      "进入最近换型窗口",
      "升级为立即评审",
    ],
    riskAxes: {
      x: "应对空间",
      y: "生产影响",
      low: "监控",
      medium: "准备",
      high: "行动",
    },
    supplierDimensions: [
      "质量",
      "成本",
      "交付",
      "包装",
      "技术",
      "服务",
      "风险",
    ],
    supplierStates: ["已验证", "待复核", "需行动"],
    skillColumns: ["A线白班", "A线夜班", "B线白班", "B线夜班"],
    skillStates: ["独立", "指导", "计划"],
    networkCore: "一致性控制",
  },
} as const;

function localize(
  value: LocalizedText,
  locale: FactoryTransformationLocale,
) {
  return value[locale];
}

function getLocaleSnapshot(): FactoryTransformationLocale {
  const storedLocale = window.localStorage.getItem(LOCALE_STORAGE_KEY);
  return storedLocale === "zh" ? "zh" : "en";
}

function getServerLocaleSnapshot(): FactoryTransformationLocale {
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

function metricEvidenceLabel(
  qualifier: "measured" | "approximate" | "stated-operating-parameter",
  locale: FactoryTransformationLocale,
) {
  const copy = UI_COPY[locale];
  if (qualifier === "measured") return copy.measured;
  if (qualifier === "approximate") return copy.approximate;
  return copy.structural;
}

function OperationalVisualization({
  caseStudy,
  locale,
}: {
  caseStudy: FactoryTransformationCaseStudy;
  locale: FactoryTransformationLocale;
}) {
  const copy = UI_COPY[locale];
  const visual =
    caseStudy.visualizationSuggestions[
      PRIMARY_VISUALIZATION_INDEX[caseStudy.id]
    ] ?? caseStudy.visualizationSuggestions[0];
  const fields = visual.dataFields.map((field) => localize(field, locale));

  if (caseStudy.id === "planning") {
    return (
      <div className={styles.decisionPlot}>
        <div className={styles.decisionTrigger}>
          <Target aria-hidden="true" />
          <span>{fields[0]}</span>
        </div>
        <div className={styles.decisionBranches}>
          {copy.planningBranches.map((branch, index) => (
            <div className={styles.decisionBranch} key={branch}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <strong>{branch}</strong>
              <small>{fields[index + 1] ?? fields.at(-1)}</small>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (caseStudy.id === "wip") {
    return (
      <div className={styles.networkPlot}>
        <div className={styles.networkCore}>
          <ShieldCheck aria-hidden="true" />
          <span>{copy.networkCore}</span>
        </div>
        {fields.slice(0, 3).map((field, index) => (
          <div
            className={`${styles.networkNode} ${styles[`networkNode${index + 1}`]}`}
            key={field}
          >
            <CircleDot aria-hidden="true" />
            <span>{field}</span>
          </div>
        ))}
      </div>
    );
  }

  if (caseStudy.id === "procurement") {
    const states = [
      copy.riskAxes.low,
      copy.riskAxes.medium,
      copy.riskAxes.high,
    ];
    return (
      <div className={styles.riskPlot}>
        <span className={styles.riskAxisY}>{copy.riskAxes.y}</span>
        <div className={styles.riskGrid}>
          {Array.from({ length: 9 }, (_, index) => {
            const stateIndex = Math.min(2, Math.floor(index / 3) + (index % 3 > 1 ? 1 : 0));
            return (
              <div
                className={`${styles.riskCell} ${styles[`riskLevel${stateIndex}`]}`}
                key={`${states[stateIndex]}-${index}`}
              >
                {states[stateIndex]}
              </div>
            );
          })}
        </div>
        <span className={styles.riskAxisX}>{copy.riskAxes.x}</span>
        <div className={styles.plotFields}>
          {fields.map((field) => (
            <span key={field}>{field}</span>
          ))}
        </div>
      </div>
    );
  }

  if (caseStudy.id === "resilience") {
    return (
      <div className={styles.matrixPlot}>
        <div className={styles.matrixHeader} aria-hidden="true">
          <span />
          <span>Supplier A</span>
          <span>Supplier B</span>
          <span>Supplier C</span>
        </div>
        {copy.supplierDimensions.map((dimension, rowIndex) => (
          <div className={styles.matrixRow} key={dimension}>
            <strong>{dimension}</strong>
            {[0, 1, 2].map((columnIndex) => {
              const stateIndex = (rowIndex + columnIndex) % 3;
              return (
                <span
                  className={`${styles.matrixState} ${styles[`matrixState${stateIndex}`]}`}
                  key={`${dimension}-${columnIndex}`}
                >
                  {copy.supplierStates[stateIndex]}
                </span>
              );
            })}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={styles.heatmapPlot}>
      <div className={styles.heatmapHeader} aria-hidden="true">
        <span />
        {copy.skillColumns.map((column) => (
          <span key={column}>{column}</span>
        ))}
      </div>
      {fields.slice(0, 4).map((field, rowIndex) => (
        <div className={styles.heatmapRow} key={field}>
          <strong>{field}</strong>
          {copy.skillColumns.map((column, columnIndex) => {
            const stateIndex = (rowIndex * 2 + columnIndex) % 3;
            return (
              <span
                className={`${styles.heatCell} ${styles[`heatState${stateIndex}`]}`}
                key={`${field}-${column}`}
              >
                {copy.skillStates[stateIndex]}
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
}

export function FactoryTransformationCaseStudyDetail({
  caseStudy,
}: {
  caseStudy: FactoryTransformationCaseStudy;
}) {
  const locale = useSyncExternalStore(
    subscribeToLocale,
    getLocaleSnapshot,
    getServerLocaleSnapshot,
  );
  const rootRef = useRef<HTMLElement>(null);
  const copy = UI_COPY[locale];
  const CaseIcon = CASE_ICONS[caseStudy.id];
  const heroMedia = HERO_MEDIA[caseStudy.id];
  const heroPrompt = caseStudy.imagePrompts.find(({ use }) => use === "hero");

  const currentIndex = useMemo(
    () =>
      factoryTransformationCaseStudies.findIndex(
        (entry) => entry.id === caseStudy.id,
      ),
    [caseStudy.id],
  );
  const safeIndex = currentIndex >= 0 ? currentIndex : 0;
  const previousCase =
    factoryTransformationCaseStudies[
      (safeIndex - 1 + factoryTransformationCaseStudies.length) %
        factoryTransformationCaseStudies.length
    ];
  const nextCase =
    factoryTransformationCaseStudies[
      (safeIndex + 1) % factoryTransformationCaseStudies.length
    ];

  const heroStyle = {
    "--hero-desktop": `url("${heroMedia.desktop}")`,
    "--hero-mobile": `url("${heroMedia.mobile}")`,
  } as CSSProperties;

  useEffect(() => {
    document.documentElement.lang = locale === "zh" ? "zh-CN" : "en";
  }, [locale]);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;

    const elements = Array.from(
      root.querySelectorAll<HTMLElement>("[data-case-reveal]"),
    );
    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    if (reducedMotion || !("IntersectionObserver" in window)) {
      elements.forEach((element) => element.classList.add(styles.revealVisible));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add(styles.revealVisible);
          observer.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -10% 0px", threshold: 0.12 },
    );

    elements.forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, [caseStudy.id]);

  const changeLocale = (nextLocale: FactoryTransformationLocale) => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, nextLocale);
    window.dispatchEvent(new Event(LOCALE_CHANGE_EVENT));
  };

  return (
    <main className={styles.root} ref={rootRef}>
      <section
        aria-labelledby={`case-title-${caseStudy.id}`}
        className={styles.hero}
      >
        <div
          aria-label={
            heroPrompt
              ? localize(heroPrompt.alt, locale)
              : localize(caseStudy.title, locale)
          }
          className={styles.heroMedia}
          role="img"
          style={heroStyle}
        />
        <div className={styles.heroShade} aria-hidden="true" />
        <div className={styles.heroGrid} aria-hidden="true" />

        <div className={styles.heroInner}>
          <div className={styles.heroUtility}>
            <Link className={styles.backLink} href="/#factory-transformation">
              <ArrowLeft aria-hidden="true" />
              {copy.back}
            </Link>

            <div
              aria-label={copy.localeLabel}
              className={styles.localeSwitch}
              role="group"
            >
              <Languages aria-hidden="true" />
              <button
                aria-pressed={locale === "en"}
                className={locale === "en" ? styles.localeActive : undefined}
                onClick={() => changeLocale("en")}
                type="button"
              >
                EN
              </button>
              <button
                aria-pressed={locale === "zh"}
                className={locale === "zh" ? styles.localeActive : undefined}
                onClick={() => changeLocale("zh")}
                type="button"
              >
                中文
              </button>
            </div>
          </div>

          <div className={styles.heroContent}>
            <div className={styles.heroKicker}>
              <span>{caseStudy.index}</span>
              <CaseIcon aria-hidden="true" />
              <span>{copy.caseFile}</span>
            </div>
            <h1 id={`case-title-${caseStudy.id}`}>
              {localize(caseStudy.title, locale)}
            </h1>
            <p className={styles.heroSubtitle}>
              {localize(caseStudy.subtitle, locale)}
            </p>
            <p className={styles.heroSummary}>
              {localize(caseStudy.summary, locale)}
            </p>
          </div>

          <div className={styles.heroStatus}>
            <span>
              <ShieldCheck aria-hidden="true" />
              {copy.publicSafe}
            </span>
            <span>
              {String(caseStudy.implementationSteps.length).padStart(2, "0")} {copy.phase}
            </span>
          </div>
        </div>
      </section>

      <section
        className={`${styles.section} ${styles.reveal}`}
        data-case-reveal
      >
        <div className={styles.sectionHeading}>
          <div>
            <span className={styles.sectionIndex}>01 / CONTEXT</span>
            <h2>{copy.overview}</h2>
          </div>
          <p>{copy.overviewIntro}</p>
        </div>
        <div className={styles.contextGrid}>
          {caseStudy.background.map((paragraph, index) => (
            <article className={styles.contextItem} key={`${caseStudy.id}-context-${index}`}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <p>{localize(paragraph, locale)}</p>
            </article>
          ))}
        </div>
      </section>

      <section
        className={`${styles.metricBand} ${styles.reveal}`}
        data-case-reveal
      >
        <div className={styles.metricBandInner}>
          <div className={styles.metricBandTitle}>
            <span>02 / EVIDENCE</span>
            <h2>{copy.facts}</h2>
            <p>{copy.factNote}</p>
          </div>
          <div className={styles.metricGrid}>
            {caseStudy.factMetrics.map((metric) => (
              <article className={styles.metric} key={metric.id}>
                <span className={styles.metricEvidence}>
                  {metricEvidenceLabel(metric.qualifier, locale)}
                </span>
                <strong>{localize(metric.value, locale)}</strong>
                <h3>{localize(metric.label, locale)}</h3>
                <p>{localize(metric.context, locale)}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section
        className={`${styles.section} ${styles.reveal}`}
        data-case-reveal
      >
        <div className={styles.dualNarrative}>
          <div className={styles.narrativeColumn}>
            <div className={styles.columnHeading}>
              <Target aria-hidden="true" />
              <div>
                <span>03A</span>
                <h2>{copy.challenge}</h2>
              </div>
            </div>
            <div className={styles.narrativeList}>
              {caseStudy.challenges.map((challenge, index) => (
                <article className={styles.narrativeItem} key={challenge.id}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <div>
                    <h3>{localize(challenge.title, locale)}</h3>
                    <p>{localize(challenge.detail, locale)}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>

          <div className={styles.narrativeColumn}>
            <div className={styles.columnHeading}>
              <Workflow aria-hidden="true" />
              <div>
                <span>03B</span>
                <h2>{copy.method}</h2>
              </div>
            </div>
            <div className={styles.narrativeList}>
              {caseStudy.methods.map((method, index) => (
                <article className={styles.narrativeItem} key={method.id}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <div>
                    <h3>{localize(method.title, locale)}</h3>
                    <p>{localize(method.detail, locale)}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section
        className={`${styles.logicBand} ${styles.reveal}`}
        data-case-reveal
      >
        <div className={styles.logicInner}>
          <div className={styles.sectionHeading}>
            <div>
              <span className={styles.sectionIndex}>04 / SYSTEM</span>
              <h2>{copy.logic}</h2>
            </div>
            <p>{copy.logicIntro}</p>
          </div>

          <div className={styles.flowTitle}>
            <Workflow aria-hidden="true" />
            <h3>{localize(caseStudy.flow.title, locale)}</h3>
          </div>
          <div className={styles.flowTrack}>
            {caseStudy.flow.nodes.map((node, index) => {
              const NodeIcon = FLOW_ICONS[node.kind];
              return (
                <article className={styles.flowNode} key={node.id}>
                  <div className={styles.flowNodeTopline}>
                    <span>{copy.node} {String(index + 1).padStart(2, "0")}</span>
                    <span>{copy.flowKinds[node.kind]}</span>
                  </div>
                  <NodeIcon aria-hidden="true" />
                  <h4>{localize(node.label, locale)}</h4>
                  <p>{localize(node.detail, locale)}</p>
                </article>
              );
            })}
          </div>

          <div className={styles.linkRegister}>
            <span>{copy.linkRegister}</span>
            <div>
              {caseStudy.flow.links.map((link, index) => {
                const from = caseStudy.flow.nodes.find(({ id }) => id === link.from);
                const to = caseStudy.flow.nodes.find(({ id }) => id === link.to);
                if (!from || !to) return null;
                return (
                  <p key={`${link.from}-${link.to}-${index}`}>
                    <span>{localize(from.label, locale)}</span>
                    <ArrowRight aria-hidden="true" />
                    <span>{localize(to.label, locale)}</span>
                    {link.label ? <em>{localize(link.label, locale)}</em> : null}
                  </p>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      <section
        className={`${styles.section} ${styles.reveal}`}
        data-case-reveal
      >
        <div className={styles.sectionHeading}>
          <div>
            <span className={styles.sectionIndex}>05 / CADENCE</span>
            <h2>{copy.phases}</h2>
          </div>
          <p>{copy.phasesIntro}</p>
        </div>
        <div className={styles.phaseTimeline}>
          {caseStudy.phases.map((phase) => (
            <article className={styles.phaseItem} key={phase.id}>
              <span className={styles.phaseSequence}>
                {String(phase.sequence).padStart(2, "0")}
              </span>
              <div>
                <p className={styles.phaseTime}>{localize(phase.timeframe, locale)}</p>
                <h3>{localize(phase.label, locale)}</h3>
                <p>{localize(phase.detail, locale)}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section
        className={`${styles.visualBand} ${styles.reveal}`}
        data-case-reveal
      >
        <div className={styles.visualInner}>
          <div className={styles.visualCopy}>
            <span className={styles.sectionIndex}>06 / VISUAL MODEL</span>
            <h2>{copy.visual}</h2>
            <h3>
              {localize(
                caseStudy.visualizationSuggestions[
                  PRIMARY_VISUALIZATION_INDEX[caseStudy.id]
                ]?.title ?? caseStudy.visualizationSuggestions[0].title,
                locale,
              )}
            </h3>
            <p>
              {localize(
                caseStudy.visualizationSuggestions[
                  PRIMARY_VISUALIZATION_INDEX[caseStudy.id]
                ]?.purpose ?? caseStudy.visualizationSuggestions[0].purpose,
                locale,
              )}
            </p>
            <span className={styles.syntheticLabel}>
              <ShieldCheck aria-hidden="true" />
              {copy.illustrative}
            </span>
          </div>
          <div className={styles.visualPlotWrap}>
            <OperationalVisualization caseStudy={caseStudy} locale={locale} />
          </div>
        </div>

        <div className={styles.visualizationRegister}>
          <span>{copy.visualIndex}</span>
          <div>
            {caseStudy.visualizationSuggestions.map((visualization) => {
              const VisualIcon = VISUALIZATION_ICONS[visualization.kind];
              return (
                <article key={visualization.id}>
                  <VisualIcon aria-hidden="true" />
                  <div>
                    <h3>{localize(visualization.title, locale)}</h3>
                    <p>{localize(visualization.purpose, locale)}</p>
                    <strong>{copy.fields}</strong>
                    <ul>
                      {visualization.dataFields.map((field) => (
                        <li key={localize(field, locale)}>{localize(field, locale)}</li>
                      ))}
                    </ul>
                    <small>{localize(visualization.evidenceBoundary, locale)}</small>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      <section
        className={`${styles.section} ${styles.reveal}`}
        data-case-reveal
      >
        <div className={styles.sectionHeading}>
          <div>
            <span className={styles.sectionIndex}>07 / DELIVERY</span>
            <h2>{copy.implementation}</h2>
          </div>
        </div>
        <div className={styles.implementationRail}>
          {caseStudy.implementationSteps.map((step) => (
            <article className={styles.implementationStep} key={step.id}>
              <div className={styles.stepMarker}>
                <span>{String(step.sequence).padStart(2, "0")}</span>
              </div>
              <div className={styles.stepBody}>
                <h3>{localize(step.title, locale)}</h3>
                <p>{localize(step.detail, locale)}</p>
                <div className={styles.stepActions}>
                  <span>{copy.actions}</span>
                  <ul>
                    {step.actions.map((action) => (
                      <li key={localize(action, locale)}>
                        <CheckCircle2 aria-hidden="true" />
                        {localize(action, locale)}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section
        className={`${styles.outcomeBand} ${styles.reveal}`}
        data-case-reveal
      >
        <div className={styles.outcomeInner}>
          <div className={styles.outcomeHeading}>
            <span className={styles.sectionIndex}>08 / RESULT</span>
            <h2>{copy.outcomes}</h2>
          </div>
          <div className={styles.outcomeList}>
            {caseStudy.outcomes.map((outcome, index) => {
              const linkedMetric = outcome.metricId
                ? caseStudy.factMetrics.find(({ id }) => id === outcome.metricId)
                : undefined;
              return (
                <article className={styles.outcomeItem} key={outcome.id}>
                  <span className={styles.outcomeNumber}>
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <span
                      className={
                        outcome.evidenceKind === "quantitative"
                          ? styles.quantitativeTag
                          : styles.qualitativeTag
                      }
                    >
                      {outcome.evidenceKind === "quantitative"
                        ? copy.quantitative
                        : copy.qualitative}
                    </span>
                    <p>{localize(outcome.statement, locale)}</p>
                    {linkedMetric ? (
                      <strong>
                        {localize(linkedMetric.value, locale)} · {localize(linkedMetric.label, locale)}
                      </strong>
                    ) : null}
                    {outcome.qualification ? (
                      <small>{localize(outcome.qualification, locale)}</small>
                    ) : null}
                  </div>
                </article>
              );
            })}
          </div>

          <aside className={styles.evidenceBoundary}>
            <ShieldCheck aria-hidden="true" />
            <div>
              <h3>{copy.evidenceBoundary}</h3>
              <p>{localize(caseStudy.evidenceBoundary, locale)}</p>
            </div>
          </aside>
        </div>
      </section>

      <section
        className={`${styles.section} ${styles.reveal}`}
        data-case-reveal
      >
        <div className={styles.roleLayout}>
          <div className={styles.roleHeading}>
            <Factory aria-hidden="true" />
            <span className={styles.sectionIndex}>09 / OWNERSHIP</span>
            <h2>{copy.role}</h2>
          </div>
          <ol className={styles.roleList}>
            {caseStudy.roles.map((role, index) => (
              <li key={localize(role, locale)}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <p>{localize(role, locale)}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <nav aria-label="Case study navigation" className={styles.caseNavigation}>
        <Link href={previousCase.href}>
          <ArrowLeft aria-hidden="true" />
          <span>
            <small>{copy.previous}</small>
            <strong>{localize(previousCase.title, locale)}</strong>
          </span>
        </Link>
        <Link href={nextCase.href}>
          <span>
            <small>{copy.next}</small>
            <strong>{localize(nextCase.title, locale)}</strong>
          </span>
          <ArrowRight aria-hidden="true" />
        </Link>
      </nav>
    </main>
  );
}

export type MetricCount = {
  from: number;
  to: number;
  /** Rendered during animation; `{n}` is replaced with the current value. */
  template: string;
  /** Final display override once the animation settles (e.g. "<1 min"). */
  final?: string;
};

export type Metric = {
  id: string;
  label: string;
  /** The baseline reading shown struck-through above the animated value. */
  before?: string;
  /** Static display value (fallback and reduced-motion rendering). */
  value: string;
  count?: MetricCount;
  detail: string;
  source: string;
  tone: "blue" | "amber" | "green" | "steel";
};

export type WorkflowStep = {
  label: string;
  detail: string;
};

export type CaseStudy = {
  slug: string;
  title: string;
  subtitle: string;
  summary: string;
  metricIds: string[];
  problem: string;
  role: string;
  methods: string[];
  actions: string[];
  outcomes: string[];
  before: WorkflowStep[];
  after: WorkflowStep[];
  evidenceProjectIds: string[];
  image: string;
  imageAlt: string;
  /** URL shown in the browser-frame address bar for the case visual. */
  imageSourceUrl?: string;
};

export type PortfolioProject = {
  id: string;
  tier: "Main evidence" | "System concept" | "Method support" | "Experimental";
  title: string;
  description: string;
  evidenceRole: string;
  stack: string;
  maturity: string;
  dataBoundary: string;
  repoUrl?: string;
  liveUrl?: string;
  image?: string;
  imageAlt?: string;
  relatedCaseSlugs: string[];
};

export type MethodologyPillar = {
  title: string;
  summary: string;
  practices: string[];
};

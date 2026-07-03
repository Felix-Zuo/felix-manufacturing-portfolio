export type Metric = {
  id: string;
  value: string;
  label: string;
  detail: string;
  source: string;
  tone: "blue" | "amber" | "green" | "steel";
};

export type WorkflowStep = {
  label: string;
  detail: string;
};

export type EvidenceLink = {
  label: string;
  href: string;
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


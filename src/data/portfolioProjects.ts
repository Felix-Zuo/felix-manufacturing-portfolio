import type { PortfolioProject } from "./types";

export const portfolioProjects: PortfolioProject[] = [
  {
    id: "takt-simulator",
    tier: "Main evidence",
    title: "Factory Takt Simulator",
    description:
      "Visual takt-time and flow-simulation workstation for modular discrete-manufacturing lines.",
    evidenceRole:
      "Supports trial production, bottleneck review, buffer tuning, transfer constraints, and capacity reporting.",
    stack: "React, TypeScript, Vite, Electron, deterministic simulation",
    maturity: "Public product page, screenshots, smoke coverage, quality docs",
    dataBoundary: "Synthetic scenarios with generic process names and public-safe screenshots.",
    repoUrl: "https://github.com/Felix-Zuo/factory-takt-simulator",
    liveUrl: "https://felix-zuo.github.io/factory-takt-simulator/?view=showcase",
    image: "/evidence/takt-simulator-product.png",
    imageAlt: "Factory Takt Simulator public product page in English",
    relatedCaseSlugs: ["trial-production-takt-simulation-changeover-improvement"],
  },
  {
    id: "notice-workbench",
    tier: "Main evidence",
    title: "Structured Operations Notice Workbench",
    description:
      "Local-first work-package workbench that turns structured requests into Excel notices, browser previews, manifests, and workflow context.",
    evidenceRole:
      "Supports production notice standardization, structured input, schedule-linked generation, and human review gates.",
    stack: "Python, openpyxl, CLI, local HTTP demo boundary",
    maturity: "Public v0.4 contract, templates, CSV imports, schedule generation, privacy docs",
    dataBoundary: "Synthetic public samples with generic operations terminology.",
    repoUrl: "https://github.com/Felix-Zuo/factory-production-notice-agent",
    liveUrl: "https://felix-zuo.github.io/factory-production-notice-agent/showcase.html",
    image: "/evidence/notice-workbench-product.png",
    imageAlt: "Structured Operations Notice Workbench public product page in English",
    relatedCaseSlugs: ["production-notice-workflow-standardization"],
  },
  {
    id: "excel-dashboard",
    tier: "Main evidence",
    title: "Factory Excel Ops Dashboard",
    description:
      "Spreadsheet operations workbench for classifying files, normalizing headers, computing metrics, and exporting local dashboards.",
    evidenceRole:
      "Supports supply-production-delivery visibility, reporting consistency, and repeated-check reduction.",
    stack: "Python package, CLI, openpyxl, standalone HTML output",
    maturity: "Public product page, config profiles, packaging checks, quality gates",
    dataBoundary: "Reusable source, synthetic fixtures, generic profiles, and private adapter boundary.",
    repoUrl: "https://github.com/Felix-Zuo/factory-excel-ops-dashboard",
    liveUrl: "https://felix-zuo.github.io/factory-excel-ops-dashboard/showcase.html",
    image: "/evidence/excel-ops-product.png",
    imageAlt: "Operations Data Workbench public product page in English",
    relatedCaseSlugs: ["supply-production-delivery-operations-visibility"],
  },
  {
    id: "ops-platform",
    tier: "System concept",
    title: "Operations Intelligence Platform",
    description:
      "Personal synthetic-data concept demo for a local control tower across demand, BOM, inventory, release gates, line simulation, and tool traces.",
    evidenceRole:
      "Shows how separate public tooling directions can connect into a reviewable operations intelligence layer.",
    stack: "FastAPI, React, TypeScript, deterministic Python domain functions",
    maturity: "Public showcase, demo snapshot, API routes, source refs, validation suite",
    dataBoundary: "Public demo only; mock/stub/sample adapters, no live factory systems.",
    repoUrl: "https://github.com/Felix-Zuo/factory-ops-intelligence-platform",
    liveUrl: "https://felix-zuo.github.io/factory-ops-intelligence-platform/showcase.html",
    image: "/evidence/ops-platform-product.png",
    imageAlt: "Operations Intelligence Platform public product page in English",
    relatedCaseSlugs: [
      "production-notice-workflow-standardization",
      "trial-production-takt-simulation-changeover-improvement",
      "supply-production-delivery-operations-visibility",
    ],
  },
  {
    id: "data-pocket-lab",
    tier: "Method support",
    title: "Factory Data Pocket Lab",
    description:
      "Offline Android pocket lab for manufacturing data modeling, traceability, vocabulary, and operations analysis concepts.",
    evidenceRole:
      "Supports the material readiness and manufacturing data literacy side of the portfolio.",
    stack: "Android WebView, JavaScript content bundle",
    maturity: "Public Android demo with generic manufacturing data concepts",
    dataBoundary: "Synthetic factory data concepts only.",
    repoUrl: "https://github.com/Felix-Zuo/factory-data-pocket-lab",
    relatedCaseSlugs: ["supply-production-delivery-operations-visibility"],
  },
  {
    id: "six-sigma-study",
    tier: "Method support",
    title: "Six Sigma Study App",
    description:
      "Local-first Android/PWA bilingual study platform with content validation, vocabulary, notes, and practice workflows.",
    evidenceRole:
      "Supports Lean/Six Sigma learning discipline and validation-heavy content workflow thinking.",
    stack: "React, Vite, Capacitor, TypeScript, Python validation scripts",
    maturity: "Public README, validation matrix, Android/PWA build path",
    dataBoundary: "Personal study and non-commercial rights boundary documented in the repository.",
    repoUrl: "https://github.com/Felix-Zuo/six-sigma-study-app",
    relatedCaseSlugs: [],
  },
  {
    id: "hulunguard",
    tier: "Experimental",
    title: "HulunGuard",
    description:
      "Proof-first reliability guard for long-running AI agent work, focused on evidence, task drift, unresolved failures, and verification.",
    evidenceRole:
      "Shows verification thinking for AI-assisted development workflows without taking over the manufacturing story.",
    stack: "Python CLI, SDK, MCP, local HTTP collector, trace adapters",
    maturity: "Public project page, validation suite, release workflow, observability docs",
    dataBoundary: "Synthetic public examples; private traces and raw payloads stay local by default.",
    repoUrl: "https://github.com/Felix-Zuo/HulunGuard",
    liveUrl: "https://felix-zuo.github.io/HulunGuard/",
    relatedCaseSlugs: [],
  },
];

export function projectsByIds(ids: string[]) {
  return portfolioProjects.filter((project) => ids.includes(project.id));
}


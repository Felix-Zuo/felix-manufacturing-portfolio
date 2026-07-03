import type { CaseStudy } from "./types";

export const caseStudies: CaseStudy[] = [
  {
    slug: "production-notice-workflow-standardization",
    title: "Production Notice Workflow Standardization",
    subtitle: "From cross-system manual checking to standard-compliant release in under 1 minute.",
    summary:
      "Standardized BOM, inventory, process, planning, and delivery inputs into a repeatable notice generation workflow with reviewable output.",
    metricIds: ["notice-time"],
    problem:
      "Production notice preparation required repeated checks across TC, ERP, BOM records, inventory data, process requirements, production schedules, and delivery information. The process often depended on experienced users and created execution risk through manual copying, missing information, and coordination errors.",
    role:
      "Felix supported the workflow improvement by clarifying the input information, mapping data relationships, and building a tool-assisted generation flow that kept release behind human review.",
    methods: [
      "Workflow standardization",
      "Cross-system information mapping",
      "BOM/material verification",
      "ERP/TC data alignment",
      "Production notice format standardization",
      "Human review before release",
      "PDCA-style iteration",
    ],
    actions: [
      "Standardized required fields for project/order, material, process, planning, inventory, and delivery information.",
      "Mapped legacy manufacturing terms into a reusable public operations notice contract.",
      "Generated Excel notices, browser previews, manifests, and workflow context from structured inputs.",
      "Kept final operational release as a review step instead of full automation.",
    ],
    outcomes: [
      "Production notice preparation reduced from around 20-40 minutes to under 1 minute.",
      "Less-experienced users can prepare standard-compliant notices with fewer repeated checks.",
      "Reduced manual copying, missing information, coordination errors, and rework.",
    ],
    before: [
      { label: "TC", detail: "Check process and project context." },
      { label: "ERP", detail: "Confirm order, material, and status data." },
      { label: "BOM", detail: "Verify required material structure." },
      { label: "Inventory", detail: "Check availability and exceptions." },
      { label: "Manual notice", detail: "Copy, calculate, format, and review." },
    ],
    after: [
      { label: "Standard input", detail: "Use validated structured work-package fields." },
      { label: "Generation logic", detail: "Create notice, preview, manifest, and context." },
      { label: "Human review", detail: "Check output before release." },
      { label: "Release packet", detail: "Share consistent artifacts for execution." },
    ],
    evidenceProjectIds: ["notice-workbench"],
    image: "/evidence/notice-output.png",
    imageAlt: "Structured operations notice output preview",
  },
  {
    slug: "trial-production-takt-simulation-changeover-improvement",
    title: "Trial Production Takt Simulation & Changeover Improvement",
    subtitle: "Reducing adjustment cycle, scrap, and repeated trial-and-error before ramp-up.",
    summary:
      "Modeled full-line takt, machine parameters, buffers, and bottlenecks to support engineering adjustment before mass-production ramp-up.",
    metricIds: ["takt-cycle", "scrap-reduction", "changeover-saving"],
    problem:
      "Trial production and model changeover preparation relied heavily on physical trial-and-error. Full-line bottlenecks were difficult to identify early, which increased debugging time, scrap material, and coordination load.",
    role:
      "Felix worked with engineering teams during trial production to simulate full-line takt time, import machine parameters, identify mass-production bottlenecks, and turn observations into repeatable analysis.",
    methods: [
      "Trial production coordination",
      "Full-line takt simulation",
      "Machine parameter input",
      "Bottleneck calculation",
      "Engineering/process adjustment support",
      "Lean waste reduction",
      "PDCA improvement cycle",
    ],
    actions: [
      "Modeled process flow, transfer logic, buffers, waiting, blocking, and station capacity.",
      "Compared machine takt assumptions against downstream and upstream constraints.",
      "Identified likely bottleneck stations and adjustment priorities before ramp-up.",
      "Converted trial observations into a repeatable scenario and capacity report.",
    ],
    outcomes: [
      "Trial analysis and adjustment cycle shortened from around 3 days to 1 day.",
      "Trial machining and debugging scrap material reduced by around 90 percent.",
      "Estimated saving for a regular model changeover reached around RMB 20,000 per changeover.",
    ],
    before: [
      { label: "Physical trial", detail: "Wait for enough real trial data." },
      { label: "Manual judgment", detail: "Discuss bottlenecks after symptoms appear." },
      { label: "Repeated adjustment", detail: "Change parameters through trial-and-error." },
      { label: "Scrap and delay", detail: "Consume material and engineering time." },
    ],
    after: [
      { label: "Line model", detail: "Represent processes, buffers, transfer rules, and station takt." },
      { label: "Simulation", detail: "Run output, utilization, waiting, and blocking checks." },
      { label: "Bottleneck review", detail: "Prioritize stations and links with evidence." },
      { label: "Ramp-up support", detail: "Adjust earlier with lower trial waste." },
    ],
    evidenceProjectIds: ["takt-simulator"],
    image: "/evidence/factory-takt-showcase.png",
    imageAlt: "Factory Takt Simulator public product showcase",
  },
  {
    slug: "supply-production-delivery-operations-visibility",
    title: "Supply-Production-Delivery Operations Visibility",
    subtitle: "Improving visibility across procurement, inventory, WIP, production, delivery, and exceptions.",
    summary:
      "Turned scattered spreadsheet exports and manual summaries into local dashboards, metrics, warnings, and reporting-ready context.",
    metricIds: [],
    problem:
      "Procurement, shipping, inventory, production, WIP, delivery, and historical project information were scattered across spreadsheets, system exports, shared files, and message records. This created repeated checking, waiting time, inconsistent reporting, and delayed exception follow-up.",
    role:
      "Felix built and maintained a supply-production-delivery operations dashboard used in departmental workflow and reporting analysis.",
    methods: [
      "Data consolidation",
      "Spreadsheet workflow improvement",
      "Standardized reporting",
      "Exception follow-up",
      "Project progress visibility",
      "Lean waste reduction",
    ],
    actions: [
      "Classified spreadsheet-like files by content rather than filename alone.",
      "Normalized noisy headers into a standard operations data model.",
      "Computed configurable metrics across inventory, demand, fulfillment, replenishment, and work output.",
      "Exported local dashboard and JSON summaries for reporting and workflow handoff.",
    ],
    outcomes: [
      "Improved visibility across supply, production, delivery, project progress, and exception follow-up.",
      "Supported departmental workflow and reporting analysis.",
      "Reduced waiting, repeated manual checks, information searching, over-processing, coordination errors, and rework.",
    ],
    before: [
      { label: "Separate exports", detail: "Spreadsheets, system downloads, and shared files." },
      { label: "Noisy headers", detail: "Changing names, units, spacing, and local edits." },
      { label: "Manual summary", detail: "Repeated copy-paste and inconsistent reporting." },
      { label: "Slow follow-up", detail: "Exceptions take longer to surface and close." },
    ],
    after: [
      { label: "Classify", detail: "Recognize file type by headers, values, and hints." },
      { label: "Normalize", detail: "Map raw headers into standard records." },
      { label: "Calculate", detail: "Run reusable metric profiles." },
      { label: "Review", detail: "Export dashboard and reporting context." },
    ],
    evidenceProjectIds: ["excel-dashboard"],
    image: "/evidence/excel-workbench-product.png",
    imageAlt: "Factory Excel Ops Dashboard product preview",
  },
];

export function getCaseStudy(slug: string) {
  return caseStudies.find((caseStudy) => caseStudy.slug === slug);
}


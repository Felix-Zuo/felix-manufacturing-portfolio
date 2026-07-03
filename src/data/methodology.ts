import type { MethodologyPillar } from "./types";

export const methodology: MethodologyPillar[] = [
  {
    title: "Project Control",
    summary: "Keep launch and delivery work visible enough for cross-functional teams to act.",
    practices: [
      "Gantt charts",
      "Milestone tracking",
      "Issue lists",
      "Cross-functional follow-up",
      "Regular reporting",
      "Delivery tracking",
    ],
  },
  {
    title: "Manufacturing Launch Support",
    summary: "Bridge quality, process, material, production, and shipment readiness.",
    practices: [
      "DFMEA-related follow-up",
      "Process requirement checks",
      "BOM/material readiness",
      "PPAP support",
      "Trial production",
      "Mass production preparation",
      "Audit support",
      "Corrective action closure",
    ],
  },
  {
    title: "Lean / Continuous Improvement",
    summary: "Frame digital tools around waste reduction and measurable operating outcomes.",
    practices: [
      "PDCA cycles",
      "Lean/Six Sigma thinking",
      "Scrap reduction",
      "Waiting-time reduction",
      "Repeated manual check reduction",
      "Information searching reduction",
      "Rework reduction",
    ],
  },
  {
    title: "Digital Workflow Tools",
    summary: "Convert scattered data and manual checks into structured, reviewable workflows.",
    practices: [
      "Structured input contracts",
      "Production notice generation",
      "Supply-production-delivery visibility",
      "Takt simulation",
      "BOM/material traceability",
      "Local dashboards",
      "Reviewable reports",
    ],
  },
];


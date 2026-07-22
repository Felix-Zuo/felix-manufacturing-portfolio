export type FactoryProjectId =
  | "planning"
  | "wip"
  | "procurement"
  | "resilience"
  | "skills";

export type FactoryProjectAtlasEntry = {
  description: string;
  futureHref: string;
  id: FactoryProjectId;
  index: string;
  label: string;
  metric: string;
  metricLabel: string;
  scene: {
    labelSide: "bottom" | "left" | "right";
    x: number;
    y: number;
  };
  scope: string;
  signals: readonly string[];
  shortLabel: string;
  title: string;
};

export const factoryProjectAtlas: readonly FactoryProjectAtlasEntry[] = [
  {
    description:
      "An order-led rolling plan that pulls demand backward from finished goods into upstream operations, while keeping expedites visible and controlled.",
    futureHref: "/case-studies/pull-based-rolling-production-scheduling",
    id: "planning",
    index: "01",
    label: "Planning Control",
    metric: "~80% less",
    metricLabel: "inter-process carryover",
    scene: { labelSide: "right", x: 13.4, y: 34.5 },
    scope: "Plan / pull / adjust",
    signals: [
      "Order and forecast demand",
      "Backward process pull",
      "Controlled expedite review",
    ],
    shortLabel: "Rolling Plan",
    title: "Pull-Based Rolling Production Scheduling",
  },
  {
    description:
      "A practical WIP governance model that connects batch identity, order status, shop-floor records, and independent physical-count controls.",
    futureHref: "/case-studies/wip-data-governance-inventory-integrity",
    id: "wip",
    index: "02",
    label: "WIP & Inventory",
    metric: "+20%",
    metricLabel: "inventory accuracy",
    scene: { labelSide: "right", x: 31.5, y: 52.5 },
    scope: "Account / card / material",
    signals: [
      "Batch-code mapping",
      "Order-linked WIP board",
      "Three-stage physical count",
    ],
    shortLabel: "WIP Integrity",
    title: "WIP Data Governance & Inventory Integrity",
  },
  {
    description:
      "An order-to-material planning chain that expands BOM demand, nets inventory and WIP, then works backward from production need dates.",
    futureHref: "/case-studies/bom-driven-procurement-risk-warning",
    id: "procurement",
    index: "03",
    label: "Procurement Control",
    metric: "BOM to PO",
    metricLabel: "closed-loop demand",
    scene: { labelSide: "bottom", x: 50, y: 40.5 },
    scope: "Demand / netting / lead time",
    signals: [
      "Multi-level BOM expansion",
      "Inventory and WIP netting",
      "Lead-time risk alerts",
    ],
    shortLabel: "BOM Planning",
    title: "BOM-Driven Procurement & Supply Risk",
  },
  {
    description:
      "A risk-driven supplier system for an overseas plant, combining technical selection, delivery, quality, packaging, logistics, and response capability.",
    futureHref: "/case-studies/overseas-supply-chain-resilience",
    id: "resilience",
    index: "04",
    label: "Supplier Resilience",
    metric: "7 signals",
    metricLabel: "supplier risk model",
    scene: { labelSide: "left", x: 89.2, y: 34.5 },
    scope: "Quality / delivery / risk",
    signals: [
      "Lifecycle grinding cost",
      "Supplier OTD and quality",
      "Packaging and rust prevention",
    ],
    shortLabel: "Supply Risk",
    title: "Overseas Supply-Chain Resilience",
  },
  {
    description:
      "A daily execution system that turns training plans into verified skills and connects capability building with standard work, maintenance, 5S, and EHS.",
    futureHref: "/case-studies/frontline-skills-standard-work",
    id: "skills",
    index: "05",
    label: "Skills & Standards",
    metric: "Daily",
    metricLabel: "training execution loop",
    scene: { labelSide: "left", x: 76, y: 58.5 },
    scope: "Train / verify / sustain",
    signals: [
      "Daily training tasks",
      "Skill validation matrix",
      "5S, PM, and EHS execution",
    ],
    shortLabel: "Skill System",
    title: "Frontline Skills & Standard Work",
  },
] as const;

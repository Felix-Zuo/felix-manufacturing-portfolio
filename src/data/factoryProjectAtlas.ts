export type FactoryProjectLocale = "zh" | "en";

export type FactoryProjectText = Readonly<
  Record<FactoryProjectLocale, string>
>;

export type FactoryProjectId =
  | "planning"
  | "wip"
  | "procurement"
  | "resilience"
  | "skills";

export type FactoryProjectAtlasEntry = {
  description: FactoryProjectText;
  futureHref: string;
  id: FactoryProjectId;
  index: string;
  label: FactoryProjectText;
  metric: FactoryProjectText;
  metricLabel: FactoryProjectText;
  scene: {
    labelSide: "bottom" | "left" | "right";
    x: number;
    y: number;
  };
  scope: FactoryProjectText;
  signals: readonly FactoryProjectText[];
  shortLabel: FactoryProjectText;
  title: FactoryProjectText;
};

export const factoryProjectAtlas: readonly FactoryProjectAtlasEntry[] = [
  {
    description: {
      en: "An order-led rolling plan that pulls demand backward from finished goods into upstream operations, while keeping expedites visible and controlled.",
      zh: "以订单需求为起点，从成品向前道工序逐级拉动，并将插单纳入可见、受控的评审与同步机制。",
    },
    futureHref: "/case-studies/pull-based-rolling-production-scheduling",
    id: "planning",
    index: "01",
    label: { en: "Planning Control", zh: "计划控制" },
    metric: { en: "~80% less", zh: "约减少 80%" },
    metricLabel: { en: "inter-process carryover", zh: "工序间带料" },
    scene: { labelSide: "right", x: 13.4, y: 34.5 },
    scope: { en: "Plan / pull / adjust", zh: "计划 / 拉动 / 调整" },
    signals: [
      { en: "Order and forecast demand", zh: "订单与预测需求" },
      { en: "Backward process pull", zh: "由后向前工序拉动" },
      { en: "Controlled expedite review", zh: "受控插单评审" },
    ],
    shortLabel: { en: "Rolling Plan", zh: "滚动排产" },
    title: {
      en: "Pull-Based Rolling Production Scheduling",
      zh: "基于拉动式生产的滚动排产体系重构",
    },
  },
  {
    description: {
      en: "A practical WIP governance model that connects batch identity, order status, shop-floor records, and independent physical-count controls.",
      zh: "连接批次身份、订单状态、现场记录与独立盘点控制，建立可落地的在制品数据治理体系。",
    },
    futureHref: "/case-studies/wip-data-governance-inventory-integrity",
    id: "wip",
    index: "02",
    label: { en: "WIP & Inventory", zh: "在制品与库存" },
    metric: { en: "+20%", zh: "+20%" },
    metricLabel: { en: "inventory accuracy", zh: "库存准确率" },
    scene: { labelSide: "right", x: 31.5, y: 52.5 },
    scope: { en: "Account / card / material", zh: "账 / 卡 / 物" },
    signals: [
      { en: "Batch-code mapping", zh: "批次编码映射" },
      { en: "Order-linked WIP board", zh: "订单关联在制品看板" },
      { en: "Three-stage physical count", zh: "三阶段实物盘点" },
    ],
    shortLabel: { en: "WIP Integrity", zh: "账卡物一致" },
    title: {
      en: "WIP Data Governance & Inventory Integrity",
      zh: "海外工厂 WIP 数据治理与“账卡物一致”盘存体系建设",
    },
  },
  {
    description: {
      en: "An order-to-material planning chain that expands BOM demand, nets inventory and WIP, then works backward from production need dates.",
      zh: "从订单需求自动展开 BOM，扣减库存与在制品，再从生产需求日期倒排采购与到料节点。",
    },
    futureHref: "/case-studies/bom-driven-procurement-risk-warning",
    id: "procurement",
    index: "03",
    label: { en: "Procurement Control", zh: "采购控制" },
    metric: { en: "BOM to PO", zh: "BOM 至采购" },
    metricLabel: { en: "closed-loop demand", zh: "闭环需求链" },
    scene: { labelSide: "bottom", x: 50, y: 40.5 },
    scope: { en: "Demand / netting / lead time", zh: "需求 / 净算 / 提前期" },
    signals: [
      { en: "Multi-level BOM expansion", zh: "多层级 BOM 展开" },
      { en: "Inventory and WIP netting", zh: "库存与在制品净算" },
      { en: "Lead-time risk alerts", zh: "采购提前期风险预警" },
    ],
    shortLabel: { en: "BOM Planning", zh: "BOM 采购计划" },
    title: {
      en: "BOM-Driven Procurement & Supply Risk Warning",
      zh: "基于 BOM 自动展开与供应风险预警的采购计划体系建设",
    },
  },
  {
    description: {
      en: "A risk-driven supplier system for an overseas plant, combining technical selection, delivery, quality, packaging, logistics, and response capability.",
      zh: "面向海外制造基地，以风险为主线整合技术选型、交付、质量、包装、物流与异常响应能力。",
    },
    futureHref: "/case-studies/overseas-supply-chain-resilience",
    id: "resilience",
    index: "04",
    label: { en: "Supplier Resilience", zh: "供应韧性" },
    metric: { en: "7 signals", zh: "7 类信号" },
    metricLabel: { en: "supplier risk model", zh: "供应商风险模型" },
    scene: { labelSide: "left", x: 89.2, y: 34.5 },
    scope: { en: "Quality / delivery / risk", zh: "质量 / 交付 / 风险" },
    signals: [
      { en: "Lifecycle grinding cost", zh: "磨削全生命周期成本" },
      { en: "Supplier OTD and quality", zh: "供应商交付与质量" },
      { en: "Packaging and rust prevention", zh: "包装与防锈控制" },
    ],
    shortLabel: { en: "Supply Risk", zh: "供应风险" },
    title: {
      en: "Overseas Manufacturing Supply-Chain Resilience",
      zh: "海外制造基地供应链韧性与供应商管理优化",
    },
  },
  {
    description: {
      en: "A daily execution system that turns training plans into verified skills and connects capability building with standard work, maintenance, 5S, and EHS.",
      zh: "将培训计划转化为每日任务与技能验证，并把能力建设连接到标准作业、维护、5S 与 EHS 执行。",
    },
    futureHref: "/case-studies/frontline-skills-standard-work",
    id: "skills",
    index: "05",
    label: { en: "Skills & Standards", zh: "技能与标准" },
    metric: { en: "Daily", zh: "每日" },
    metricLabel: { en: "training execution loop", zh: "培训执行闭环" },
    scene: { labelSide: "left", x: 76, y: 58.5 },
    scope: { en: "Train / verify / sustain", zh: "培训 / 验证 / 固化" },
    signals: [
      { en: "Daily training tasks", zh: "每日培训任务" },
      { en: "Skill validation matrix", zh: "技能验证矩阵" },
      { en: "5S, PM, and EHS execution", zh: "5S、设备维护与 EHS 执行" },
    ],
    shortLabel: { en: "Skill System", zh: "技能体系" },
    title: {
      en: "Frontline Skills & Standard Work",
      zh: "海外工厂一线技能培养与现场标准化管理体系建设",
    },
  },
] as const;

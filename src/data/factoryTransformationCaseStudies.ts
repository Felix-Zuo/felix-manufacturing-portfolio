export type FactoryTransformationLocale = "zh" | "en";

export type LocalizedText = Readonly<
  Record<FactoryTransformationLocale, string>
>;

export type FactoryTransformationCaseStudyId =
  | "planning"
  | "wip"
  | "procurement"
  | "resilience"
  | "skills";

export type FactoryTransformationCaseStudySlugById = {
  planning: "pull-based-rolling-production-scheduling";
  wip: "wip-data-governance-inventory-integrity";
  procurement: "bom-driven-procurement-risk-warning";
  resilience: "overseas-supply-chain-resilience";
  skills: "frontline-skills-standard-work";
};

export type FactoryTransformationCaseStudySlug =
  FactoryTransformationCaseStudySlugById[FactoryTransformationCaseStudyId];

export type EvidenceKind = "quantitative" | "qualitative" | "structural";

export type FactMetric = {
  id: string;
  value: LocalizedText;
  label: LocalizedText;
  context: LocalizedText;
  evidenceKind: Exclude<EvidenceKind, "qualitative">;
  qualifier: "measured" | "approximate" | "stated-operating-parameter";
};

export type NarrativePoint = {
  id: string;
  title: LocalizedText;
  detail: LocalizedText;
};

export type ImplementationStep = NarrativePoint & {
  sequence: number;
  actions: readonly LocalizedText[];
};

export type CaseStudyOutcome = {
  id: string;
  statement: LocalizedText;
  evidenceKind: "quantitative" | "qualitative";
  metricId?: string;
  qualification?: LocalizedText;
};

export type FlowNodeKind =
  | "input"
  | "process"
  | "decision"
  | "control"
  | "output"
  | "feedback";

export type FlowNode = {
  id: string;
  kind: FlowNodeKind;
  label: LocalizedText;
  detail: LocalizedText;
};

export type FlowLink = {
  from: string;
  to: string;
  label?: LocalizedText;
};

export type CaseStudyPhase = {
  id: string;
  sequence: number;
  label: LocalizedText;
  timeBasis:
    | "sequence-only"
    | "daily"
    | "rolling-horizon"
    | "event-driven"
    | "recurring-control";
  timeframe: LocalizedText;
  detail: LocalizedText;
};

export type VisualizationKind =
  | "before-after"
  | "decision-tree"
  | "flow"
  | "gantt"
  | "heatmap"
  | "matrix"
  | "network"
  | "risk-map"
  | "timeline";

export type VisualizationSuggestion = {
  id: string;
  kind: VisualizationKind;
  title: LocalizedText;
  purpose: LocalizedText;
  dataFields: readonly LocalizedText[];
  evidenceBoundary: LocalizedText;
};

export type CaseStudyImagePrompt = {
  id: string;
  use: "hero" | "section" | "transition";
  aspectRatio: "16:9" | "4:3" | "1:1";
  prompt: LocalizedText;
  negativePrompt: LocalizedText;
  alt: LocalizedText;
};

export type FactoryTransformationCaseStudy<
  Id extends FactoryTransformationCaseStudyId = FactoryTransformationCaseStudyId,
> = {
  id: Id;
  index: string;
  slug: FactoryTransformationCaseStudySlugById[Id];
  href: `/case-studies/${FactoryTransformationCaseStudySlugById[Id]}`;
  title: LocalizedText;
  subtitle: LocalizedText;
  summary: LocalizedText;
  background: readonly LocalizedText[];
  challenges: readonly NarrativePoint[];
  methods: readonly NarrativePoint[];
  implementationSteps: readonly ImplementationStep[];
  outcomes: readonly CaseStudyOutcome[];
  roles: readonly LocalizedText[];
  factMetrics: readonly FactMetric[];
  flow: {
    title: LocalizedText;
    nodes: readonly FlowNode[];
    links: readonly FlowLink[];
  };
  phases: readonly CaseStudyPhase[];
  visualizationSuggestions: readonly VisualizationSuggestion[];
  imagePrompts: readonly CaseStudyImagePrompt[];
  evidenceBoundary: LocalizedText;
};

const defineCaseStudy = <const Id extends FactoryTransformationCaseStudyId>(
  caseStudy: FactoryTransformationCaseStudy<Id>,
) => caseStudy;

const t = (zh: string, en: string): LocalizedText => ({ zh, en });

export const factoryTransformationCaseStudies = [
  defineCaseStudy({
    id: "planning",
    index: "01",
    slug: "pull-based-rolling-production-scheduling",
    href: "/case-studies/pull-based-rolling-production-scheduling",
    title: t(
      "基于拉动式生产的滚动排产体系重构",
      "Rebuilding a Pull-Based Rolling Production Scheduling System",
    ),
    subtitle: t(
      "从临时下单与被动换型，转向订单驱动、上下工序联动的生产节奏",
      "From reactive dispatching and changeovers to an order-led, cross-process production rhythm",
    ),
    summary: t(
      "以客户订单和滚动预测为需求起点，建立成品计划、前道拉动、生产通知单自动化、受控插单和现场反馈闭环，使计划从当天救火转变为可维护的一周至一个月滚动视图。",
      "An order-led operating system that connects rolling demand, finished-goods planning, upstream pull signals, automated production notices, controlled expedites, and shop-floor feedback. It moved planning away from same-day firefighting toward a maintainable one-week to one-month view.",
    ),
    background: [
      t(
        "菲律宾工厂原先主要依据船运信息、合同评审和临时生产通知单安排生产，各工序只能在当前型号接近结束时确认下一任务。",
        "The Philippine plant originally scheduled work from shipping information, contract reviews, and ad hoc production notices. Each process often learned its next assignment only as the current model was nearing completion.",
      ),
      t(
        "订单、通知单和现场库存信息彼此分散，前道依赖眼前库存决定生产内容，插单和交期变化也无法同步传递到所有相关工序。",
        "Order data, production notices, and shop-floor inventory signals were fragmented. Upstream teams relied on visible stock to decide what to run, while expedites and due-date changes did not propagate consistently across operations.",
      ),
      t(
        "项目目标不是再做一张排产表，而是建立由客户需求向前道逐级拉动、同时允许现场反馈修正的生产运行机制。",
        "The goal was not another scheduling spreadsheet, but an operating mechanism that pulled demand upstream from customer requirements and allowed shop-floor evidence to refine the plan.",
      ),
    ],
    challenges: [
      {
        id: "planning-visibility",
        title: t("计划可见性不足", "Insufficient planning visibility"),
        detail: t(
          "各工序只能看到当前任务，无法查看未来一周或一个月的需求。",
          "Operations could see the current job but not the demand expected over the next week or month.",
        ),
      },
      {
        id: "planning-desynchronization",
        title: t("前后工序不同步", "Disconnected upstream and downstream plans"),
        detail: t(
          "前道依赖现场库存判断生产型号，无法根据后道切换顺序提前准备。",
          "Upstream operations chose models from visible stock rather than preparing against the downstream sequence.",
        ),
      },
      {
        id: "planning-changeovers",
        title: t("带料与频繁换型", "Carryover WIP and frequent changeovers"),
        detail: t(
          "型号切换缺少统一规划，当前批次结束后容易残留无法立即进入下一工序的在制品。",
          "Uncoordinated model changes left excess work-in-process that could not immediately enter the next operation and increased adjustment frequency.",
        ),
      },
      {
        id: "planning-expedites",
        title: t("插单缺少影响评估", "Expedites without impact assessment"),
        detail: t(
          "临时需求主要依靠口头通知，容易造成重复生产、漏排和优先级冲突。",
          "Urgent demand was often communicated verbally, creating risks of duplicate production, omitted work, and priority conflicts.",
        ),
      },
    ],
    methods: [
      {
        id: "planning-demand-policy",
        title: t("订单为主、预测为辅", "Orders first, forecasts as a controlled supplement"),
        detail: t(
          "已确认订单按交期和数量排产；高概率但未正式确认的需求仅在未来三个月产能中预留适当空间。",
          "Confirmed orders were scheduled by quantity and due date. High-probability demand without a firm order received controlled capacity allowances within the next three months.",
        ),
      },
      {
        id: "planning-backward-pull",
        title: t("由后向前逐级拉动", "Backward pull across operations"),
        detail: t(
          "从成品计划反推后道、毛坯和前磨需求，使准备动作与真实交付需求相连。",
          "Finished-goods plans were translated backward into downstream, blank, and pre-grinding requirements so preparation followed actual delivery demand.",
        ),
      },
      {
        id: "planning-controlled-expedite",
        title: t("受控插单评审", "Controlled expedite review"),
        detail: t(
          "按交期、库存、在制品、产线状态、物料工装和换型影响寻找最合适的插入窗口。",
          "Expedites were evaluated against due dates, inventory, WIP, line status, material and tooling readiness, and changeover impact before a production window was selected.",
        ),
      },
      {
        id: "planning-feedback",
        title: t("计划与现场双向反馈", "Two-way planning and shop-floor feedback"),
        detail: t(
          "现场可基于设备适配、换型难度和稳定性提出调整，但必须同时验证交期和其他订单影响。",
          "The shop floor could recommend sequencing changes based on equipment fit, changeover difficulty, and stability, provided delivery and cross-order impacts were reviewed.",
        ),
      },
    ],
    implementationSteps: [
      {
        id: "planning-step-orders",
        sequence: 1,
        title: t("统一滚动订单数据库", "Consolidate the rolling order base"),
        detail: t(
          "汇总确认订单、未来三个月滚动需求、小批量需求、交期、成品库存和未完任务。",
          "Consolidate confirmed orders, the next three months of rolling demand, small-lot requirements, due dates, finished-goods inventory, and open production tasks.",
        ),
        actions: [
          t("统一合同评审、船运和业务沟通中的需求信息。", "Unify demand signals from contract review, shipping, and commercial communication."),
          t("区分确认订单与预测性产能预留。", "Separate firm orders from forecast-based capacity reservations."),
        ],
      },
      {
        id: "planning-step-master-plan",
        sequence: 2,
        title: t("建立成品生产计划总表", "Build the finished-goods master plan"),
        detail: t(
          "维护型号、数量、产线和完成时间，并通过型号与产线关系自动分配任务。",
          "Maintain model, quantity, line, and completion requirements, with assignments driven by the model-to-line compatibility map.",
        ),
        actions: [
          t("按时间顺序呈现每条线的当前与后续任务。", "Show current and upcoming work for each line in time order."),
          t("标识插单、调整、订单关系和前道准备量。", "Expose expedites, changes, order links, and upstream preparation quantities."),
        ],
      },
      {
        id: "planning-step-notices",
        sequence: 3,
        title: t("联动生产通知单", "Connect the production-notice workflow"),
        detail: t(
          "从计划中读取型号、数量、工艺和产线信息，自动生成标准化通知单并回写状态。",
          "Read model, quantity, process, and line data from the plan to generate standardized production notices and write status back to the planning entry point.",
        ),
        actions: [
          t("减少重复录入、复制和逐线分发。", "Reduce duplicate entry, copying, and line-by-line distribution."),
          t("保留人工审核作为发布关口。", "Retain human review as the release gate."),
        ],
      },
      {
        id: "planning-step-upstream",
        sequence: 4,
        title: t("把成品计划转换为前道需求", "Translate the plan into upstream requirements"),
        detail: t(
          "结合后道数量、计划时间和现有WIP，计算毛坯与前磨的准备数量和时间。",
          "Use downstream quantities, planned timing, and available WIP to calculate when and how much blanks and pre-grinding operations should prepare.",
        ),
        actions: [
          t("让前道看到未来一周至一个月需求。", "Give upstream operations visibility into the next week to month of demand."),
          t("以需求窗口替代现场库存驱动的临时生产。", "Replace stock-driven improvisation with demand-window preparation."),
        ],
      },
      {
        id: "planning-step-expedite",
        sequence: 5,
        title: t("建立插单与调整机制", "Establish expedite and replanning controls"),
        detail: t(
          "评估紧急度、库存、产能、物料工装、换型时间及对其他订单的影响。",
          "Evaluate urgency, inventory, capacity, material and tooling readiness, changeover time, and consequences for other orders.",
        ),
        actions: [
          t("优先利用同型号或相近工艺的连续生产窗口。", "Prefer a continuous window for the same model or a similar process."),
          t("同步更新计划、通知单、前道需求和受影响订单时间。", "Synchronize the plan, notices, upstream demand, and affected order dates."),
        ],
      },
      {
        id: "planning-step-feedback",
        sequence: 6,
        title: t("闭合现场反馈", "Close the shop-floor feedback loop"),
        detail: t(
          "结合生产进度、设备适配、稳定性、换型难度和准备状态复核现场建议。",
          "Review shop-floor recommendations against progress, equipment fit, stability, changeover difficulty, and readiness.",
        ),
        actions: [
          t("允许有证据的顺序调整。", "Allow evidence-backed sequencing changes."),
          t("避免计划脱离现场或现场随意改序。", "Prevent both detached planning and arbitrary local resequencing."),
        ],
      },
    ],
    outcomes: [
      {
        id: "planning-outcome-notice-time",
        statement: t(
          "生产通知单准备时间由约20至40分钟缩短至1分钟以内。",
          "Production-notice preparation fell from approximately 20–40 minutes to under one minute.",
        ),
        evidenceKind: "quantitative",
        metricId: "planning-notice-time",
      },
      {
        id: "planning-outcome-carryover",
        statement: t(
          "工序间带料相较改善前下降约80%。",
          "Inter-process carryover WIP declined by approximately 80% versus the pre-improvement condition.",
        ),
        evidenceKind: "quantitative",
        metricId: "planning-carryover",
      },
      {
        id: "planning-outcome-visibility",
        statement: t(
          "管理人员能够查看未来一周至一个月的生产任务。",
          "Managers gained visibility into production work for the coming week to month.",
        ),
        evidenceKind: "qualitative",
        qualification: t("原始说明未提供计划达成率等附加数值。", "The source narrative does not provide an additional schedule-adherence figure."),
      },
      {
        id: "planning-outcome-control",
        statement: t(
          "无计划生产、过量生产、频繁换型和口头插单得到更系统的控制。",
          "Unplanned production, overproduction, frequent changeovers, and verbal expedites became more systematically controlled.",
        ),
        evidenceKind: "qualitative",
      },
      {
        id: "planning-outcome-stability",
        statement: t(
          "前后工序信息透明度和机床运行稳定性得到改善。",
          "Cross-process visibility and machine operating stability improved.",
        ),
        evidenceKind: "qualitative",
      },
    ],
    roles: [
      t("订单数据整理与统一", "Order-data consolidation"),
      t("排产与拉动逻辑设计", "Scheduling and pull-logic design"),
      t("生产计划总表与通知单自动化", "Master-plan and production-notice automation"),
      t("型号与产线关系维护", "Model-to-line compatibility maintenance"),
      t("前后工序需求联动", "Upstream and downstream demand coordination"),
      t("插单规则、现场反馈与跨部门协调", "Expedite rules, shop-floor feedback, and cross-functional coordination"),
    ],
    factMetrics: [
      {
        id: "planning-notice-time",
        value: t("20–40分钟 → <1分钟", "20–40 min → <1 min"),
        label: t("生产通知单准备时间", "Production-notice preparation"),
        context: t("通过计划与通知单自动生成联动实现。", "Achieved by linking the plan to standardized notice generation."),
        evidenceKind: "quantitative",
        qualifier: "approximate",
      },
      {
        id: "planning-carryover",
        value: t("约下降80%", "Approximately 80% lower"),
        label: t("工序间带料", "Inter-process carryover WIP"),
        context: t("与改善前状态相比。", "Compared with the pre-improvement condition."),
        evidenceKind: "quantitative",
        qualifier: "approximate",
      },
      {
        id: "planning-visibility-window",
        value: t("1周–1个月", "1 week–1 month"),
        label: t("生产任务可见窗口", "Production visibility window"),
        context: t("前道与管理人员可查看的后续需求范围。", "The forward demand window made visible to upstream operations and management."),
        evidenceKind: "structural",
        qualifier: "stated-operating-parameter",
      },
      {
        id: "planning-forecast-horizon",
        value: t("未来3个月", "Next 3 months"),
        label: t("滚动订单与预测视野", "Rolling order and forecast horizon"),
        context: t("用于订单汇总与高概率需求的有限产能预留。", "Used for order consolidation and controlled capacity reservations for high-probability demand."),
        evidenceKind: "structural",
        qualifier: "stated-operating-parameter",
      },
    ],
    flow: {
      title: t("订单拉动与反馈闭环", "Order-pull and feedback loop"),
      nodes: [
        { id: "demand", kind: "input", label: t("客户订单与需求预测", "Customer orders and demand forecast"), detail: t("以确认订单为主，预测仅用于有限预留。", "Firm orders lead; forecasts support limited reservations.") },
        { id: "finished-plan", kind: "process", label: t("成品滚动计划", "Finished-goods rolling plan"), detail: t("按交期、数量、产线和状态维护。", "Maintained by due date, quantity, line, and status.") },
        { id: "notice", kind: "control", label: t("标准化生产通知单", "Standardized production notice"), detail: t("自动生成并保留人工发布关口。", "Generated automatically with a human release gate.") },
        { id: "upstream-pull", kind: "process", label: t("前道需求与准备", "Upstream demand and preparation"), detail: t("结合计划时间和可用WIP反推。", "Calculated backward from timing and available WIP.") },
        { id: "execution", kind: "output", label: t("产线执行", "Line execution"), detail: t("按统一顺序生产并反馈状态。", "Run to the common sequence and report status.") },
        { id: "expedite", kind: "decision", label: t("插单影响评审", "Expedite impact review"), detail: t("判断交期、库存、产能和换型影响。", "Assess delivery, inventory, capacity, and changeover impact.") },
        { id: "feedback", kind: "feedback", label: t("现场反馈与重排", "Shop-floor feedback and replanning"), detail: t("用设备与执行证据修正计划。", "Use equipment and execution evidence to refine the plan.") },
      ],
      links: [
        { from: "demand", to: "finished-plan" },
        { from: "finished-plan", to: "notice" },
        { from: "finished-plan", to: "upstream-pull" },
        { from: "notice", to: "execution" },
        { from: "upstream-pull", to: "execution" },
        { from: "expedite", to: "finished-plan", label: t("受控调整", "Controlled adjustment") },
        { from: "execution", to: "feedback" },
        { from: "feedback", to: "finished-plan" },
      ],
    },
    phases: [
      { id: "planning-phase-demand", sequence: 1, label: t("需求统一", "Demand consolidation"), timeBasis: "rolling-horizon", timeframe: t("未来三个月滚动视野", "Next-three-month rolling horizon"), detail: t("统一确认订单、预测、库存和未完任务。", "Unify firm orders, forecasts, inventory, and open work.") },
      { id: "planning-phase-plan", sequence: 2, label: t("计划与通知单联动", "Plan and notice integration"), timeBasis: "sequence-only", timeframe: t("实施阶段；原始说明未给日历日期", "Implementation stage; no calendar dates stated"), detail: t("建立产线分配、通知单生成与状态回写。", "Establish line assignment, notice generation, and status write-back.") },
      { id: "planning-phase-pull", sequence: 3, label: t("前道拉动", "Upstream pull"), timeBasis: "rolling-horizon", timeframe: t("一周至一个月需求窗口", "One-week to one-month demand window"), detail: t("将后道计划转换为前道准备量与时间。", "Convert downstream plans into upstream quantities and timing.") },
      { id: "planning-phase-control", sequence: 4, label: t("持续调整与反馈", "Continuous adjustment and feedback"), timeBasis: "event-driven", timeframe: t("插单、异常或现场建议触发", "Triggered by expedites, exceptions, or shop-floor evidence"), detail: t("评审影响并同步更新相关计划。", "Review impacts and synchronize affected plans.") },
    ],
    visualizationSuggestions: [
      { id: "planning-viz-pull", kind: "flow", title: t("订单向前道拉动图", "Order-to-upstream pull map"), purpose: t("展示需求如何从成品计划逐级转化为前道准备。", "Show how demand moves backward from the finished-goods plan into upstream preparation."), dataFields: [t("订单与预测", "Orders and forecast"), t("成品计划", "Finished-goods plan"), t("前道需求", "Upstream demand"), t("现场反馈", "Shop-floor feedback")], evidenceBoundary: t("使用脱敏型号与合成数量，不展示真实订单。", "Use sanitized models and synthetic quantities; do not expose real orders.") },
      { id: "planning-viz-before-after", kind: "before-after", title: t("临时排产与滚动排产对比", "Reactive versus rolling scheduling"), purpose: t("对比信息可见性、通知单制作、换型和插单机制。", "Compare visibility, notice preparation, changeover planning, and expedite control."), dataFields: [t("计划视野", "Planning horizon"), t("通知单时间", "Notice time"), t("换型逻辑", "Changeover logic"), t("插单规则", "Expedite rule")], evidenceBoundary: t("仅两个结果数字可作为量化标注。", "Only the two documented result figures may be shown as quantitative callouts.") },
      { id: "planning-viz-expedite", kind: "decision-tree", title: t("插单决策树", "Expedite decision tree"), purpose: t("解释同型号续产、最近换型窗口和立即切换之间的判断。", "Explain the choice among same-model continuation, the next changeover window, and an immediate switch."), dataFields: [t("紧急度", "Urgency"), t("库存与WIP", "Inventory and WIP"), t("物料工装", "Material and tooling"), t("订单影响", "Order impact")], evidenceBoundary: t("规则来自项目说明，不显示客户名称或真实订单优先级。", "Rules come from the project narrative; omit customer names and live order priorities.") },
    ],
    imagePrompts: [
      { id: "planning-hero", use: "hero", aspectRatio: "16:9", prompt: t("明亮整洁的现代轴承工厂中央控制视角，前景为一块克制的滚动排产控制台，远处多条磨削产线沿黄色通道延伸，屏幕仅显示脱敏甘特条和拉动信号，工业摄影，真实金属与玻璃材质，自然顶光，电影级但不夸张，无品牌。", "A bright, immaculate modern bearing factory seen from a central operations viewpoint. A restrained rolling-schedule console sits in the foreground while several grinding lines recede along clear yellow aisles. Screens show only sanitized Gantt bars and pull signals. Photoreal industrial cinematography, accurate metal and glass materials, soft natural roof light, cinematic but restrained, no brands."), negativePrompt: t("不要科幻HUD、悬浮文字、密集机械臂、穿模轨道、可读订单、品牌标识或夸张橙蓝色调。", "No sci-fi HUD, floating text, crowded robot arms, intersecting rails, readable orders, brand marks, or exaggerated orange-and-teal grading."), alt: t("滚动排产控制台与整洁生产线", "Rolling-schedule control station overlooking clean production lines") },
      { id: "planning-transition", use: "transition", aspectRatio: "16:9", prompt: t("从客户订单数据线自然推入工厂成品计划，再沿生产线向前道物料准备区延伸的电影化转场，所有信息为抽象图形和脱敏符号，视觉引导线清晰，黑色与琥珀色控制室风格。", "A cinematic transition that moves from abstract customer-order signals into a finished-goods plan, then follows a clean production line toward upstream material preparation. All information is represented by sanitized graphics and symbols, with one clear visual path in a black-and-amber control-room aesthetic."), negativePrompt: t("不要真实公司数据、密集图标、文字乱码、霓虹赛博朋克或不合理设备。", "No real company data, icon clutter, garbled text, neon cyberpunk styling, or mechanically implausible equipment."), alt: t("订单信号向前道生产逐级拉动", "Order signals pulling production upstream") },
    ],
    evidenceBoundary: t(
      "公开页面只使用脱敏流程、合成订单和概括性结果；不展示客户、真实排产、设备参数或内部生产通知单。",
      "The public page must use sanitized workflows, synthetic orders, and summarized outcomes only. Do not expose customers, live schedules, machine parameters, or internal production notices.",
    ),
  }),
  defineCaseStudy({
    id: "wip",
    index: "02",
    slug: "wip-data-governance-inventory-integrity",
    href: "/case-studies/wip-data-governance-inventory-integrity",
    title: t(
      "海外工厂WIP数据治理与“账卡物一致”盘存体系建设",
      "WIP Data Governance and Account-Label-Material Inventory Integrity",
    ),
    subtitle: t(
      "用最小有效记录、订单联动看板和独立复核，把分散在制品转化为可信运营数据",
      "Turning fragmented work-in-process into trusted operating data through minimum viable capture, order-linked visibility, and independent verification",
    ),
    summary: t(
      "项目先建立可用的WIP基础账，再用短代码映射降低一线记录负担，并把订单联动看板与初盘、复盘、抽盘及财务随机复核结合，形成适合当地执行条件的账、卡、物一致闭环。",
      "The project first established a usable WIP ledger, then reduced frontline recording effort through short-code mapping. An order-linked dashboard was combined with first count, independent recount, spot check, and finance sampling to create a locally executable account-label-material integrity loop.",
    ),
    background: [
      t("WIP分散在毛坯、前磨、后磨、待检、生产线和临时存放区。", "WIP was spread across blank stock, pre-grinding, post-grinding, inspection, production lines, and temporary storage."),
      t("现场记录、手工台账、电子表格和口头信息互不连接，管理人员难以判断订单对应位置、数量、缺口和账实差异。", "Shop-floor notes, manual ledgers, spreadsheets, and verbal updates were disconnected, making it difficult to determine each order's location, quantity, shortage, and physical-versus-recorded variance."),
      t("信息可信度不足促使现场保留较高缓冲库存，进一步带来积压、资金占用、盘存差异和管理负担。", "Low confidence in the data encouraged higher buffers, which in turn increased WIP accumulation, working-capital exposure, count variances, and management effort."),
    ],
    challenges: [
      { id: "wip-no-ledger", title: t("从无账起步", "Starting without a continuous ledger"), detail: t("部分在制品缺少连续流转记录，只能依靠现场清点和询问判断状态。", "Some WIP had no continuous movement record, so its status could only be reconstructed through physical counts and interviews.") },
      { id: "wip-capture-triangle", title: t("现场数据采集不可能三角", "The shop-floor data-capture trade-off"), detail: t("记录字段越多，完整性可能提高，但员工意愿和现场效率会下降。", "More fields could improve completeness while reducing operator participation and execution efficiency.") },
      { id: "wip-integrity", title: t("账、卡、物脱节", "Account, label, and material divergence"), detail: t("台账、现场标识和箱内实物任一不一致，报表就无法支持可靠决策。", "If the ledger, physical label, or actual contents diverged, the resulting report could not support reliable decisions.") },
      { id: "wip-count-governance", title: t("盘存责任与复核不清", "Unclear count ownership and verification"), detail: t("原流程容易出现重复盘点、区域遗漏和同一人复核自己结果。", "The former process allowed duplicate counting, missed areas, and self-verification of initial results.") },
    ],
    methods: [
      { id: "wip-staged-maturity", title: t("分阶段提升数据成熟度", "Stage data maturity deliberately"), detail: t("先解决有没有账，再补充过程追踪与校验，不在基础薄弱时追求虚假的接近100%。", "First establish whether a usable record exists, then add traceability and validation instead of claiming near-perfect accuracy before the operating foundation is ready.") },
      { id: "wip-minimum-data", title: t("最小有效记录单位", "Minimum viable record"), detail: t("以唯一批次和短代码为核心，只让员工记录代码、数量和必要动作。", "Use a unique batch and short code as the core identifier, requiring operators to capture only the code, quantity, and necessary movement."), },
      { id: "wip-cross-validation", title: t("数字映射与交叉校验", "Digital mapping and cross-validation"), detail: t("由短代码自动带出批次、物料、型号、订单和工序，并检查不一致。", "Resolve a short code into batch, material, model, order, and process data, then check for mismatches."), },
      { id: "wip-independent-count", title: t("独立多层复核", "Independent layered verification"), detail: t("通过初盘、独立复盘、菲方组长抽盘和财务随机复核降低系统性误差。", "Reduce systematic error through first count, independent recount, local team-lead sampling, and finance-led random checks."), },
    ],
    implementationSteps: [
      { id: "wip-step-ledger", sequence: 1, title: t("建立基础WIP台账", "Establish the baseline WIP ledger"), detail: t("记录主要型号、批次、数量、所在工序和流转方向。", "Record key models, batches, quantities, current operations, and movement direction."), actions: [t("先覆盖主要在制品。", "Cover the main WIP population first."), t("用数据识别积压、待料和投入产出不匹配。", "Use the ledger to expose accumulation, shortages, and input-output mismatches.")] },
      { id: "wip-step-codes", sequence: 2, title: t("设计短代码映射", "Design short-code mapping"), detail: t("将复杂批次映射为类似A0001的现场代码，后台保留完整关联。", "Map complex batches to shop-floor codes such as A0001 while retaining the full relationship in the system."), actions: [t("减少长编码抄写。", "Reduce transcription of long identifiers."), t("自动带出型号、订单和工序。", "Resolve model, order, and process automatically.")] },
      { id: "wip-step-pilot", sequence: 3, title: t("试点一箱一码并止损", "Pilot one-code-per-container and stop when economics fail"), detail: t("在前磨完成Beta试运行，发现维护成本高于当时收益后停止全面部署。", "Run a beta in pre-grinding, then stop full deployment when the maintenance burden exceeded the benefit under current conditions."), actions: [t("保留唯一识别与映射思路。", "Retain the unique-identification and mapping concepts."), t("改用更适合现场成熟度的简化方案。", "Adopt a simpler method suited to current operating maturity.")] },
      { id: "wip-step-dashboard", sequence: 4, title: t("建立订单联动WIP看板", "Build the order-linked WIP board"), detail: t("集中订单需求、成品库存、各工序WIP、缺口、异常积压和计划实际进度。", "Combine order demand, finished inventory, process-level WIP, shortages, abnormal accumulation, and plan-versus-actual progress."), actions: [t("支持按订单或型号查看。", "Enable views by order or model."), t("将分散查询收敛到统一入口。", "Consolidate fragmented lookups into one entry point.")] },
      { id: "wip-step-freeze", sequence: 5, title: t("规划停机与盘存甘特", "Plan the shutdown and count sequence"), detail: t("明确停产、整理、保养清洁、初盘、复盘、抽盘、差异处理和财务确认节点。", "Define production stop, organization, maintenance and cleaning, first count, recount, spot check, variance handling, and finance confirmation."), actions: [t("冻结物料流动。", "Freeze material movement."), t("利用停机窗口同步完成保养和清洁。", "Use the shutdown window for maintenance and cleaning.")] },
      { id: "wip-step-verification", sequence: 6, title: t("实施三级盘存与财务抽查", "Run three-stage counting and finance sampling"), detail: t("确保初盘与复盘人员独立，由菲方组长抽盘、项目负责人监盘、财务随机复核。", "Keep first-count and recount personnel independent, add local team-lead sampling, project supervision, and finance-led random verification."), actions: [t("差异触发扩大复核。", "Expand verification when a variance is found."), t("由菲方组长自主安排现场人员。", "Let local team leads assign shop-floor personnel within defined rules.")] },
    ],
    outcomes: [
      { id: "wip-outcome-accuracy", statement: t("本次盘存准确率相较此前提升约20%。", "Inventory-count accuracy improved by approximately 20% compared with the prior condition."), evidenceKind: "quantitative", metricId: "wip-accuracy" },
      { id: "wip-outcome-traceability", statement: t("分散WIP逐步形成统一、可追踪并与订单关联的数据入口。", "Fragmented WIP was brought into a unified, traceable, order-linked view."), evidenceKind: "qualitative" },
      { id: "wip-outcome-workload", statement: t("短代码和自动映射降低了长编码人工录入负担与错误风险。", "Short codes and automatic mapping reduced long-code entry effort and transcription risk."), evidenceKind: "qualitative" },
      { id: "wip-outcome-local", statement: t("菲方组长能够自主安排并执行盘存，其他中方人员不再参与大规模现场清点。", "Local team leads were able to organize and execute the count, without other Chinese staff participating in the large-scale physical count."), evidenceKind: "qualitative" },
      { id: "wip-outcome-buffer", statement: t("数据时效性和可信度改善后，现场具备逐步降低信息不透明型缓冲库存的基础。", "Better timeliness and confidence created the basis for gradually reducing buffers held mainly because of information uncertainty."), evidenceKind: "qualitative", qualification: t("原始说明未提供库存金额或库存天数下降值。", "The source narrative does not provide a reduction in inventory value or days on hand.") },
    ],
    roles: [
      t("WIP治理路径与最小记录逻辑设计", "WIP governance roadmap and minimum-record design"),
      t("短代码映射工具与订单联动看板设计", "Short-code mapping tool and order-linked dashboard design"),
      t("一箱一码Beta试点评估与停止决策", "One-code-per-container beta evaluation and stop decision"),
      t("盘存甘特、区域规则与独立复核机制设计", "Count Gantt, area rules, and independent-verification design"),
      t("英文培训、监盘与跨区域异常处理", "English-language training, count supervision, and cross-area exception handling"),
    ],
    factMetrics: [
      { id: "wip-accuracy", value: t("约+20%", "Approximately +20%"), label: t("盘存准确率改善", "Inventory-count accuracy improvement"), context: t("相较此前盘存结果。", "Compared with the prior count result."), evidenceKind: "quantitative", qualifier: "approximate" },
      { id: "wip-review-layers", value: t("3级 + 财务随机复核", "3 stages + finance sampling"), label: t("现场与独立验证结构", "Operational and independent verification structure"), context: t("初盘、独立复盘、菲方组长抽盘之后由财务随机复核。", "First count, independent recount, and local team-lead spot check followed by finance-led random verification."), evidenceKind: "structural", qualifier: "stated-operating-parameter" },
      { id: "wip-workstreams", value: t("2条主线", "2 linked workstreams"), label: t("项目结构", "Program structure"), context: t("WIP记录与订单看板；账卡物一致盘存机制。", "WIP recording and order-linked visibility; account-label-material inventory control."), evidenceKind: "structural", qualifier: "stated-operating-parameter" },
    ],
    flow: {
      title: t("WIP记录到独立盘存验证", "WIP capture to independent inventory verification"),
      nodes: [
        { id: "movement", kind: "input", label: t("领料与工序流转", "Issue and process movement"), detail: t("记录批次、数量和必要动作。", "Capture batch, quantity, and essential movement.") },
        { id: "short-code", kind: "process", label: t("短代码输入", "Short-code entry"), detail: t("以最小输入识别唯一批次。", "Identify the unique batch with minimal input.") },
        { id: "mapping", kind: "control", label: t("数字映射与校验", "Digital mapping and validation"), detail: t("关联物料、型号、订单和工序。", "Resolve material, model, order, and process.") },
        { id: "wip-board", kind: "output", label: t("订单联动WIP看板", "Order-linked WIP board"), detail: t("展示数量、位置、缺口和异常。", "Expose quantity, location, shortages, and anomalies.") },
        { id: "freeze", kind: "control", label: t("停机冻结", "Movement freeze"), detail: t("在稳定状态下开展盘存。", "Count under a stable material state.") },
        { id: "count", kind: "process", label: t("初盘 → 复盘 → 抽盘", "First count → recount → spot check"), detail: t("人员独立、区域清晰。", "Independent personnel and explicit area ownership.") },
        { id: "finance", kind: "control", label: t("财务随机复核", "Finance random verification"), detail: t("差异触发追加检查。", "Variances trigger expanded checks.") },
        { id: "correction", kind: "feedback", label: t("差异关闭与账目修正", "Variance closure and record correction"), detail: t("将验证结果反馈到治理体系。", "Feed verified results back into the governance system.") },
      ],
      links: [
        { from: "movement", to: "short-code" },
        { from: "short-code", to: "mapping" },
        { from: "mapping", to: "wip-board" },
        { from: "wip-board", to: "freeze" },
        { from: "freeze", to: "count" },
        { from: "count", to: "finance" },
        { from: "finance", to: "correction" },
        { from: "correction", to: "mapping" },
      ],
    },
    phases: [
      { id: "wip-phase-ledger", sequence: 1, label: t("从无账到基本有账", "From no ledger to a usable ledger"), timeBasis: "sequence-only", timeframe: t("第一阶段；无日历日期", "Stage 1; no calendar dates stated"), detail: t("优先记录主要型号、批次、数量、工序和流向。", "Prioritize key models, batches, quantities, operations, and flows.") },
      { id: "wip-phase-traceability", sequence: 2, label: t("从有账到过程可追踪", "From a ledger to process traceability"), timeBasis: "sequence-only", timeframe: t("第二阶段；无日历日期", "Stage 2; no calendar dates stated"), detail: t("补充关键流转动作并用最小记录降低负担。", "Add key movements while minimizing capture effort.") },
      { id: "wip-phase-pilot", sequence: 3, label: t("一箱一码Beta试点", "One-code-per-container beta"), timeBasis: "sequence-only", timeframe: t("Beta试运行后停止全面推广", "Beta completed; full rollout stopped"), detail: t("验证价值后保留编码思想，放弃不经济的执行粒度。", "Retain the useful identification logic while rejecting an uneconomic execution granularity.") },
      { id: "wip-phase-control", sequence: 4, label: t("盘存闭环运行", "Inventory-control loop"), timeBasis: "recurring-control", timeframe: t("每次计划盘存周期", "Each planned inventory-count cycle"), detail: t("停机、三级盘存、财务复核和差异关闭。", "Movement freeze, three-stage count, finance verification, and variance closure.") },
    ],
    visualizationSuggestions: [
      { id: "wip-viz-integrity", kind: "network", title: t("账—卡—物一致性三角", "Account-label-material integrity triangle"), purpose: t("显示台账、现场标识和实物之间的双向校验关系。", "Show the bidirectional checks among system records, physical labels, and actual material."), dataFields: [t("账面型号与数量", "Recorded model and quantity"), t("卡片批次与状态", "Label batch and status"), t("实物数量与位置", "Physical quantity and location")], evidenceBoundary: t("展示合成批次和数量。", "Use synthetic batches and quantities.") },
      { id: "wip-viz-gantt", kind: "gantt", title: t("盘存停机甘特图", "Inventory shutdown Gantt"), purpose: t("呈现冻结、整理、保养、初盘、复盘、抽盘和财务确认的依赖。", "Show dependencies across freeze, organization, maintenance, first count, recount, spot check, and finance confirmation."), dataFields: [t("区域", "Area"), t("任务节点", "Task"), t("责任角色", "Owner role"), t("完成状态", "Status")], evidenceBoundary: t("不编造实际日期和工厂班次，仅展示相对顺序。", "Do not invent dates or plant shifts; show relative sequencing only.") },
      { id: "wip-viz-maturity", kind: "timeline", title: t("WIP数据成熟度路径", "WIP data-maturity path"), purpose: t("解释为什么先建立可用账目，再逐步提升追踪粒度。", "Explain why a usable ledger came before finer-grained traceability."), dataFields: [t("无账", "No ledger"), t("基本有账", "Usable ledger"), t("过程追踪", "Process traceability"), t("独立验证", "Independent verification")], evidenceBoundary: t("70%–80%只可作为阶段性容忍范围的叙述，不作为最终绩效。", "The 70%–80% figure may only describe an accepted early-stage range, not a final performance result.") },
    ],
    imagePrompts: [
      { id: "wip-hero", use: "hero", aspectRatio: "16:9", prompt: t("现代轴承工厂的在制品超市区，低矮金属周转箱整齐平放，清晰但不可读的批次标签，远处可见前磨与后磨区域，中央仅一条视觉引导线连接实物箱、标签和脱敏WIP控制屏，真实自然顶光，克制的黑灰、钢色和少量琥珀标识。", "A modern bearing-plant WIP supermarket with low metal totes arranged neatly and bearing clear but unreadable batch labels. Pre-grinding and post-grinding areas are visible in the distance. One strong visual path connects a physical tote, its label, and a sanitized WIP control screen. Photoreal natural roof light, restrained black, graphite, steel, and small amber safety accents."), negativePrompt: t("不要悬浮全息屏、可读客户信息、立放轴承套圈、堆积杂物、科幻仓库或不合比例叉车。", "No floating holograms, readable customer information, bearing rings standing upright, clutter piles, sci-fi warehouse styling, or incorrectly scaled forklifts."), alt: t("账卡物一致的WIP管理区域", "WIP area linking system records, labels, and physical material") },
      { id: "wip-section", use: "section", aspectRatio: "4:3", prompt: t("盘存复核场景特写：一只周转箱、一张脱敏物料卡和一台显示核对状态的工业平板，三者构成清晰三角构图，背景为整洁生产线，真实工业摄影，不出现人员面部。", "Close-up of an inventory verification scene: one material tote, one sanitized material card, and one industrial tablet showing a verification state, arranged in a clear triangular composition. Clean production line in the background, photoreal industrial photography, no identifiable faces."), negativePrompt: t("不要可读真实编号、夸张HUD、错误数量文字、脏乱环境。", "No readable real identifiers, exaggerated HUD, malformed quantity text, or untidy environment."), alt: t("实物、标签与数字台账的盘存核对", "Inventory verification across material, label, and digital record") },
    ],
    evidenceBoundary: t("使用脱敏批次、合成数量和角色名称；不得公开真实库存、订单、人员姓名或Google Sheets内容。", "Use sanitized batches, synthetic quantities, and role labels. Do not publish live inventory, orders, employee names, or actual Google Sheets content."),
  }),
  defineCaseStudy({
    id: "procurement",
    index: "03",
    slug: "bom-driven-procurement-risk-warning",
    href: "/case-studies/bom-driven-procurement-risk-warning",
    title: t("基于BOM自动展开与供应风险预警的采购计划体系建设", "BOM-Driven Procurement Planning and Supply-Risk Early Warning"),
    subtitle: t("把订单、库存、WIP、供应周期和外部物流风险转化为可解释的采购动作", "Turning orders, inventory, WIP, lead times, and external logistics risk into explainable procurement actions"),
    summary: t("在滚动排产和WIP治理基础上，将客户订单自动展开为多级物料需求，抵扣可用库存、WIP和已下未到数量，加入差异化损耗余量并反推最晚下单时间，再通过联网风险检索把港口、船期和清关事件转化为采购与排产建议。", "Building on rolling scheduling and WIP governance, the system expands customer orders into multi-level material demand, nets usable inventory, WIP, and open purchase orders, applies differentiated loss allowances, and back-schedules the latest order date. Connected risk research then translates port, sailing, and customs events into procurement and production responses."),
    background: [
      t("临时生产通知和不完整WIP数据使采购缺少稳定需求来源，物料往往在现场接近短缺时才开始核查和加急。", "Ad hoc production notices and incomplete WIP data left procurement without a stable demand signal, so materials were often investigated and expedited only when a shortage was imminent."),
      t("滚动排产回答未来生产什么，WIP看板回答现场已有多少，为订单驱动的BOM需求拆解创造了前提。", "Rolling scheduling answered what would be produced; the WIP board clarified what was already available. Together they enabled order-driven BOM demand planning."),
      t("海外供应还必须同时考虑供应商生产、国内运输、海运、港口等待、清关、收货检验和风险缓冲。", "Overseas supply also required consideration of supplier production, domestic transport, ocean freight, port waiting, customs clearance, receiving inspection, and risk buffers."),
    ],
    challenges: [
      { id: "procurement-demand", title: t("需求来源不稳定", "Unstable demand source"), detail: t("采购难以判断未来产品、数量、到货日期和订单优先级。", "Procurement lacked a reliable view of future products, quantities, required dates, and order priorities.") },
      { id: "procurement-netting", title: t("账面数量不等于可用数量", "Recorded quantity is not necessarily usable supply"), detail: t("待检、冻结、返工、已占用库存和不同完工时间的WIP不能简单抵扣。", "Inspection-pending, frozen, rework, allocated inventory, and WIP with incompatible completion timing could not be netted indiscriminately.") },
      { id: "procurement-allowance", title: t("统一余量造成两种风险", "A uniform allowance creates two opposing risks"), detail: t("余量过低会待料，统一高余量又会积压，需要按物料历史和供应特征区分。", "Too little allowance creates shortages; a uniformly high allowance creates excess. The setting had to vary by material history and supply characteristics.") },
      { id: "procurement-external-risk", title: t("外部物流风险与生产脱节", "External logistics risk disconnected from production"), detail: t("船期、港口和清关信息只有与库存覆盖和生产需求日期结合后才具有行动价值。", "Sailing, port, and customs information becomes actionable only when connected to inventory coverage and production need dates.") },
    ],
    methods: [
      { id: "procurement-demand-chain", title: t("端到端需求转换", "End-to-end demand conversion"), detail: t("订单先扣成品库存，再按BOM展开并汇总共用与专用物料。", "Net finished-goods inventory from orders first, then explode the BOM and aggregate common while preserving dedicated materials.") },
      { id: "procurement-net-requirement", title: t("状态与时间感知的净需求", "Status- and time-aware net requirements"), detail: t("理论需求加损耗和安全余量，再扣除真正可用的库存、WIP和已下未到数量。", "Add loss and required safety allowances to theoretical demand, then subtract only genuinely usable inventory, WIP, and open inbound orders.") },
      { id: "procurement-back-schedule", title: t("从需求日反向排采购", "Back-schedule procurement from the need date"), detail: t("从要求到货时间依次扣除供应、运输、海运、清关、检验和风险缓冲周期。", "Work backward from the required arrival date through supplier, inland transport, ocean freight, customs, inspection, and risk-buffer lead times.") },
      { id: "procurement-ai-risk", title: t("人机协同风险预警", "Human-governed risk intelligence"), detail: t("DeepSeek API与联网检索负责汇总外部信号，采购人员保留最终判断。", "A DeepSeek API and connected search summarize external signals while procurement retains the final decision."), },
    ],
    implementationSteps: [
      { id: "procurement-step-order", sequence: 1, title: t("订单转成品净生产需求", "Convert orders into net finished-goods demand"), detail: t("读取型号、数量、交期、成品库存、未完计划和优先级。", "Read model, quantity, due date, finished inventory, open production plans, and priority."), actions: [t("先扣除可直接交付的成品。", "Deduct finished goods available for direct shipment."), t("避免按订单总量重复安排生产。", "Avoid duplicating production against gross order quantity.")] },
      { id: "procurement-step-bom", sequence: 2, title: t("自动展开BOM", "Explode the BOM automatically"), detail: t("按单位用量计算内外圈、钢球、保持架、密封件、润滑脂、包装和辅料需求。", "Calculate requirements for inner and outer rings, balls, cages, seals, grease, packaging, and other materials from unit usage."), actions: [t("合并不同型号的共用物料。", "Aggregate shared materials across models."), t("保留专用物料与对应型号关系。", "Preserve model links for dedicated materials.")] },
      { id: "procurement-step-netting", sequence: 3, title: t("计算净需求", "Calculate net requirements"), detail: t("区分可用、待检、冻结、占用和按时间可达的WIP及在途采购。", "Distinguish usable, inspection-pending, frozen, allocated, and time-feasible WIP and inbound purchases."), actions: [t("加入历史废品与损耗余量。", "Apply historical scrap and loss allowances."), t("按通用性、周期和稳定性设置差异化安全余量。", "Differentiate safety allowances by commonality, lead time, and supply stability.")] },
      { id: "procurement-step-timing", sequence: 4, title: t("反推请购与下单日期", "Back-calculate requisition and order dates"), detail: t("将完整生产与跨境供应周期纳入最晚下单日期。", "Include the full production and cross-border supply lead time in the latest-order-date calculation."), actions: [t("同时避免过晚待料和过早积压。", "Avoid both late shortages and premature inventory."), t("保留风险缓冲。", "Retain an explicit risk buffer.")] },
      { id: "procurement-step-execution", sequence: 5, title: t("建立请购到到货闭环", "Close the requisition-to-receipt loop"), detail: t("生成采购建议，经确认形成请购和采购订单，并跟踪供应商、船运、清关、收货、发票与付款状态。", "Generate a recommendation, convert approved demand into requisitions and purchase orders, and track supplier, sailing, customs, receipt, invoice, and payment states."), actions: [t("保留需求来源和对应订单。", "Preserve demand source and order linkage."), t("记录预计与实际关键日期。", "Record planned and actual milestone dates.")] },
      { id: "procurement-step-risk", sequence: 6, title: t("接入外部风险并分级响应", "Connect external risk and tier the response"), detail: t("将港口、天气、船期和政策信号与库存覆盖及生产日期比对。", "Compare port, weather, sailing, and policy signals with inventory coverage and production dates."), actions: [t("按低、中、高风险选择跟踪、催交、排产调整或替代方案。", "Choose monitoring, expediting, resequencing, or alternatives according to low, medium, or high risk."), t("供应变化反向修正生产计划。", "Feed supply changes back into the production plan.")] },
    ],
    outcomes: [
      { id: "procurement-outcome-conversion", statement: t("订单能够自动转换为成品和各级物料需求。", "Orders could be converted automatically into finished-goods and multi-level material requirements."), evidenceKind: "qualitative" },
      { id: "procurement-outcome-transparency", statement: t("库存、WIP、已下未到、损耗和供应周期进入同一套可解释的净需求逻辑。", "Inventory, WIP, open inbound orders, losses, and lead times entered one explainable net-requirements logic."), evidenceKind: "qualitative" },
      { id: "procurement-outcome-planning", statement: t("采购从临时救火逐步转向可预测、可分析和可计划。", "Procurement shifted from reactive firefighting toward a more predictable, analyzable, and plan-driven mode."), evidenceKind: "qualitative" },
      { id: "procurement-outcome-risk", statement: t("外部物流信息能够转化为采购、清关和排产应对建议。", "External logistics signals could be translated into procurement, customs, and production-planning responses."), evidenceKind: "qualitative" },
      { id: "procurement-outcome-inventory", statement: t("临时采购、过早采购、原材料与WIP积压风险得到更系统的控制。", "Emergency buying, premature purchasing, and raw-material and WIP accumulation risks became more systematically controlled."), evidenceKind: "qualitative", qualification: t("原始说明未提供采购成本、库存金额或缺料次数的量化降幅。", "The source narrative does not quantify reductions in procurement cost, inventory value, or shortage events.") },
    ],
    roles: [
      t("制造运营平台BOM自动拆解模块开发", "Development of the manufacturing-platform BOM explosion module"),
      t("净需求、损耗余量与安全余量逻辑设计", "Net-requirement, loss-allowance, and safety-buffer logic design"),
      t("采购提前期反排与请购流程设计", "Procurement back-scheduling and requisition workflow design"),
      t("订单、库存、WIP与在途采购数据联动", "Integration of orders, inventory, WIP, and open inbound purchasing"),
      t("联网检索、风险分级与生产反馈机制设计", "Connected research, risk-tiering, and production-feedback design"),
    ],
    factMetrics: [
      { id: "procurement-risk-levels", value: t("3级", "3 levels"), label: t("供应风险分级", "Supply-risk tiers"), context: t("低风险、中风险和高风险分别对应不同响应。", "Low, medium, and high risk each trigger a different response."), evidenceKind: "structural", qualifier: "stated-operating-parameter" },
      { id: "procurement-loop", value: t("订单 → 到货", "Order → receipt"), label: t("端到端需求闭环", "End-to-end demand loop"), context: t("覆盖BOM展开、净需求、请购、采购、物流和收货。", "Covers BOM explosion, netting, requisition, purchasing, logistics, and receipt."), evidenceKind: "structural", qualifier: "stated-operating-parameter" },
    ],
    flow: {
      title: t("订单到采购与风险反馈闭环", "Order-to-procurement and risk-feedback loop"),
      nodes: [
        { id: "order", kind: "input", label: t("客户订单", "Customer order"), detail: t("型号、数量、交期和优先级。", "Model, quantity, due date, and priority.") },
        { id: "fg-demand", kind: "process", label: t("成品净需求", "Net finished-goods demand"), detail: t("扣除可直接交付成品。", "Net available finished goods.") },
        { id: "bom", kind: "process", label: t("BOM自动展开", "Automatic BOM explosion"), detail: t("计算并汇总各级物料。", "Calculate and aggregate material levels.") },
        { id: "netting", kind: "control", label: t("库存、WIP与在途抵扣", "Inventory, WIP, and inbound netting"), detail: t("只抵扣状态与时间可用数量。", "Net only supply that is usable by status and timing.") },
        { id: "allowance", kind: "control", label: t("差异化损耗与余量", "Differentiated losses and buffers"), detail: t("基于历史和供应特征。", "Based on history and supply characteristics.") },
        { id: "back-schedule", kind: "process", label: t("反推下单日期", "Back-scheduled order date"), detail: t("扣除完整跨境提前期。", "Subtract the full cross-border lead time.") },
        { id: "purchase", kind: "output", label: t("请购与采购执行", "Requisition and purchasing"), detail: t("审批、下单与里程碑跟踪。", "Approval, ordering, and milestone tracking.") },
        { id: "external-risk", kind: "input", label: t("外部物流风险", "External logistics risk"), detail: t("船期、港口、天气和清关。", "Sailings, ports, weather, and customs.") },
        { id: "risk-response", kind: "decision", label: t("风险分级响应", "Tiered risk response"), detail: t("跟踪、催交、调整或替代。", "Monitor, expedite, resequence, or substitute.") },
        { id: "planning-feedback", kind: "feedback", label: t("反馈生产计划", "Production-plan feedback"), detail: t("供应变化修正优先级和顺序。", "Supply changes revise priority and sequence.") },
      ],
      links: [
        { from: "order", to: "fg-demand" },
        { from: "fg-demand", to: "bom" },
        { from: "bom", to: "netting" },
        { from: "netting", to: "allowance" },
        { from: "allowance", to: "back-schedule" },
        { from: "back-schedule", to: "purchase" },
        { from: "external-risk", to: "risk-response" },
        { from: "purchase", to: "risk-response" },
        { from: "risk-response", to: "planning-feedback" },
        { from: "planning-feedback", to: "fg-demand" },
      ],
    },
    phases: [
      { id: "procurement-phase-demand", sequence: 1, label: t("需求形成", "Demand formation"), timeBasis: "rolling-horizon", timeframe: t("随滚动订单更新", "Updated with the rolling order horizon"), detail: t("将订单转为成品和物料需求。", "Convert orders into finished-goods and material demand.") },
      { id: "procurement-phase-net", sequence: 2, label: t("净需求与时间计算", "Netting and timing"), timeBasis: "event-driven", timeframe: t("订单、库存、WIP或供应状态变化时重算", "Recalculated when order, inventory, WIP, or supply status changes"), detail: t("更新可用量、损耗余量和最晚下单日。", "Update usable supply, allowances, and the latest order date.") },
      { id: "procurement-phase-execution", sequence: 3, label: t("采购执行", "Procurement execution"), timeBasis: "sequence-only", timeframe: t("请购至实际到货", "From requisition to physical receipt"), detail: t("追踪审批、供应商、物流、清关和收货里程碑。", "Track approval, supplier, logistics, customs, and receipt milestones.") },
      { id: "procurement-phase-risk", sequence: 4, label: t("风险轮询与反馈", "Risk monitoring and feedback"), timeBasis: "recurring-control", timeframe: t("持续联网检索与订单状态比对", "Recurring connected research and order-status comparison"), detail: t("按生产影响升级风险并修正排产。", "Escalate by production impact and revise scheduling.") },
    ],
    visualizationSuggestions: [
      { id: "procurement-viz-flow", kind: "flow", title: t("订单到采购需求瀑布", "Order-to-procurement demand waterfall"), purpose: t("解释毛需求、可用量抵扣、余量和净采购需求的关系。", "Explain gross demand, usable-supply netting, allowances, and net purchasing demand."), dataFields: [t("理论需求", "Theoretical demand"), t("损耗与安全余量", "Loss and safety allowances"), t("可用库存与WIP", "Usable inventory and WIP"), t("已下未到", "Open inbound supply"), t("净需求", "Net requirement")], evidenceBoundary: t("用合成BOM和数量，避免暗示真实采购规模。", "Use a synthetic BOM and quantities; do not imply the plant's actual purchase volume.") },
      { id: "procurement-viz-timeline", kind: "timeline", title: t("跨境采购反排时间轴", "Cross-border procurement back-schedule"), purpose: t("从生产需要日反向展示收货、清关、海运、国内运输和供应商生产。", "Work backward from the production need date through receipt, customs, ocean freight, inland transport, and supplier production."), dataFields: [t("需要日期", "Need date"), t("检验与入库", "Inspection and receipt"), t("清关", "Customs"), t("海运", "Ocean freight"), t("供应商周期", "Supplier lead time")], evidenceBoundary: t("原始说明没有实际天数，图表只能显示阶段和相对顺序。", "The source gives no actual durations, so the chart may show stages and relative order only.") },
      { id: "procurement-viz-risk", kind: "risk-map", title: t("供应风险响应矩阵", "Supply-risk response matrix"), purpose: t("按生产影响和应对空间区分低、中、高风险。", "Separate low, medium, and high risk by production impact and response room."), dataFields: [t("库存覆盖", "Inventory coverage"), t("需求日期", "Need date"), t("物流状态", "Logistics status"), t("响应动作", "Response action")], evidenceBoundary: t("风险示例必须使用虚构港口事件和脱敏物料。", "Risk examples must use fictional port events and sanitized materials.") },
    ],
    imagePrompts: [
      { id: "procurement-hero", use: "hero", aspectRatio: "16:9", prompt: t("现代制造运营控制室与真实工厂物流背景，主视觉是一条清晰的物料需求链：脱敏订单、轴承BOM爆炸图、库存容器、海运集装箱和到货节点依次连接，信息层克制、可读但无真实文本，工业写实，冷灰钢色搭配少量琥珀风险信号。", "A modern manufacturing operations room with a real factory logistics backdrop. One clear material-demand chain connects a sanitized order, an exploded bearing BOM, inventory containers, an ocean container, and a receipt milestone. Restrained information layers, legible structure without real text, photoreal industrial style, cool steel and graphite with sparse amber risk signals."), negativePrompt: t("不要世界地图陈词滥调、霓虹网络、可读采购订单、悬浮零件穿模、品牌Logo或密集仪表盘。", "No clichéd world map, neon network, readable purchase orders, intersecting floating parts, brand logos, or dashboard clutter."), alt: t("从订单与BOM到跨境到货的采购链路", "Procurement chain from order and BOM to cross-border receipt") },
      { id: "procurement-section", use: "section", aspectRatio: "4:3", prompt: t("轴承总成的专业爆炸视图，内圈、外圈、钢球、保持架、密封件和包装材料按正确比例水平展开，旁边是简洁的库存抵扣与风险分级图形，深色工业展陈，真实材质，无文字。", "A professional exploded view of a bearing assembly with correctly scaled inner ring, outer ring, balls, cage, seals, and packaging material arranged horizontally. A restrained inventory-netting and risk-tier graphic sits beside it. Dark industrial presentation, physically accurate materials, no text."), negativePrompt: t("不要错误轴承结构、缺失滚动体、悬空阴影、卡通渲染或伪文字。", "No incorrect bearing structure, missing rolling elements, floating shadows, cartoon rendering, or pseudo-text."), alt: t("轴承BOM展开与净需求计算概念", "Bearing BOM explosion and net-requirement concept") },
    ],
    evidenceBoundary: t("公开案例必须使用合成BOM、库存、供应商和物流事件；不公开真实物料编码、采购订单、价格、供应商名称或API密钥。", "The public case must use synthetic BOMs, inventory, suppliers, and logistics events. Do not expose real material codes, purchase orders, prices, supplier identities, or API keys."),
  }),
  defineCaseStudy({
    id: "resilience",
    index: "04",
    slug: "overseas-supply-chain-resilience",
    href: "/case-studies/overseas-supply-chain-resilience",
    title: t("海外制造基地供应链韧性与供应商管理优化", "Overseas Manufacturing Supply-Chain Resilience and Supplier Management"),
    subtitle: t("把技术选型、质量、包装、物流和响应能力纳入同一套风险驱动的供应商体系", "Bringing technical selection, quality, packaging, logistics, and response capability into one risk-driven supplier system"),
    summary: t("针对海外基地补货周期长、质量补救慢和海运防护要求高的特点，项目把砂轮全生命周期成本、套圈供应节点、热处理反馈、包装防锈、供应商绩效和智能风险轮询连接起来，使供应商管理围绕生产连续性而非单价和承诺交期运行。", "To address long replenishment cycles, slow quality recovery, and demanding ocean-freight protection, the project connected grinding-wheel lifecycle cost, ring-supply milestones, heat-treatment feedback, packaging and corrosion prevention, supplier performance, and intelligent risk monitoring. Supplier management was reframed around production continuity rather than quoted price and promised delivery alone."),
    background: [
      t("海外基地的关键物料需跨越国内生产、集货、报关、海运、菲律宾清关和本地运输，任一节点延期都可能放大为生产风险。", "Critical materials for an overseas plant pass through domestic production, consolidation, export clearance, ocean freight, Philippine customs, and local transport. Delay at any node can amplify into a production risk."),
      t("到货后发现尺寸、热处理、锈蚀、包装或批次问题时，补货往往需要再次经历完整跨境周期。", "When dimensional, heat-treatment, corrosion, packaging, or batch issues are found after arrival, replacement often requires another full cross-border cycle."),
      t("安全库存必须覆盖真实风险，但盲目增加又会带来资金、空间、锈蚀、呆滞和盘存负担。", "Safety stock must cover real risk, but indiscriminate buffering creates working-capital, space, corrosion, obsolescence, and inventory-control costs."),
    ],
    challenges: [
      { id: "resilience-lead-time", title: t("长链路放大微小偏差", "Long supply chains amplify small deviations"), detail: t("加工、检验、包装、海运或清关任一延误都可能影响生产连续性。", "A delay in processing, inspection, packaging, ocean freight, or customs can threaten production continuity.") },
      { id: "resilience-quality", title: t("质量问题补救周期长", "Quality recovery takes longer offshore"), detail: t("后端磨削才暴露的热处理或尺寸问题会同时增加报废、调整、砂轮消耗和补货风险。", "Heat-treatment or dimensional issues discovered during grinding can increase scrap, adjustments, wheel consumption, and replenishment risk simultaneously.") },
      { id: "resilience-packaging", title: t("包装是质量保证的一部分", "Packaging is part of quality assurance"), detail: t("潮湿、冷凝、多次装卸和长期存放要求防锈、密封、抗压、追溯和先进先出同时成立。", "Humidity, condensation, repeated handling, and long storage require corrosion protection, sealing, compression strength, traceability, and FIFO support together.") },
      { id: "resilience-price", title: t("单价无法代表总成本", "Unit price does not represent total cost"), detail: t("砂轮寿命、修整、节拍、稳定性、废品和停机共同决定单位合格件综合成本。", "Wheel life, dressing, cycle time, stability, scrap, and downtime jointly determine total cost per conforming part.") },
    ],
    methods: [
      { id: "resilience-lifecycle", title: t("单位合格件全生命周期成本", "Lifecycle cost per conforming part"), detail: t("用节拍模拟比较砂轮价格、磨削、修整、换轮、寿命、质量和停机，而非只看单价或硬度。", "Use takt simulation to compare wheel price, grinding, dressing, changeover, life, quality, and downtime rather than unit price or hardness alone."), },
      { id: "resilience-node-control", title: t("供应节点化管理", "Milestone-based supply control"), detail: t("把锻造、车加工、热处理、检验、防锈、物流、清关和入库拆成计划与实际节点。", "Break forging, turning, heat treatment, inspection, corrosion protection, logistics, customs, and receipt into planned and actual milestones."), },
      { id: "resilience-feedback-quality", title: t("后道表现反馈供应商", "Feed downstream performance back to suppliers"), detail: t("将来料检验、磨削表现和最终质量反向关联到供应商与批次。", "Link incoming inspection, grinding performance, and final quality back to supplier and batch."), },
      { id: "resilience-risk-ranking", title: t("按生产影响分配管理精力", "Prioritize management effort by production impact"), detail: t("结合订单状态、库存覆盖、历史OTD、包装异常和在途节点决定催货与替代优先级。", "Use order status, inventory coverage, historical OTD, packaging anomalies, and in-transit milestones to prioritize expediting and alternatives."), },
    ],
    implementationSteps: [
      { id: "resilience-step-wheel", sequence: 1, title: t("建立砂轮技术与成本模型", "Build the grinding-wheel technical and cost model"), detail: t("比较采购价、磨削时间、成型、修整、换轮、寿命、质量和非计划停机。", "Compare purchase price, grinding time, profiling, dressing, wheel changes, life, quality, and unplanned downtime."), actions: [t("用节拍模拟验证供应商方案。", "Validate supplier options through takt simulation."), t("以单位合格件综合成本和稳定性决策。", "Decide on total cost per conforming part and stability.")] },
      { id: "resilience-step-milestones", sequence: 2, title: t("拆解套圈供应节点", "Map ring-supply milestones"), detail: t("从采购订单到锻造、车加工、热处理、包装、海运、清关、检验和入库逐点跟踪。", "Track milestones from purchase order through forging, turning, heat treatment, packaging, ocean freight, customs, inspection, and receipt."), actions: [t("对比计划与实际日期。", "Compare planned and actual dates."), t("定位延期发生环节。", "Locate the stage where delay occurs.")] },
      { id: "resilience-step-quality", sequence: 3, title: t("关联热处理与磨削表现", "Connect heat treatment to grinding performance"), detail: t("将硬度、变形、余量和稳定性问题与供应商批次关联。", "Relate hardness, distortion, stock allowance, and stability issues to supplier batches."), actions: [t("结合来料检验和生产反馈。", "Combine incoming inspection with production feedback."), t("纳入供应商质量评价。", "Include the result in supplier quality evaluation.")] },
      { id: "resilience-step-packaging", sequence: 4, title: t("验证包装与防锈方案", "Validate packaging and corrosion protection"), detail: t("评估防锈油、VCI、防潮、干燥剂、密封、外箱、固定和标签。", "Evaluate corrosion inhibitor, VCI, moisture barriers, desiccant, sealing, outer packaging, restraint, and labeling."), actions: [t("以实际到货状态验证方案。", "Validate the design against actual receipt condition."), t("将锈蚀和包装异常计入绩效。", "Include corrosion and packaging anomalies in performance.")] },
      { id: "resilience-step-scorecard", sequence: 5, title: t("统一供应商绩效数据", "Unify supplier-performance data"), detail: t("集中ERP、收货、检验、集团物流、集团采购、承诺和现场使用反馈。", "Combine ERP, receipts, inspection, group logistics, group procurement, commitments, and shop-floor use feedback."), actions: [t("计算OTD、到货、数量、质量、包装和响应指标。", "Calculate OTD, receipt, quantity, quality, packaging, and response indicators."), t("形成综合评级与分级。", "Create an integrated rating and tier.")] },
      { id: "resilience-step-agent", sequence: 6, title: t("运行智能体风险轮询", "Run agent-assisted risk monitoring"), detail: t("每日汇总订单、在途、港口清关、收货、质量、包装和库存覆盖信号。", "Summarize orders, in-transit status, ports and customs, receipts, quality, packaging, and inventory coverage each day."), actions: [t("识别真正影响生产的订单。", "Identify orders that genuinely threaten production."), t("支持催交、替代、订单分配和抽检决策。", "Support expediting, alternatives, order allocation, and inspection decisions.")] },
    ],
    outcomes: [
      { id: "resilience-outcome-cost", statement: t("砂轮评价从采购单价扩展为单位合格件综合成本和生产稳定性。", "Grinding-wheel evaluation expanded from purchase price to lifecycle cost per conforming part and production stability."), evidenceKind: "qualitative" },
      { id: "resilience-outcome-trace", statement: t("毛坯加工、热处理、包装和物流过程形成可追踪节点。", "Blank processing, heat treatment, packaging, and logistics were converted into traceable milestones."), evidenceKind: "qualitative" },
      { id: "resilience-outcome-quality", statement: t("热处理和包装结果能够反馈到供应商绩效与后续决策。", "Heat-treatment and packaging outcomes could feed supplier performance and subsequent decisions."), evidenceKind: "qualitative" },
      { id: "resilience-outcome-priority", statement: t("催货与供应商管理从平均分配精力转向围绕生产影响和风险排序。", "Expediting and supplier management shifted from evenly distributed effort to prioritization by production impact and risk."), evidenceKind: "qualitative" },
      { id: "resilience-outcome-risk", statement: t("海外供应链从被动催货逐步转向可预测、风险驱动的管理方式。", "The overseas supply chain moved from reactive expediting toward a more predictable, risk-driven management model."), evidenceKind: "qualitative", qualification: t("原始说明没有提供节省金额、OTD提升或缺料下降的具体数字。", "The source narrative does not provide specific savings, OTD improvement, or shortage-reduction figures.") },
    ],
    roles: [
      t("砂轮节拍模拟与全生命周期成本分析", "Grinding-wheel takt simulation and lifecycle cost analysis"),
      t("毛坯、热处理、包装与物流节点设计", "Blank, heat-treatment, packaging, and logistics milestone design"),
      t("供应商评价维度与评级机制设计", "Supplier evaluation dimensions and rating-system design"),
      t("ERP、收货、质量、物流和采购数据整合", "Integration of ERP, receipt, quality, logistics, and procurement data"),
      t("智能体风险轮询与催货优先级逻辑", "Agent-assisted risk monitoring and expedite-priority logic"),
    ],
    factMetrics: [
      { id: "resilience-dimensions", value: t("7个维度", "7 dimensions"), label: t("供应商综合评价", "Integrated supplier evaluation"), context: t("质量、成本、交付、包装与防护、技术能力、服务响应、供应风险。", "Quality, cost, delivery, packaging and protection, technical capability, service response, and supply risk."), evidenceKind: "structural", qualifier: "stated-operating-parameter" },
      { id: "resilience-monitoring", value: t("每日", "Daily"), label: t("智能体风险轮询", "Agent-assisted risk monitoring"), context: t("汇总采购、物流、质量、包装和生产缺口信号。", "Aggregates procurement, logistics, quality, packaging, and production-shortage signals."), evidenceKind: "structural", qualifier: "stated-operating-parameter" },
    ],
    flow: {
      title: t("海外供应商风险闭环", "Overseas supplier-risk loop"),
      nodes: [
        { id: "selection", kind: "input", label: t("技术与成本选型", "Technical and cost selection"), detail: t("以生命周期表现筛选方案。", "Select against lifecycle performance.") },
        { id: "po", kind: "process", label: t("采购与供应节点", "Purchase and supply milestones"), detail: t("加工、热处理、检验与包装。", "Processing, heat treatment, inspection, and packaging.") },
        { id: "logistics", kind: "process", label: t("跨境物流", "Cross-border logistics"), detail: t("集货、报关、海运、清关和本地运输。", "Consolidation, export, ocean freight, customs, and local transport.") },
        { id: "receipt", kind: "control", label: t("收货与来料检验", "Receipt and incoming inspection"), detail: t("验证数量、质量、锈蚀和包装。", "Verify quantity, quality, corrosion, and packaging.") },
        { id: "production", kind: "feedback", label: t("生产使用反馈", "Production-use feedback"), detail: t("关联磨削、质量和稳定性表现。", "Connect grinding, quality, and stability performance.") },
        { id: "scorecard", kind: "control", label: t("供应商绩效评级", "Supplier performance rating"), detail: t("综合七个评价维度。", "Combine seven evaluation dimensions.") },
        { id: "risk", kind: "decision", label: t("生产影响风险判断", "Production-impact risk decision"), detail: t("结合库存覆盖与在途状态。", "Combine inventory coverage with in-transit status.") },
        { id: "action", kind: "output", label: t("订单、催货与替代决策", "Allocation, expediting, and alternative decisions"), detail: t("把风险转化为可执行动作。", "Turn risk into executable action.") },
      ],
      links: [
        { from: "selection", to: "po" },
        { from: "po", to: "logistics" },
        { from: "logistics", to: "receipt" },
        { from: "receipt", to: "production" },
        { from: "production", to: "scorecard" },
        { from: "scorecard", to: "risk" },
        { from: "risk", to: "action" },
        { from: "action", to: "selection" },
      ],
    },
    phases: [
      { id: "resilience-phase-selection", sequence: 1, label: t("技术选型", "Technical selection"), timeBasis: "sequence-only", timeframe: t("批量采购前", "Before volume purchasing"), detail: t("用节拍与成本模型验证关键耗材。", "Validate critical consumables with takt and cost models.") },
      { id: "resilience-phase-supply", sequence: 2, label: t("供应过程控制", "Supply-process control"), timeBasis: "sequence-only", timeframe: t("采购订单至工厂入库", "From purchase order to plant receipt"), detail: t("跟踪加工、包装、物流和检验节点。", "Track processing, packaging, logistics, and inspection milestones.") },
      { id: "resilience-phase-feedback", sequence: 3, label: t("质量与生产反馈", "Quality and production feedback"), timeBasis: "event-driven", timeframe: t("来料异常或生产表现触发", "Triggered by incoming anomalies or production performance"), detail: t("将后道结果归因到供应商与批次。", "Attribute downstream results to supplier and batch.") },
      { id: "resilience-phase-monitor", sequence: 4, label: t("持续风险管理", "Continuous risk management"), timeBasis: "daily", timeframe: t("每日轮询", "Daily monitoring"), detail: t("按生产影响更新评级、催货和替代优先级。", "Update ratings, expediting, and alternative priorities by production impact.") },
    ],
    visualizationSuggestions: [
      { id: "resilience-viz-cost", kind: "before-after", title: t("单价与单位合格件总成本", "Unit price versus lifecycle cost per conforming part"), purpose: t("解释为什么寿命更长或单价更低并不必然更优。", "Explain why longer life or lower unit price is not necessarily the better option."), dataFields: [t("采购价", "Purchase price"), t("磨削节拍", "Grinding cycle"), t("修整与换轮", "Dressing and changeover"), t("质量与停机", "Quality and downtime")], evidenceBoundary: t("不展示真实供应商报价；使用归一化合成指数。", "Do not show supplier quotes; use normalized synthetic indices.") },
      { id: "resilience-viz-network", kind: "network", title: t("套圈跨境供应节点图", "Cross-border ring-supply milestone map"), purpose: t("显示加工、热处理、包装、海运、清关和入库的责任与反馈。", "Show responsibility and feedback across processing, heat treatment, packaging, ocean freight, customs, and receipt."), dataFields: [t("计划日期", "Planned date"), t("实际日期", "Actual date"), t("质量状态", "Quality state"), t("包装状态", "Packaging state")], evidenceBoundary: t("隐藏真实国家内供应商位置、名称和批次。", "Hide actual supplier locations, identities, and batches.") },
      { id: "resilience-viz-matrix", kind: "matrix", title: t("供应商七维评分矩阵", "Seven-dimension supplier matrix"), purpose: t("对比质量、成本、交付、包装、技术、服务和风险。", "Compare quality, cost, delivery, packaging, technical capability, service, and risk."), dataFields: [t("七个评价维度", "Seven evaluation dimensions"), t("供应商等级", "Supplier tier"), t("行动建议", "Recommended action")], evidenceBoundary: t("使用Supplier A/B/C和合成评分，不公布实际供应商绩效。", "Use Supplier A/B/C and synthetic scores; do not publish actual supplier performance.") },
    ],
    imagePrompts: [
      { id: "resilience-hero", use: "hero", aspectRatio: "16:9", prompt: t("高质量轴承套圈供应链场景，前景为经过防锈油和VCI内衬保护的水平放置套圈与正确标签，中景为检验台和密封周转箱，远景通过厂房装卸口自然连接集装箱物流，一条清晰视觉线贯穿加工、包装、运输和收货，真实工业摄影，潮湿环境防护细节准确。", "A premium bearing-ring supply-chain scene. In the foreground, rings lie flat with realistic corrosion inhibitor, VCI lining, and a clear but unreadable label. A quality bench and sealed returnable containers occupy the middle ground, while a loading bay naturally connects to container logistics in the distance. One strong visual line links processing, packaging, transport, and receipt. Photoreal industrial cinematography with accurate moisture-protection details."), negativePrompt: t("不要套圈竖立漂浮、错误包装、锈迹美化、全球地图HUD、港口与车间穿模或可读供应商信息。", "No upright floating rings, incorrect packaging, glamorized corrosion, world-map HUD, intersecting port and factory geometry, or readable supplier information."), alt: t("从防锈包装到海外工厂收货的套圈供应链", "Bearing-ring supply chain from corrosion-protected packaging to overseas receipt") },
      { id: "resilience-section", use: "section", aspectRatio: "4:3", prompt: t("工业检验台上的砂轮与轴承套圈样件，旁边以实体卡片表现节拍、修整、质量和寿命四类评估，不使用发光屏幕，真实CBN磨料颗粒、钢件磨削纹理和专业量具，克制电影光。", "A grinding wheel and bearing-ring samples on an industrial inspection bench. Physical cards represent cycle time, dressing, quality, and life without glowing screens. Realistic CBN abrasive grain, ground-steel texture, and professional gauges under restrained cinematic light."), negativePrompt: t("不要砂轮与套圈比例错误、虚构品牌、赛博灯光、文字乱码或不合理接触姿态。", "No incorrect wheel-to-ring scale, fictional branding, cyber lighting, garbled text, or implausible contact geometry."), alt: t("砂轮全生命周期技术与成本评价", "Technical and lifecycle-cost evaluation of grinding wheels") },
    ],
    evidenceBoundary: t("所有公开供应商、价格、批次、OTD和质量数据必须为脱敏或合成数据；不显示真实合同、物流单据和供应商位置。", "All public supplier, price, batch, OTD, and quality data must be sanitized or synthetic. Do not show real contracts, logistics documents, or supplier locations."),
  }),
  defineCaseStudy({
    id: "skills",
    index: "05",
    slug: "frontline-skills-standard-work",
    href: "/case-studies/frontline-skills-standard-work",
    title: t("海外工厂一线技能培养与现场标准化管理体系建设", "Frontline Skills Development and Standard Work for an Overseas Plant"),
    subtitle: t("把静态培训计划转化为每日任务、技能验证、异常补训和现场标准的执行闭环", "Turning static training plans into daily assignments, verified capability, exception recovery, and standard-work execution"),
    summary: t("项目通过新学员培训打点小程序，将HR计划转换为白班和夜班的每日任务，明确HR、团队长、师傅和员工责任，并把技能验证、补训、技能矩阵、3分钟汇报、5S、设备保养和EHS连接成日常执行体系。", "A trainee check-in application converted HR plans into daily assignments for day and night shifts, clarified responsibilities across HR, team leads, mentors, and trainees, and connected skill verification, retraining, the skills matrix, three-minute reporting, 5S, maintenance, and EHS into one daily execution system."),
    background: [
      t("工厂已有新员工名单、师徒关系、培训项目和周期，但计划主要停留在报表，缺少每日监督与结果验证。", "The plant already had new-hire lists, mentor relationships, training items, and planned cycles, but execution remained largely report-based without daily supervision or outcome verification."),
      t("请假、换班、调线、师傅缺席和逾期任务没有稳定的补救路径，完成记录也不等于员工真正具备独立操作能力。", "Leave, shift changes, line transfers, mentor absence, and overdue tasks lacked a stable recovery path, while a completion record did not prove independent operating capability."),
      t("人员培养需要与班组沟通、5S、文件版本、设备点检和EHS共同落地，才能形成真实现场能力。", "Capability building had to operate together with team communication, 5S, document control, equipment checks, and EHS to become real shop-floor competence."),
    ],
    challenges: [
      { id: "skills-plan-execution", title: t("计划与每日执行脱节", "Training plans disconnected from daily execution"), detail: t("管理人员难以及时确认当天谁学什么、由谁负责、是否完成。", "Managers could not reliably see who should learn what today, who owned the task, or whether it was completed.") },
      { id: "skills-proof", title: t("培训完成不等于能力达标", "Training completion did not prove competence"), detail: t("员工可能有完成记录，但仍无法独立操作、识别异常或正确升级问题。", "An employee could have a completion record yet remain unable to work independently, recognize anomalies, or escalate correctly.") },
      { id: "skills-exceptions", title: t("人员变化打断计划", "People changes disrupted the plan"), detail: t("请假、换班、调线和师傅不在岗容易让任务被遗漏或错误关闭。", "Leave, shift changes, line transfers, and mentor absence could cause tasks to be missed or closed incorrectly.") },
      { id: "skills-dependency", title: t("关键技能依赖少数人员", "Critical skills concentrated in too few people"), detail: t("夜班和特定产线可能缺少能够处理换型、调整和简单异常的人员。", "Night shifts and specific lines could lack people capable of changeovers, adjustments, and basic exception handling.") },
    ],
    methods: [
      { id: "skills-daily-loop", title: t("计划转每日任务", "Convert plans into daily work"), detail: t("按日期、班次、产线、师傅、未完成和逾期状态自动生成培训打点。", "Generate training check-ins from date, shift, line, mentor, incomplete work, and overdue status."), },
      { id: "skills-verified-capability", title: t("以验证代替形式完成", "Verify capability, not attendance"), detail: t("通过现场操作、口头提问或实际任务区分已培训、待验证、未通过和可独立操作。", "Use observed work, questions, or practical tasks to distinguish trained, pending verification, failed, and independently qualified states."), },
      { id: "skills-exception-loop", title: t("异常进入补训闭环", "Route exceptions into recovery"), detail: t("请假、换班、调线、师傅缺席、未通过和逾期都必须重新安排或升级。", "Leave, shift changes, line transfers, mentor absence, failed checks, and overdue work must be rescheduled or escalated."), },
      { id: "skills-operating-system", title: t("技能与现场标准联动", "Connect skills to the operating system"), detail: t("把培训与3分钟汇报、5S、文件版本、保养和三级安全教育结合。", "Connect training with three-minute reporting, 5S, document versioning, maintenance, and three-level safety education."), },
    ],
    implementationSteps: [
      { id: "skills-step-foundation", sequence: 1, title: t("统一员工、岗位与技能基础", "Unify employee, role, and skill foundations"), detail: t("整理人员、班次、产线、岗位、师傅、培训日期、状态、考核和独立资格。", "Organize people, shifts, lines, roles, mentors, dates, status, assessment, and independent qualification."), actions: [t("将岗位能力拆为可执行技能项。", "Break each role into executable skill items."), t("覆盖安全、操作、换型、调整、质量、点检和简单异常。", "Cover safety, operation, changeover, adjustment, quality, checks, and basic exceptions.")] },
      { id: "skills-step-daily", sequence: 2, title: t("自动生成每日培训任务", "Generate daily training tasks"), detail: t("分别为白班和夜班筛选当日、未完成、临期和逾期任务。", "Generate separate day- and night-shift lists for due, incomplete, approaching-deadline, and overdue work."), actions: [t("明确员工、内容、师傅、团队长和计划完成时间。", "Name the employee, topic, mentor, team lead, and planned completion."), t("减少反复查找HR总表。", "Reduce repeated searches through the HR master sheet.")] },
      { id: "skills-step-loop", sequence: 3, title: t("建立发布、执行和验证闭环", "Close the publish-execute-verify loop"), detail: t("HR发布，团队长安排，师傅培训，团队长确认，员工接受技能验证。", "HR publishes, the team lead schedules, the mentor trains, the team lead confirms, and the employee undergoes skill verification."), actions: [t("关键技能必须通过实际验证。", "Critical skills require practical verification."), t("验证未通过不能直接关闭。", "A failed verification cannot be closed as complete.")] },
      { id: "skills-step-exceptions", sequence: 4, title: t("处理培训异常与补训", "Handle training exceptions and retraining"), detail: t("对请假、换班、调线、师傅不在岗、未通过和逾期任务重新安排。", "Reschedule work affected by leave, shift changes, line transfers, absent mentors, failed assessments, or overdue status."), actions: [t("保留仍适用的已完成技能。", "Retain completed skills that remain applicable."), t("记录原因、补训内容、责任人和复核时间。", "Record cause, retraining content, owner, and review timing.")] },
      { id: "skills-step-matrix", sequence: 5, title: t("汇总技能矩阵", "Build the skills matrix"), detail: t("显示已掌握、待完成、指导下操作、独立操作和师傅资格。", "Show mastered, pending, supervised-operation, independent-operation, and mentor-qualified states."), actions: [t("识别产线与班次技能缺口。", "Expose line- and shift-level skill gaps."), t("支持跨岗培养和资源优先级。", "Support cross-training and resource priorities.")] },
      { id: "skills-step-standard-work", sequence: 6, title: t("连接现场标准化执行", "Connect shop-floor standard work"), detail: t("引入3分钟结构化汇报、定置管理、文件版本、保养节奏、PPE、消防和特种作业检查。", "Integrate three-minute structured reporting, location control, document versions, maintenance cadence, PPE, fire safety, and special-work checks."), actions: [t("偏差必须形成责任人和完成时间。", "Deviations require an owner and due time."), t("检查发现异常必须进入后续动作。", "Inspection findings must create follow-up actions.")] },
    ],
    outcomes: [
      { id: "skills-outcome-daily", statement: t("HR培训计划被转换为白班和夜班每天可执行的任务。", "HR training plans were converted into executable daily tasks for day and night shifts."), evidenceKind: "qualitative" },
      { id: "skills-outcome-ownership", statement: t("HR、团队长、师傅和员工的培训责任及异常处理路径更加明确。", "Training ownership and exception paths became clearer across HR, team leads, mentors, and trainees."), evidenceKind: "qualitative" },
      { id: "skills-outcome-visibility", statement: t("技能矩阵提高了员工能力、班次差距和关键岗位风险的可见性。", "The skills matrix improved visibility into employee capability, shift gaps, and critical-role risk."), evidenceKind: "qualitative" },
      { id: "skills-outcome-standard", statement: t("培训、班组沟通、5S、设备保养和EHS形成更一致的现场执行框架。", "Training, team communication, 5S, equipment maintenance, and EHS formed a more consistent execution framework."), evidenceKind: "qualitative" },
      { id: "skills-outcome-independence", statement: t("人员培养从默认随师学习转向计划、任务、记录、验证和补救闭环。", "Capability development shifted from assumed learning-by-shadowing to a loop of plans, tasks, records, verification, and recovery."), evidenceKind: "qualitative", qualification: t("原始说明未提供培训完成率、独立上岗人数或事故率变化等量化结果。", "The source narrative does not quantify completion rate, independently qualified headcount, or safety-rate change.") },
    ],
    roles: [
      t("新学员培训打点小程序设计与开发", "Design and development of the trainee check-in application"),
      t("岗位技能拆解与培训任务规则设计", "Role-skill decomposition and training-task rule design"),
      t("HR、团队长、师傅和员工责任闭环设计", "Ownership-loop design across HR, team leads, mentors, and trainees"),
      t("异常、补训、验证和技能矩阵机制设计", "Exception, retraining, verification, and skills-matrix design"),
      t("3分钟汇报、5S、文件、保养和EHS标准化推动", "Implementation of three-minute reporting, 5S, document control, maintenance, and EHS standards"),
    ],
    factMetrics: [
      { id: "skills-daily-cycle", value: t("每日", "Daily"), label: t("培训任务生成节奏", "Training-task generation cadence"), context: t("按白班和夜班分别生成当日任务。", "Tasks are generated separately for day and night shifts."), evidenceKind: "structural", qualifier: "stated-operating-parameter" },
      { id: "skills-report", value: t("3分钟", "3 minutes"), label: t("结构化班组汇报", "Structured team report"), context: t("围绕上一班结果、当前班计划和需要支持事项。", "Covers the previous shift result, current-shift plan, and support required."), evidenceKind: "structural", qualifier: "stated-operating-parameter" },
      { id: "skills-safety", value: t("3级", "3 levels"), label: t("新员工安全教育", "New-hire safety education"), context: t("公司级、车间级、班组或岗位级。", "Company, workshop, and team or job level."), evidenceKind: "structural", qualifier: "stated-operating-parameter" },
      { id: "skills-maintenance", value: t("5种节奏", "5 cadences"), label: t("设备保养频率", "Equipment-maintenance cadence"), context: t("每班、每日、每周、月度和停机计划保养。", "Per shift, daily, weekly, monthly, and planned-shutdown maintenance."), evidenceKind: "structural", qualifier: "stated-operating-parameter" },
    ],
    flow: {
      title: t("培训计划到验证能力闭环", "Training-plan to verified-capability loop"),
      nodes: [
        { id: "hr-plan", kind: "input", label: t("HR培训计划", "HR training plan"), detail: t("人员、岗位、师傅、技能和日期。", "Employee, role, mentor, skill, and dates.") },
        { id: "daily-task", kind: "process", label: t("每日任务生成", "Daily task generation"), detail: t("按班次、状态和到期情况筛选。", "Filter by shift, status, and due state.") },
        { id: "publish", kind: "control", label: t("HR发布", "HR release"), detail: t("确认当日计划进入现场。", "Release the daily plan to the shop floor.") },
        { id: "execution", kind: "process", label: t("团队长安排与师傅培训", "Team-lead scheduling and mentor delivery"), detail: t("在岗确认后执行培训。", "Execute after confirming attendance.") },
        { id: "verify", kind: "decision", label: t("技能验证", "Skill verification"), detail: t("通过操作、提问或任务判断。", "Assess through observation, questions, or practical work.") },
        { id: "qualified", kind: "output", label: t("独立操作资格", "Independent qualification"), detail: t("更新技能矩阵。", "Update the skills matrix.") },
        { id: "exception", kind: "feedback", label: t("补训与逾期处理", "Retraining and overdue handling"), detail: t("记录原因并重新安排。", "Record the cause and reschedule.") },
        { id: "standard-work", kind: "control", label: t("现场标准化", "Shop-floor standard work"), detail: t("连接5S、保养、文件和EHS。", "Connect 5S, maintenance, documents, and EHS.") },
      ],
      links: [
        { from: "hr-plan", to: "daily-task" },
        { from: "daily-task", to: "publish" },
        { from: "publish", to: "execution" },
        { from: "execution", to: "verify" },
        { from: "verify", to: "qualified", label: t("通过", "Pass") },
        { from: "verify", to: "exception", label: t("未通过或未完成", "Failed or incomplete") },
        { from: "exception", to: "daily-task" },
        { from: "qualified", to: "standard-work" },
      ],
    },
    phases: [
      { id: "skills-phase-foundation", sequence: 1, label: t("能力基础建模", "Capability foundation"), timeBasis: "sequence-only", timeframe: t("实施起点；无日历日期", "Implementation start; no calendar dates stated"), detail: t("统一人员、岗位、技能和培训计划。", "Unify people, roles, skills, and training plans.") },
      { id: "skills-phase-daily", sequence: 2, label: t("每日培训执行", "Daily training execution"), timeBasis: "daily", timeframe: t("白班与夜班每日", "Daily for day and night shifts"), detail: t("生成、发布、安排和确认任务。", "Generate, release, schedule, and confirm tasks.") },
      { id: "skills-phase-verification", sequence: 3, label: t("验证与补训", "Verification and recovery"), timeBasis: "event-driven", timeframe: t("培训完成、未通过或人员变化时触发", "Triggered by completion, failed verification, or people changes"), detail: t("验证能力并将异常送入补训。", "Verify capability and route exceptions into retraining.") },
      { id: "skills-phase-sustain", sequence: 4, label: t("技能矩阵与标准维持", "Skills matrix and standard sustainment"), timeBasis: "recurring-control", timeframe: t("持续更新与周期检查", "Continuous updates and recurring checks"), detail: t("用技能覆盖、5S、保养和EHS维持现场能力。", "Sustain capability through skill coverage, 5S, maintenance, and EHS.") },
    ],
    visualizationSuggestions: [
      { id: "skills-viz-loop", kind: "flow", title: t("每日培训执行闭环", "Daily training execution loop"), purpose: t("展示从HR计划到任务、培训、验证和补训的责任转移。", "Show ownership transfer from HR planning through tasks, training, verification, and recovery."), dataFields: [t("员工与班次", "Employee and shift"), t("培训项目", "Training item"), t("责任角色", "Responsible role"), t("验证状态", "Verification state")], evidenceBoundary: t("使用虚构员工编号和合成任务，不显示真实姓名。", "Use fictional employee IDs and synthetic tasks; do not show real names.") },
      { id: "skills-viz-matrix", kind: "heatmap", title: t("产线与班次技能矩阵", "Line-and-shift skills matrix"), purpose: t("识别独立操作、指导下操作、待培训和师傅覆盖。", "Expose independent, supervised, pending, and mentor coverage."), dataFields: [t("产线", "Line"), t("班次", "Shift"), t("技能", "Skill"), t("资格状态", "Qualification state")], evidenceBoundary: t("只展示合成覆盖率，不暗示实际人员绩效。", "Show synthetic coverage only; do not imply actual employee performance.") },
      { id: "skills-viz-standard", kind: "matrix", title: t("现场标准执行控制板", "Shop-floor standard execution board"), purpose: t("把培训、3分钟汇报、5S、文件、保养和EHS放在同一节奏中。", "Place training, three-minute reporting, 5S, documents, maintenance, and EHS in one operating cadence."), dataFields: [t("每日任务", "Daily task"), t("周期检查", "Recurring check"), t("异常责任人", "Exception owner"), t("关闭状态", "Closure state")], evidenceBoundary: t("不展示真实安全事件、设备编号或员工记录。", "Do not display actual safety events, equipment IDs, or employee records.") },
    ],
    imagePrompts: [
      { id: "skills-hero", use: "hero", aspectRatio: "16:9", prompt: t("明亮整洁的轴承工厂培训站，经验员工在安全围栏外向新员工演示工业控制面板，双方佩戴正确PPE但面部不可识别，背景有清晰的定置线、标准作业文件夹和维护看板，屏幕内容脱敏，真实自然光与克制电影构图。", "A bright, immaculate bearing-plant training station. An experienced operator demonstrates an industrial control panel to a new employee from outside the safety boundary. Both wear correct PPE and have no identifiable faces. Clear location markings, standard-work folders, and a maintenance board appear in the background. Screens are sanitized. Photoreal natural light and restrained cinematic composition."), negativePrompt: t("不要无PPE、人员站入危险区、触碰运行设备、可辨识面部、夸张笑容、科幻屏幕或乱码文字。", "No missing PPE, people inside hazardous zones, contact with running equipment, identifiable faces, exaggerated smiles, sci-fi screens, or garbled text."), alt: t("在安全边界外进行的一线技能培训", "Frontline skills training conducted outside the safety boundary") },
      { id: "skills-transition", use: "transition", aspectRatio: "16:9", prompt: t("镜头从一张脱敏每日培训任务表平滑推进到真实培训工位，再自然转到技能矩阵灯墙和整洁的5S区域，始终沿一条清晰引导线移动，低调琥珀状态灯，电影级工业写实。", "A smooth cinematic move from a sanitized daily training task sheet into a real training station, then naturally toward a skills-matrix status wall and an orderly 5S area. The camera follows one clear visual path throughout, with subtle amber status lights and photoreal industrial rendering."), negativePrompt: t("不要跳切、悬浮卡片堆积、人物穿模、错误安全行为、品牌或可读私人信息。", "No jump cuts, stacked floating cards, intersecting people or machinery, unsafe behavior, brands, or readable private information."), alt: t("从每日培训任务到技能矩阵和标准现场", "From daily training tasks to skills matrix and standard work") },
    ],
    evidenceBoundary: t("公开页面使用虚构员工、班次、设备和培训记录；不展示姓名、员工编号、考核结果、安全事件或内部文件原件。", "The public page must use fictional employees, shifts, equipment, and training records. Do not expose names, employee IDs, assessment results, safety incidents, or internal source documents."),
  }),
] as const;

export type FactoryTransformationCaseStudyEntry =
  (typeof factoryTransformationCaseStudies)[number];

export const factoryTransformationCaseStudyBySlug = Object.fromEntries(
  factoryTransformationCaseStudies.map((caseStudy) => [
    caseStudy.slug,
    caseStudy,
  ]),
) as {
  readonly [Slug in FactoryTransformationCaseStudySlug]: Extract<
    FactoryTransformationCaseStudyEntry,
    { slug: Slug }
  >;
};

export function getFactoryTransformationCaseStudy(
  slug: string,
): FactoryTransformationCaseStudyEntry | undefined {
  return factoryTransformationCaseStudies.find(
    (caseStudy) => caseStudy.slug === slug,
  );
}

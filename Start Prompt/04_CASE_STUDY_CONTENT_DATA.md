# Case Study Content Data

## Case Study 1: Production Notice Workflow Standardization

### Title

Production Notice Workflow Standardization

### Subtitle

From cross-system manual checking to standard-compliant release in under 1 minute.

### Business Problem

Production notice preparation required repeated manual checks across Siemens Teamcenter (TC), Yonyou ERP, BOM records, inventory data, process requirements, production schedules, and delivery information.

The process usually took around 20-40 minutes and depended heavily on experienced users. Manual copying, missing information, repeated checking, and coordination errors created execution risk.

### Felix's Role

Felix supported the workflow improvement by standardizing required input information, clarifying BOM/material/process/planning/delivery data relationships, and building a tool-assisted notice generation workflow.

### Methods

- Workflow standardization
- Cross-system information mapping
- BOM/material verification
- ERP/TC data alignment
- Production notice format standardization
- Human review before release
- PDCA-style iteration from real use

### Action

Standardized input fields and integrated:

- BOM data
- Inventory information
- Process requirements
- Production planning
- Delivery information
- Material codes
- Project/order information

Built a digital workflow/tool concept that allowed production notices to be generated quickly and consistently.

### Result

- Production notice preparation time reduced from around 20-40 minutes to under 1 minute.
- Less-experienced users can generate standard-compliant production notices.
- Reduced repeated manual checks, missing information, manual copying, coordination errors, and rework.

### Suggested Visual

Before:

TC → ERP → BOM → Inventory → Process Requirement → Manual Calculation → Production Notice → Review

After:

Standard Input → Automated Logic → Notice Output → Human Review → Release

### Public Evidence

Use the public sanitized project:

- Structured Operations Notice Workbench
- GitHub: https://github.com/Felix-Zuo/factory-production-notice-agent

This public project should be introduced as a sanitized/synthetic-data showcase inspired by real workflow patterns.

---

## Case Study 2: Trial Production Takt Simulation & Changeover Improvement

### Title

Trial Production Takt Simulation & Changeover Improvement

### Subtitle

Reducing trial adjustment cycle, scrap, and repeated trial-and-error before ramp-up.

### Business Problem

Trial production and model changeover preparation relied heavily on repeated physical trial-and-error, manual judgment, and adjustment.

Full-line takt bottlenecks were difficult to identify before enough trial data was collected. Repeated trial machining and debugging created time loss, scrap material, and inefficient engineering adjustment.

### Felix's Role

Felix worked with engineering teams during trial production to simulate full-line takt time, import machine parameters, and identify mass-production bottlenecks before ramp-up.

### Methods

- Trial production coordination
- Full-line takt simulation
- Machine parameter input
- Bottleneck calculation
- Engineering/process adjustment support
- Lean waste reduction
- PDCA improvement cycle
- Data-supported decision making

### Action

Used simulation and data calculation to replace part of the repeated trial-and-error process.

Supported engineering teams by:

- Modeling full-line process flow
- Importing machine parameters
- Checking takt assumptions
- Identifying capacity bottlenecks
- Supporting adjustment before full ramp-up
- Turning trial observations into repeatable analysis

### Result

- Trial analysis and adjustment cycle shortened from around 3 days to 1 day.
- Trial machining and debugging scrap material reduced by around 90%.
- Estimated saving for a regular model changeover reached around RMB 20,000 per changeover across inner/outer rings, auxiliary components, consumables, and labor efficiency.

### Suggested Visual

Show a simplified production line:

Process A → Process B → Process C → QA → Packing

Then show:

- Machine takt
- Buffer status
- Waiting
- Blocking
- Bottleneck station
- Before/after cycle timeline
- Scrap reduction card
- Estimated saving card

### Public Evidence

Use the public sanitized project:

- Factory Takt Simulator
- GitHub: https://github.com/Felix-Zuo/factory-takt-simulator
- Product page: https://felix-zuo.github.io/factory-takt-simulator/?view=showcase

This should be the most visually impressive case.

---

## Case Study 3: Supply-Production-Delivery Operations Visibility

### Title

Supply-Production-Delivery Operations Visibility

### Subtitle

Improving visibility across procurement, shipping, inventory, production, WIP, delivery, and exception follow-up.

### Business Problem

Procurement, shipping, inventory, production, WIP, delivery, and historical project information were scattered across spreadsheets, system exports, and shared files.

This created repeated checking, waiting time, information searching, inconsistent reporting, coordination errors, and delayed exception follow-up.

### Felix's Role

Felix built and maintained a supply-production-delivery operations dashboard used in departmental workflow and reporting analysis.

### Methods

- Data consolidation
- Spreadsheet workflow improvement
- Standardized reporting
- Supply-production-delivery tracking
- Exception follow-up
- Project progress visibility
- Lean waste reduction
- Departmental reporting support

### Action

Integrated and organized information across:

- Procurement
- Shipping
- Inventory
- Production
- WIP
- Delivery
- Project progress
- Exception status

Built a dashboard/reporting workflow to support department-level review and daily follow-up.

### Result

- Improved visibility across supply, production, and delivery stages.
- Supported departmental workflow and reporting analysis.
- Reduced waiting time, repeated manual checks, information searching, over-processing, coordination errors, and rework.
- Improved project progress and exception follow-up visibility.

### Suggested Visual

Before:

Separate spreadsheets, system exports, message records, manual summaries, and historical files.

After:

Unified view with procurement, inventory, WIP, production, shipment, delivery, project progress, and exception follow-up.

### Public Evidence

Use the public sanitized project:

- Factory Excel Ops Dashboard
- GitHub: https://github.com/Felix-Zuo/factory-excel-ops-dashboard
- Product page: https://felix-zuo.github.io/factory-excel-ops-dashboard/showcase.html

---

## Portfolio Lab Support Cases

### BOM Knowledge Base

Use as support for material readiness and BOM verification.

Public positioning:

> A privacy-safe BOM and material search foundation for parsing cleaned Excel BOMs, building local indexes, and preserving source evidence for material traceability.

Avoid describing it as a completed enterprise RAG system unless the repository later contains that implemented functionality.

### Operations Intelligence Platform

Use as a concept demo showing system integration vision.

Public positioning:

> A personal synthetic-data concept demo integrating operations data, BOM readiness, inventory risk, release gates, line simulation, and tool-call traces into a local control-tower-style product.

Avoid implying production deployment.

### Six Sigma Study App

Use under methodology or learning discipline.

Public positioning:

> A local-first bilingual Six Sigma study platform showing Felix's structured approach to technical learning, Lean/Six Sigma concepts, content workflows, and validation gates.

### HulunGuard

Use as optional experimental evidence.

Public positioning:

> A proof-first reliability guard for long-running AI agent work, focused on evidence, task drift, unresolved failures, and verification.

## Standard Confidentiality Text

Use this text on case pages:

> This case study is presented with sanitized or synthetic data. It describes selected improvement outcomes and tool concepts based on real manufacturing workflow patterns. No customer names, private BOMs, supplier records, internal system exports, production routes, machine parameters, or confidential factory files are disclosed.

# Discovery Report

Project: Felix Zuo independent manufacturing portfolio website  
Date: 2026-07-03  
Prepared from: Start Prompt documents, local repository review, GitHub CLI metadata, and public Pages checks.

## Executive Positioning

Felix Zuo should be presented as a manufacturing project coordination and digital process improvement professional.

The strongest public story is not "AI engineer" or "software engineer". It is:

> Manufacturing project coordination and process improvement, supported by practical digital tools and public sanitized-data showcases.

The site should show that Felix can connect production planning, supply chain execution, trial production, PPAP support, DFMEA-related follow-up, audit support, corrective action closure, Lean/Six Sigma thinking, PDCA cycles, and digital workflow tools into measurable manufacturing improvement.

## What The Start Prompt Documents Say

The Start Prompt package defines a clear hierarchy:

- Lead with manufacturing outcomes, not biography.
- Use three primary case studies:
  - Production Notice Workflow Standardization
  - Trial Production Takt Simulation and Changeover Improvement
  - Supply-Production-Delivery Operations Visibility
- Use public GitHub repositories as sanitized evidence, not as the main identity.
- Keep AI, RAG, and agent wording secondary unless it directly supports workflow standardization, visibility, or verification.
- Keep confidentiality boundaries visible and professional.
- Prepare the codebase and documentation so Claude/Fable 5 can later review narrative clarity, design strategy, and case-study framing.

## Current Public Profile Snapshot

GitHub profile metadata checked with `gh api users/Felix-Zuo` on 2026-07-03:

- Name: Felix Zuo (left profile name includes Chinese name)
- Bio: "Smart Manufacturing & Industrial AI | Factory Digitalization | AI Agent/RAG | MES/WMS/ERP"
- Public repositories: 8
- Profile updated at: 2026-07-01T18:24:35Z

Local profile README currently frames the GitHub front door as "Smart Manufacturing & Industrial AI Applications". This is useful evidence, but the independent website should sharpen the market-facing story around manufacturing project execution and process improvement.

## GitHub Portfolio Evidence

Public repository metadata checked with `gh repo list Felix-Zuo --limit 80` on 2026-07-03.

### Tier 1: Main Public Evidence

#### Factory Takt Simulator

- Repository: https://github.com/Felix-Zuo/factory-takt-simulator
- Live page: https://felix-zuo.github.io/factory-takt-simulator/?view=showcase
- Local stack: React, TypeScript, Vite, Electron, Zustand, React Flow, Framer Motion.
- Public version: `0.6.5-beta` in local `package.json`.
- Evidence reviewed:
  - README with synthetic-data boundary, screenshots, product page link, and verification commands.
  - `docs/ARCHITECTURE.md`: deterministic graph editor, simulation engine, takt calculator, bottleneck analyzer, report exporter, agent bridge.
  - `docs/QUALITY.md`: build, lint, maintainability, audit, smoke, and Pages gates.
  - `docs/PROJECT_HISTORY.md`: public generalization history and synthetic full-line template hardening.
  - `src/lib/analysis.ts`: real bottleneck analysis combining static capacity and runtime symptoms.
- Website role: strongest visual proof for trial production takt simulation, bottleneck analysis, buffer tuning, and model-changeover improvement.

#### Structured Operations Notice Workbench

- Repository: https://github.com/Felix-Zuo/factory-production-notice-agent
- Live page: https://felix-zuo.github.io/factory-production-notice-agent/showcase.html
- Local stack: Python package and CLI, openpyxl, local HTTP demo boundary.
- Public version: `0.4.1` in local `pyproject.toml`.
- Evidence reviewed:
  - README with generic operations notice contract, sample commands, CLI/API paths, public sample data, and validation command.
  - `docs/ARCHITECTURE.md`: contract-first generator from JSON, CSV, templates, or schedule plan into workbook, HTML preview, manifest, and workflow context.
  - `docs/PRIVACY.md`: explicit do-not-commit and public sample rules.
  - `docs/QUALITY.md`: request limits, loopback default, formula escaping, HTML escaping, and artifact path boundary.
  - `CHANGELOG.md`: v0.4.1 sample catalog, v0.4.0 templates and schedule generation, v0.3.0 CSV/profile support.
  - `src/factory_production_notice/generator.py`: generates Excel, HTML, manifest, and agent context with safe Excel value handling.
- Website role: primary proof for production notice workflow standardization and the 20-40 minutes to under 1 minute improvement.

#### Factory Excel Ops Dashboard

- Repository: https://github.com/Felix-Zuo/factory-excel-ops-dashboard
- Live page: https://felix-zuo.github.io/factory-excel-ops-dashboard/showcase.html
- Local stack: Python package and CLI, openpyxl, local HTML dashboard export.
- Public version: `0.2.2` in local `pyproject.toml`.
- Evidence reviewed:
  - README with local-first spreadsheet operations positioning, data boundary, quick start, config profiles, and validation.
  - `docs/architecture.md`: file classifier -> field mapper -> standard records -> metrics -> summary/dashboard/analysis context.
  - `docs/data_safety_checklist.md`: repository, search, package, and GitHub checks.
  - `docs/product_evolution.md`: evolution from manual spreadsheet flow to generic operations profile.
  - `docs/quality_gates.md`: pytest, config validation, demo run, analysis context, and package safety.
  - `src/factory_excel_ops/metrics.py`: configurable metric engine for inventory, demand, fulfillment, replenishment, and work output.
- Website role: primary proof for supply-production-delivery visibility and reducing spreadsheet-driven repeated checks.

### Tier 2: Supporting Manufacturing Data Foundation

#### Operations Intelligence Platform

- Repository: https://github.com/Felix-Zuo/factory-ops-intelligence-platform
- Live page: https://felix-zuo.github.io/factory-ops-intelligence-platform/showcase.html
- Local stack: FastAPI, React/Vite, SQLite-style seed workflow, deterministic domain functions.
- Public version: `0.3.1` in local `package.json` and API metadata.
- Evidence reviewed:
  - README with control tower, release gate, BOM and inventory, line simulation, agent trace, adapter boundary, and synthetic-data statement.
  - `ARCHITECTURE.md`: demo-ready operations intelligence layer between fragmented manufacturing data and decisions.
  - `DATA_CONTRACT.md`: materials, BOM, inventory, demand, policy signals, scenario profiles, release gate, adapters, agent trace.
  - `PROJECT_HISTORY.md`: independent public demo, not a private deployment mirror.
  - `QUALITY_STANDARD.md`: `npm run test:all`, audit, diff check, UI acceptance.
  - `apps/api-server/factory_ops_api/domain.py`: deterministic BOM explosion, material risk, source refs, release gate, simulation and trace functions.
  - `apps/api-server/factory_ops_api/main.py`: bounded FastAPI request models and local CORS origins.
- Website role: Portfolio Lab and future-facing concept demo. It should be described as a personal synthetic-data concept demo, not a company-deployed system.

#### Factory Data Pocket Lab

- Repository: https://github.com/Felix-Zuo/factory-data-pocket-lab
- Local stack: Android WebView app.
- Public version: `0.4.0` in local Gradle config.
- Evidence reviewed:
  - README with offline manufacturing data-modeling walkthrough, BOM/inventory/supplier/lot/routing examples, glossary, vocabulary, and local notes.
  - Gradle files with package namespace `com.factorydata.pocketlab`.
- Website role: supporting proof of portable manufacturing data modeling and learning/reference material.

#### BOM Knowledge Base

- Repository metadata: `Felix-Zuo/bom-knowledge-base`
- Current visibility checked on 2026-07-03: PRIVATE.
- Description: "Generic, privacy-safe Excel BOM knowledge base toolkit"
- Website role: use carefully. It should not be presented as public clickable evidence in v1 unless made public and audited. It can be mentioned as a future or non-public direction only if the wording avoids exposing private details.

### Tier 3: Adjacent Evidence

#### Six Sigma Study App

- Repository: https://github.com/Felix-Zuo/six-sigma-study-app
- Public visibility: PUBLIC.
- Evidence reviewed through GitHub contents API README:
  - Local-first Android/PWA bilingual study platform.
  - 33 chapters, 449 aligned study pages, 470 preserved figure/table/formula assets.
  - Public rights boundary and non-commercial disclaimer.
  - Validation matrix for content, books, public safety, source coverage, UX, Android, and release package.
- Website role: methodology support. Use it to show Lean/Six Sigma learning discipline, content pipeline rigor, and validation gates. Do not let it dominate the manufacturing project improvement story.

#### HulunGuard

- Repository: https://github.com/Felix-Zuo/HulunGuard
- Live page: https://felix-zuo.github.io/HulunGuard/
- Public visibility: PUBLIC.
- Local evidence reviewed:
  - README: proof-first reliability guard and desktop risk meter for long-running AI agent work.
  - `PROJECT_DEFINITION.md`: evidence coverage, intent drift, execution freshness, state continuity, failure honesty.
- Website role: optional experimental proof of verification thinking and AI-assisted workflow governance. It should sit behind the manufacturing story.

## Public Pages Check

HTTP checks with `Invoke-WebRequest` on 2026-07-03:

| Page | Status | Title or signal |
| --- | ---: | --- |
| Factory Takt Simulator | 200 | SPA title `factory-takt-simulator`, content includes takt/showcase signals |
| Structured Operations Notice Workbench | 200 | `Structured Operations Notice Workbench` |
| Factory Excel Ops Dashboard | 200 | `Operations Data Workbench | factory-excel-ops-dashboard` |
| Operations Intelligence Platform Showcase | 200 | `Operations Intelligence Platform Showcase` |

## Which Public Projects Support Which Website Case Studies

| Website case study | Primary public evidence | Supporting evidence |
| --- | --- | --- |
| Production Notice Workflow Standardization | Structured Operations Notice Workbench | Operations Intelligence Platform release gate and notice generator concept |
| Trial Production Takt Simulation and Changeover Improvement | Factory Takt Simulator | Operations Intelligence Platform line simulation concept |
| Supply-Production-Delivery Operations Visibility | Factory Excel Ops Dashboard | Operations Intelligence Platform control tower, Factory Data Pocket Lab |
| Methodology and learning discipline | Six Sigma Study App | HulunGuard verification thinking |

## What Should Be Emphasized

- Manufacturing execution outcomes:
  - Production notice preparation: around 20-40 minutes to under 1 minute.
  - Trial takt analysis and adjustment: around 3 days to 1 day.
  - Trial machining and debugging scrap: around 90 percent reduction.
  - Regular model changeover savings: estimated around RMB 20,000 per changeover.
  - Dashboard adopted in departmental workflow and reporting analysis.
- Full-cycle project tracking from risk review to delivery, audit support, corrective action, and improvement reporting.
- Practical workflow standardization, source mapping, validation, review gates, and local-first data safety.
- Public evidence as sanitized or synthetic demonstrations inspired by real manufacturing workflow patterns.

## What Should Be Worded Carefully

- Use "estimated" for the RMB 20,000 savings unless audited finance records are later available.
- Do not imply ownership of an enterprise MES/WMS/ERP implementation.
- Do not present Operations Intelligence Platform as a deployed company system.
- Do not present BOM Knowledge Base as public evidence while its repository is private.
- Do not imply public screenshots or sample data include real customer records, real BOMs, production routes, supplier records, machine parameters, ERP exports, or confidential factory files.
- Keep AI, RAG, and agent wording as support for evidence, automation, and workflow review, not as the main professional identity.

## Presentation Gaps And Opportunities

- Current GitHub profile front door still leans toward "Smart Manufacturing & Industrial AI"; the website should provide a clearer recruiting narrative centered on manufacturing project coordination and process improvement.
- The public repositories are strong but scattered. The website should translate them into three business case studies first, then show the Portfolio Lab as evidence.
- Case-study detail pages can convert strong metrics into a readable problem -> role -> method -> action -> result -> public evidence structure.
- Screenshots already exist in several repositories and can be reused to make the site feel evidence-backed instead of generic.
- A persistent confidentiality note should be visible near case studies and Portfolio Lab.
- Claude/Fable 5 can later improve copy hierarchy, first-screen pacing, and recruiter readability without changing the technical structure.


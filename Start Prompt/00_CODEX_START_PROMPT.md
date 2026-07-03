# Codex Start Prompt

## Project

Project name: `felix-manufacturing-portfolio`

Build a premium independent portfolio website for Felix Zuo.

This project is not a normal developer portfolio. It is a manufacturing project improvement portfolio: part case-study platform, part product showcase, part operational improvement evidence room.

The website should make readers understand Felix as a manufacturing project coordination and process improvement professional who can translate factory workflow problems into structured tracking, measurable improvement, practical digital tools, and credible portfolio evidence.

## Before You Build

Start with discovery.

First inspect these project-context documents in the `start-prompt/` folder:

1. `01_PROFILE_AND_CAREER_CONTEXT.md`
2. `02_GITHUB_PORTFOLIO_MAP.md`
3. `03_WEBSITE_PRODUCT_BRIEF.md`
4. `04_CASE_STUDY_CONTENT_DATA.md`
5. `05_CODEX_CLAUDE_COLLABORATION.md`

Then review Felix's GitHub profile and repositories carefully:

- GitHub profile: https://github.com/Felix-Zuo
- Profile repository: https://github.com/Felix-Zuo/Felix-Zuo
- Factory Takt Simulator: https://github.com/Felix-Zuo/factory-takt-simulator
- Factory Production Notice Agent / Structured Operations Notice Workbench: https://github.com/Felix-Zuo/factory-production-notice-agent
- Factory Excel Ops Dashboard: https://github.com/Felix-Zuo/factory-excel-ops-dashboard
- BOM Knowledge Base: https://github.com/Felix-Zuo/bom-knowledge-base
- Operations Intelligence Platform: https://github.com/Felix-Zuo/factory-ops-intelligence-platform
- Factory Data Pocket Lab: https://github.com/Felix-Zuo/factory-data-pocket-lab
- HulunGuard: https://github.com/Felix-Zuo/HulunGuard
- Six Sigma Study App: https://github.com/Felix-Zuo/six-sigma-study-app
- Other repositories under the same profile if visible and relevant

Treat the GitHub review as part of the work, not as optional browsing. Read READMEs, project documents, visible product pages, public demo pages, package/config files, and representative source files before choosing the final website structure.

## Discovery Output Required First

Before implementing the website, create these documents in the project:

1. `docs/DISCOVERY_REPORT.md`
   - Summary of Felix's positioning
   - What the GitHub portfolio currently proves
   - What each major repository contributes to the future website
   - Gaps or opportunities in presentation

2. `docs/CONTENT_STRATEGY.md`
   - Website narrative
   - Audience reading path
   - Case study hierarchy
   - What should be shown on the homepage versus deeper pages

3. `docs/PROJECT_PLAN.md`
   - Proposed site architecture
   - Component plan
   - Data/content model
   - First implementation milestones

4. `CLAUDE_BRIEF.md`
   - A clean handoff brief for Claude to later improve copywriting, storytelling, visual hierarchy, and case-study clarity

After creating those documents, proceed with implementation.

## Core Positioning

Felix Zuo is best presented as:

Manufacturing Project Coordination & Digital Process Improvement

He works at the intersection of:

- Manufacturing project coordination
- Production operations
- Supply chain execution
- Material readiness
- Trial production improvement
- PPAP and mass-production preparation
- Delivery follow-up
- Audit support and corrective action closure
- Lean / Six Sigma thinking
- PDCA improvement
- Practical digital tools for workflow standardization and operational visibility

The main story is not "AI engineer". The main story is manufacturing improvement with measurable results. Digital tools and AI-assisted development are enablers, not the identity.

## Outcomes To Feature

Use these as the strongest proof points:

- Production notice preparation improved from around 20-40 minutes to under 1 minute.
- Trial production takt analysis and adjustment cycle shortened from around 3 days to 1 day.
- Trial machining and debugging scrap material reduced by around 90%.
- Estimated saving of around RMB 20,000 per regular model changeover across inner/outer rings, auxiliary components, consumables, and labor efficiency.
- Supply-production-delivery dashboard adopted in departmental workflow and reporting analysis.
- Digital and automation tools reduced waiting time, repeated manual checks, information searching, over-processing, coordination errors, and rework.

## Website Goal

The website should be impressive to:

- Manufacturing project managers
- Process improvement managers
- Quality and launch teams
- Supply chain and operations leaders
- Smart manufacturing teams
- Recruiters who may not understand factory systems but understand numbers, projects, and outcomes
- Hiring managers at manufacturing, semiconductor equipment, EMS/ODM, industrial automation, automotive components, and supply chain digitalization teams

The website should quickly answer:

1. Who is Felix?
2. What manufacturing problems does he solve?
3. What measurable outcomes has he delivered?
4. What public portfolio evidence supports the claims?
5. Why is he different from a normal supply chain specialist or a normal software developer?

## Implementation Direction

Recommended stack for v1:

- Next.js
- TypeScript
- Tailwind CSS
- Framer Motion for subtle motion
- Data-driven content files
- Static site first
- Vercel-ready deployment
- Public demos and GitHub links integrated as evidence

Keep the project extensible. The portfolio may later add:

- English/Chinese toggle
- More case studies
- Interactive demos
- Resume download
- Blog or field notes
- Project one-page briefs
- Video walkthroughs
- More GitHub showcase integrations

## Suggested First Build

Build v1 as a polished static portfolio with:

- Home page
- Impact metrics section
- Full-cycle manufacturing project map
- Three featured case studies
- Portfolio Lab section
- Methodology section
- About section
- Contact / resume CTA
- Case study detail pages
- Public project detail cards
- Confidentiality note
- README
- CLAUDE_BRIEF.md

## Content Style

Use premium, direct, evidence-based language.

Prefer concrete manufacturing language:

- project execution
- trial production
- takt analysis
- process preparation
- PPAP support
- material readiness
- cross-functional follow-up
- audit readiness
- corrective action closure
- supply-production-delivery visibility
- workflow standardization
- scrap reduction
- waiting-time reduction
- repeated manual check reduction

Avoid turning the site into keyword soup. Mention AI, RAG, Agent, digital twin, or smart manufacturing only when the context truly needs it.

## Confidentiality Principle

All public materials should use sanitized or synthetic data.

The website should include a professional boundary statement explaining that public demos and visuals are based on sanitized or synthetic data and do not disclose customer names, private BOMs, supplier records, real machine parameters, internal ERP exports, production routes, or confidential factory files.

This is part of Felix's professional maturity, not a limitation.

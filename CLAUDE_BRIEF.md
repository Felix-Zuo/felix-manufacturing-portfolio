# Claude/Fable 5 Brief

## Project Positioning

This is Felix Zuo's independent manufacturing project improvement portfolio.

The site should present Felix as:

> A manufacturing project coordination and process improvement professional who uses structured follow-up, Lean/Six Sigma thinking, PDCA cycles, and practical digital tools to improve manufacturing execution.

Do not turn the site into a pure software engineering portfolio, pure AI portfolio, or machine learning research profile.

## Current Implementation

The v1 implementation is a static Next.js App Router portfolio with:

- Home page
- Impact metrics
- Full-cycle manufacturing project map
- Three featured case studies
- Portfolio Lab
- Methodology section
- About section
- Resume/contact CTA
- Confidentiality note
- Case study detail pages

Content is kept in structured `src/data` files so narrative and design can be improved without rewriting core components.

Current architecture:

- `src/app/page.tsx`: homepage assembly.
- `src/app/case-studies/[slug]/page.tsx`: static case-study detail route.
- `src/app/not-found.tsx`: invalid route fallback.
- `src/components`: reusable section, metric, case, portfolio, methodology, CTA, reveal, and workflow components.
- `src/data`: profile, metrics, case studies, portfolio projects, methodology, and navigation.
- `public/evidence`: public-safe screenshots copied from local public showcase repositories.

## Key Case Studies

### Production Notice Workflow Standardization

Core result:

- Production notice preparation improved from around 20-40 minutes to under 1 minute.

Public evidence:

- Structured Operations Notice Workbench
- https://github.com/Felix-Zuo/factory-production-notice-agent
- https://felix-zuo.github.io/factory-production-notice-agent/showcase.html

Narrative angle:

- Repeated cross-system manual checks became structured inputs, generated notice artifacts, workflow context, and human review before release.

### Trial Production Takt Simulation and Changeover Improvement

Core results:

- Trial analysis and adjustment cycle shortened from around 3 days to 1 day.
- Trial machining and debugging scrap reduced by around 90 percent.
- Estimated saving around RMB 20,000 per regular model changeover.

Public evidence:

- Factory Takt Simulator
- https://github.com/Felix-Zuo/factory-takt-simulator
- https://felix-zuo.github.io/factory-takt-simulator/?view=showcase

Narrative angle:

- Full-line takt modeling, machine parameter input, bottleneck analysis, buffer/transfer modeling, and reviewable capacity reporting reduced repeated trial-and-error.

### Supply-Production-Delivery Operations Visibility

Core result:

- Dashboard adopted in departmental workflow and reporting analysis.

Public evidence:

- Factory Excel Ops Dashboard
- https://github.com/Felix-Zuo/factory-excel-ops-dashboard
- https://felix-zuo.github.io/factory-excel-ops-dashboard/showcase.html

Narrative angle:

- Scattered spreadsheets and exports became a local-first workflow for classification, field mapping, metric calculation, dashboard export, and reporting handoff.

## Portfolio Lab

Primary evidence:

- Factory Takt Simulator
- Structured Operations Notice Workbench
- Factory Excel Ops Dashboard

Supporting/concept evidence:

- Operations Intelligence Platform: personal synthetic-data control-tower concept demo.
- Factory Data Pocket Lab: offline manufacturing data modeling and traceability reference.
- Six Sigma Study App: Lean/Six Sigma learning discipline and validation-heavy content workflow.
- HulunGuard: proof-first agent reliability and verification thinking.

Do not show BOM Knowledge Base as a public evidence card unless its private status changes and public data safety is audited.

## Content Strategy

Homepage order:

1. Outcomes and positioning
2. Impact metrics
3. Full-cycle manufacturing project map
4. Case studies
5. Portfolio Lab
6. Methodology
7. About
8. Contact/resume CTA
9. Confidentiality note

Tone:

- Credible
- Evidence-based
- Industrial
- Calm
- Measurable
- Practical

Avoid:

- Keyword soup
- AI hype
- Pure developer positioning
- Claims of production deployment where evidence is a demo

## Visual Direction

Target feel:

- Industrial control room
- Manufacturing project review deck
- Premium consulting case study
- Modern product landing page

Use:

- Metric cards
- Process maps
- Timelines
- Before/after diagrams
- Public evidence cards
- Dashboard-like sections

Palette:

- Dark graphite/deep navy
- Off-white
- Steel blue
- Amber warning/review accents
- Green improvement accents

## Files Created

- `docs/DISCOVERY_REPORT.md`
- `docs/CONTENT_STRATEGY.md`
- `docs/PROJECT_PLAN.md`
- `CLAUDE_BRIEF.md`
- `README.md`
- `AGENTS.md`
- `src/data/*`
- `src/components/*`
- `src/app/page.tsx`
- `src/app/case-studies/[slug]/page.tsx`
- `public/evidence/*`

## Recommended Next Improvements For Claude/Fable 5

- Tighten the first-screen headline and supporting copy.
- Improve case-study storytelling so manufacturing readers see Felix's role clearly.
- Check whether recruiters can understand the site within 30 seconds.
- Reduce any wording that over-emphasizes AI or software implementation.
- Strengthen visual hierarchy around the three primary outcomes.
- Review whether each public project card clearly supports the main story.

## Open Questions

- Should the final site include a downloadable resume now, or only a contact CTA until a resume PDF is ready?
- Should the website be English-only for v1, or should Chinese copy be added after the structure stabilizes?
- Should sanitized screenshots be copied into this repository for permanent display, or should v1 link to public project pages only?
- Should BOM Knowledge Base become public later after a data safety review?

## Confidentiality Rule

All public-facing content must use sanitized or synthetic data. Do not expose customer names, private BOMs, supplier records, internal system exports, production routes, machine parameters, shipment data, or confidential factory files.

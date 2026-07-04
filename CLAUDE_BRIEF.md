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

## Review Pass Applied (2026-07, Claude/Fable 5)

A multi-agent review (content accuracy, confidentiality, storytelling, design/a11y) was run and
its confirmed findings applied:

- Hero summary rewritten: grammatical, names the automotive bearing industry, ends with the
  brief's "structured workflows, measurable improvements, and practical digital tools" triad.
- Hero stat strip now shows the three strongest impact metrics (from `metrics.ts`) instead of
  site-inventory counts, so outcomes are on the first screen.
- CTA has a real contact channel: `mailto:` to `profile.email` (zuoyaxuan666@gmail.com), with
  GitHub as the secondary link. CTA section has `id="contact"` and a nav entry.
- Case detail pages use the brief-mandated case-specific confidentiality text (via a `text`
  prop on `ConfidentialityNotice`) and frame public evidence as a sanitized/synthetic showcase.
- Portfolio Lab section now carries the compact confidentiality notice; the BOM boundary note
  was restyled for the dark section.
- Meta/self-referential copy removed from section summaries and the About block; About now uses
  the LinkedIn-style experience summary from the profile brief.
- Copy fidelity fixes: "Felix's role" heading, typographic arrows in metric values, "Trial takt
  analysis and adjustment cycle" label, case subtitles/actions realigned to source, methodology
  pillar renamed to "Manufacturing Launch & Quality Support" with "Over-processing reduction" added.
- Design/a11y: `Reveal` now actually animates (was a no-op) with reduced-motion opt-out,
  responsive hero headline, header moved outside `main`, anchor scroll-margin under the sticky
  header, gated smooth scroll, focus-visible outlines, eyebrow letter tracking, metric source
  contrast bump.

## Recommended Next Improvements

- Mobile navigation: nav links are hidden below `lg` with no menu; add a small disclosure menu.
- Site header/nav is absent on case-study detail pages (only "Back to portfolio"); consider a
  shared header.
- Consider a downloadable resume PDF once ready (CTA currently email + GitHub).
- Review whether the amber tone on the changeover-saving metric should become green
  (improvement) or stay amber (estimated/review signal) — currently amber, intentionally.

## Open Questions

- Should the website be English-only for v1, or should Chinese copy be added after the structure stabilizes?
- Should BOM Knowledge Base become public later after a data safety review?
- If this repository is ever made public, decide whether `Start Prompt/` and `docs/` (internal
  positioning strategy) should be removed from history or kept.

## Confidentiality Rule

All public-facing content must use sanitized or synthetic data. Do not expose customer names, private BOMs, supplier records, internal system exports, production routes, machine parameters, shipment data, or confidential factory files.

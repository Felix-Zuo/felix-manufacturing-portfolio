# Claude/Fable 5 Brief

## Project Positioning

This is Felix Zuo's independent manufacturing project improvement portfolio.

The site should present Felix as:

> A manufacturing project coordination and process improvement professional who uses structured follow-up, Lean/Six Sigma thinking, PDCA cycles, and practical digital tools to improve manufacturing execution.

Do not turn the site into a pure software engineering portfolio, pure AI portfolio, or machine learning research profile.

## Current Implementation

The current implementation is a static Next.js App Router portfolio with a scroll-directed
cinematic homepage and static case-study detail routes:

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
- `src/components/CinematicBackdrop.tsx`: one persistent Three.js/R3F world, camera path,
  project nodes, rail pulses, and bullet-time time scaling.
- `src/components/CinematicScene.tsx`: accessible HTML scene wrapper with sticky desktop
  timing, scroll-linked entry/hold/exit transforms, and static mobile/reduced-motion fallback.
- `src/components/CinematicCaseStudy.tsx`: reusable full-frame case-study composition.
- `src/components`: reusable metric, portfolio, methodology, CTA, reveal, screenshot, and workflow components.
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

Homepage scene order:

1. Felix Zuo identity, positioning, and live operations model
2. Impact metrics
3. Full-cycle manufacturing project map
4. Production notice case
5. Trial takt/changeover case
6. Operations visibility case
7. Before/after control loop
8. Three primary evidence systems
9. Four connected/supporting tools
10. Methodology
11. About, confidentiality, and BOM-publication boundary
12. Contact/resume CTA

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
- One continuous spatial camera move
- Manufacturing project review deck
- Premium consulting case study
- Independent professional homepage

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

## v2 "Control Room" Redesign (2026-07, Claude/Fable 5)

Triggered by user feedback that v1 felt template-like, lacked premium motion, and used
mixed-language screenshots. See `docs/REDESIGN_SPEC.md` for the full design system.

- Single coherent dark industrial theme (no more alternating white/dark sections); blueprint
  grid textures, mono data labels, amber/emerald/steel signal palette.
- Motion: count-up/count-down impact metrics (`CountUp`), animated hero line simulation
  (`HeroConsole` — stands in for video), outcome readout marquee (`StatusTicker`),
  scroll-drawn project map progress line, staggered reveals. All reduced-motion safe and
  hydration-mismatch free (verified in both motion modes).
- Evidence screenshots recaptured in English at uniform 16:10 from the live GitHub Pages via
  Playwright + Edge (takt simulator switched to EN through its `FactoryTaktAgent` bridge,
  full-line template loaded, simulation running at t=90s). Shown inside a browser-chrome
  frame (`ScreenshotFrame`) with the live URL visible.
- New shared shell: `SiteNav` (fixed, mobile menu) + `SiteFooter` on every page; case detail
  pages restyled with metric chips, animated before/after, and next-case pagination.
- Replaced components: `SectionHeader`→`SectionHeading`, `CaseStudyCard`→`CaseShowcase`.
  New: `SiteNav`, `SiteFooter`, `HeroConsole`, `CountUp`, `StatusTicker`, `ScreenshotFrame`.
- Hero headline now uses the brief's Core Promise ("Manufacturing project chaos, turned into
  measurable improvement.") with the positioning phrase as the mono eyebrow.

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

## v3 One-Shot Cinematic Homepage (2026-07-13, Codex)

- Preserved the v2 control-room palette, evidence screenshots, metrics, and structured data.
- Rebuilt the homepage as 12 connected chapters over one persistent full-viewport WebGL world.
  The camera travels through an industrial rail/tunnel of project nodes instead of restarting
  an animation for each section.
- Added chapter-local time warping: camera travel and scene objects slow around each midpoint,
  while the HTML layer uses sticky entry/hold/exit transforms for the bullet-time effect.
- Every existing homepage surface remains represented: four impact metrics, ten project-cycle
  stages, all three case studies, before/after workflow, all seven public projects, methodology,
  profile, confidentiality boundary, BOM-publication status, and contact links.
- Kept content as normal server-rendered HTML. The WebGL layer is decorative and `aria-hidden`;
  mobile/tablet use normal document flow, and `prefers-reduced-motion` removes the canvas,
  sticky positioning, ticker animation, blur, and transforms.
- Responsive controls: full-width mobile CTAs, two-column hero workstations/readouts, constrained
  grid children, compact supporting-project cards, and zero horizontal overflow at 390 px.
- Dependencies: `three@0.180.0`, `@react-three/fiber@9.6.1`, and matching Three.js types. Three is
  intentionally pinned below the release that warns about R3F's internal legacy clock.
- Verification: lint/build pass; desktop 1440x900 and mobile 390x844 browser checks; WebGL canvas
  nonblank pixel-variance checks; no browser warnings/errors; mobile menu and reduced-motion mode
  exercised; all static case-study routes still prerender.

## v4 Pre-Rendered Industrial Film (2026-07-13, Codex + Production Agents)

- Replaced the homepage's real-time WebGL presentation with a Blender-authored,
  pre-rendered 28-second one-shot factory journey. Scroll now controls film time;
  it is not normal document scrolling.
- Built parameterized hard-surface bearing, six-axis arm, grinding cell, twin guide
  rail, four evidence stations, and a restrained terminal signature. The bright,
  clean factory remains purpose-led rather than decorative.
- Authored eight focus frames at 54, 127, 211, 295, 379, 463, 547, and 631, with
  independent scene bullet-time and a camera that preserves spatial continuity.
- Added separate desktop and mobile camera outputs at 1600 x 900 and 900 x 1600.
  Final Eevee settings use 64 samples, the 1024 MB shadow pool, and 0.75 shadow
  resolution scale after atlas-overflow tests.
- Added `RenderedJourney`: poster-first loading, responsive video source selection,
  smoothed scroll-to-time seeking, chapter snapping, keyboard/touch controls,
  hash navigation, accessible HTML content, and a static reduced-motion mode.
- The independent visual gate failed four early rounds for blank frames, roll,
  clay look, weak composition, a grinding-exit wall clip, and a moving end cut.
  Round 5 passed both complete playblasts after those issues were corrected.
- Source pipeline and review records live in `production/`; generated Blender scenes
  and frame sequences remain ignored. Only encoded web media belongs in `public/media/`.

## v5 Mature Factory And Grinding Hero Pass (2026-07-16, Codex)

- Replaced provisional factory proxies with production assets, including the licensed
  KUKA KR210 visual chain, detailed machine shells, a mature daylight factory hall,
  command-bay display, AGV, and mechanically supported screen stations.
- Rebuilt the outer-ring internal-raceway grinding insert around a horizontal workhead
  and grinding spindle. The hero assembly now uses a short taper arbor, 98 mm profiled
  vitrified CBN wheel, modeled bond and abrasive layers, 504 readable grains, a concave
  raceway, fresh-ground band, stepped soft jaws, spindle seals, cooling rings, and slide
  hardware instead of the earlier oversized wheel and chuck proxies.
- Added a sealed wet process chamber with splash liners, service-panel seams, side
  returns, roof, coolant sump, inspection lamp, two coherent coolant jets, and only
  three short micro-sparks. The operation reads as wet precision grinding rather than
  welding or dry abrasive cutting.
- Re-authored the grinding beat as one continuous 42-to-90 mm move. F180 enters behind
  the enclosure, F195 establishes the full assembly, F211 locks the contact point at
  0.16x/120 fps, F227 exits behind the shell, and F242 returns to the center aisle.
- Added `production/blender/render_grinding_audit.py` and the reference-pass record in
  `production/reviews/grinding-hero-reference-pass.md`. Both 16:9 and 9:16 keep the
  wheel-to-raceway contact centered and legible.
- Twinmotion export and clean-scene re-import pass with 801 objects, 23 materials,
  12 animation actions, and valid long-axis factory bounds. Local shop-floor reference
  imagery is never copied into the repository or export packages.

## Recommended Next Improvements

- Consider a downloadable resume PDF once ready (CTA currently email + GitHub).
- Add a custom OG image and social preview once the final positioning copy is frozen.
- Keep future 3D additions inside the Blender render pipeline; do not restore a
  homepage real-time renderer or add meshes without a narrative purpose.
- Review whether the amber tone on the changeover-saving metric should become green
  (improvement) or stay amber (estimated/review signal) — currently amber, intentionally.

## Open Questions

- Should the website be English-only for v1, or should Chinese copy be added after the structure stabilizes?
- Should BOM Knowledge Base become public later after a data safety review?
- If this repository is ever made public, decide whether `Start Prompt/` and `docs/` (internal
  positioning strategy) should be removed from history or kept.

## Confidentiality Rule

All public-facing content must use sanitized or synthetic data. Do not expose customer names, private BOMs, supplier records, internal system exports, production routes, machine parameters, shipment data, or confidential factory files.

# Redesign Spec — "Control Room" v2

Date: 2026-07-04. Trigger: user feedback that v1 felt template-like ("vibe-coded"), lacked
premium motion, and used messy mixed-language screenshots.

## Design Direction

One coherent dark industrial theme across every page — no alternating white/dark sections.
The site should read like the control software Felix builds evidence around: engineering
surfaces, mono data labels, restrained signal colors, live-feeling instrumentation.

### Tokens

- Base background `#05080f`; elevated surface `#0b1220`; card `rgba(15,23,42,.55)`.
- Hairlines `rgba(148,163,184,.14)`; blueprint grid texture (48px hairline grid, masked).
- Text: `#e8edf7` primary, `#8fa1bb` secondary.
- Signals: amber `#fbbf24` (attention/CTA/bottleneck), emerald `#34d399` (improvement
  deltas only), steel blue `#60a5fa` (links/structure). Never decorative rainbow.
- Type: Geist Sans display (tracking-tight); Geist Mono for all data, eyebrows, labels
  (uppercase, tracking 0.18em, 11-12px).

### Motion System

- Reveal on scroll: opacity + y + slight blur, 0.5-0.7s, easeOut, once, staggered.
- Count-up/count-down metrics (rAF, easeOutExpo, ~1.4s, trigger in view): time metrics
  count DOWN (40→<1 min, 3→1 day) because improvement is reduction; percentage and saving
  count UP (0→90%, 0→20,000).
- Hero console: looping CSS/SVG production-line animation — parts flowing through stations,
  amber-pulsing bottleneck, utilization bars, ticking mono clock. Labeled "synthetic line
  demo". This replaces static hero screenshots and stands in for video (lightweight,
  always-on, on-brand; real screen recordings can be added later).
- Status ticker: thin mono marquee of outcome readouts under the hero (CSS keyframe loop).
- Project map: progress line draws across the 10 stages on scroll (useScroll + scaleX).
- All motion gated by `prefers-reduced-motion` (final states render immediately).

## Evidence Screenshots (public/evidence)

Recaptured 2026-07-04 via Playwright + system Edge at 1600×1000@2x from the public GitHub
Pages, UI switched to English (takt simulator via its `FactoryTaktAgent.runCommand`
`updateSettings` bridge; notice/excel pages via their EN toggles). Simulator captured with
side panels collapsed, full-line template loaded, simulation at t=90s so counters are live.

- `takt-simulator-workbench.png` — running English workbench (primary takt case visual)
- `takt-simulator-product.png` — product page hero (backdrop swapped to the EN workbench)
- `notice-workbench-product.png` / `notice-output.png` — notice product page / artifact
- `excel-ops-product.png` / `excel-workbench-product.png` — excel product page / mockup
- `ops-platform-product.png` — ops platform product hero

Screenshots are shown inside a browser-chrome frame component with the live URL in the
address bar (uniform crop, authentic context).

## Page Blueprint (home)

1. Nav (fixed, blur, mobile menu, Email CTA)
2. Hero: mono positioning eyebrow → H1 "Manufacturing project chaos, turned into measurable
   improvement." → summary → CTAs → HeroConsole (animated line) on the right
3. Status ticker (outcome readouts)
4. Impact metrics (4 cards, count animation, before→after)
5. Full-cycle project map (10 stages, scroll progress line)
6. Case studies (3 alternating rows: ghost numeral, outcome chips, framed screenshot)
7. Portfolio Lab (framed product shots grid + boundary notes)
8. Methodology (4 numbered pillars)
9. About + confidentiality
10. CTA band + Footer

Case detail pages share the same system: breadcrumb band, metric chips with count
animation, problem/role, methods/actions, animated before/after, outcomes, framed evidence,
case-specific confidentiality, next-case pagination.

## Component Inventory

`SiteNav` `SiteFooter` `HeroConsole` `StatusTicker` `CountUp` `Reveal` `SectionHeading`
`MetricCard` `ProjectMap` `ScreenshotFrame` `CaseShowcase` `PortfolioCard`
`MethodologyGrid` `BeforeAfterWorkflow` `ConfidentialityNotice` `CTA` `CaseStudyDetail`

## Copy Rules (unchanged)

Tone guide, wording guards ("estimated", "around"), confidentiality texts, and
manufacturing-first positioning from docs/CONTENT_STRATEGY.md still bind every section.

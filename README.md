# Felix Manufacturing Portfolio

Independent portfolio website for Felix Zuo.

This is not a conventional developer portfolio. It presents Felix as a manufacturing project coordination and digital process improvement professional, with public sanitized evidence for trial production improvement, production notice standardization, and supply-production-delivery visibility.

## Positioning

Core identity:

> Manufacturing Project Coordination & Digital Process Improvement

The site emphasizes:

- manufacturing project coordination
- trial production and changeover improvement
- production notice workflow standardization
- supply-production-delivery visibility
- PPAP and launch readiness support
- DFMEA-related follow-up
- audit support and corrective action closure
- Lean/Six Sigma thinking and PDCA
- practical digital tools as evidence, not as the main identity

## Key Pages

- `/` - pre-rendered one-shot manufacturing journey with eight scroll-directed chapters, impact metrics, case studies, public tools, and contact actions.
- `/case-studies/production-notice-workflow-standardization`
- `/case-studies/trial-production-takt-simulation-changeover-improvement`
- `/case-studies/supply-production-delivery-operations-visibility`

## Content Model

Structured content lives under `src/data`:

- `profile.ts`
- `metrics.ts`
- `caseStudies.ts`
- `portfolioProjects.ts`
- `methodology.ts`
- `navigation.ts`

Core UI components live under `src/components`.

The homepage Blender pipeline, review gate, and encoding commands live under
`production/`. Visitors receive scrubbed H.264 video and accessible HTML rather
than a real-time 3D renderer.

## Public Data Boundary

All public-facing content uses sanitized or synthetic data. Do not add customer names, private BOMs, supplier records, internal ERP/WMS/MES exports, production routes, machine parameters, shipment data, or confidential factory files.

## Development

```powershell
npm install
npm run dev
```

Build and lint:

```powershell
npm run lint
npm run build
```

## Evidence Sources

Screenshots in `public/evidence` are captured in English from the live public GitHub Pages
demos at a uniform 16:10 viewport (see `docs/REDESIGN_SPEC.md` for the capture method).

Primary public evidence:

- Factory Takt Simulator
- Structured Operations Notice Workbench
- Factory Excel Ops Dashboard

Supporting public evidence:

- Operations Intelligence Platform
- Factory Data Pocket Lab
- Six Sigma Study App
- HulunGuard

BOM/material readiness is represented through public synthetic examples in v1. A dedicated BOM toolkit should not be presented as public evidence until it is public and data-safety reviewed.

## Handoff Files

- `docs/DISCOVERY_REPORT.md`
- `docs/CONTENT_STRATEGY.md`
- `docs/PROJECT_PLAN.md`
- `CLAUDE_BRIEF.md`
- `AGENTS.md`

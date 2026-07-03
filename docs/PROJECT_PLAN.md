# Project Plan

## Recommended Stack

- Next.js App Router
- TypeScript
- Tailwind CSS
- Framer Motion for subtle reveal only
- Static content-first architecture
- Data-driven content under `src/data`
- Vercel-ready deployment

The project should be mostly static. It does not need a database, login, API routes, or server actions for v1.

## Site Architecture

```text
src/app
  layout.tsx
  page.tsx
  case-studies/[slug]/page.tsx
  not-found.tsx
src/components
  Hero.tsx
  MetricCard.tsx
  ProjectMap.tsx
  CaseStudyCard.tsx
  CaseStudyDetail.tsx
  PortfolioProjectCard.tsx
  MethodologyGrid.tsx
  ConfidentialityNotice.tsx
  CTA.tsx
  SectionHeader.tsx
  Timeline.tsx
  BeforeAfterWorkflow.tsx
src/data
  profile.ts
  metrics.ts
  caseStudies.ts
  portfolioProjects.ts
  methodology.ts
  navigation.ts
```

## Page Structure

### Home

Sections:

1. Hero
2. Impact metrics
3. Full-cycle manufacturing project map
4. Featured case studies
5. Portfolio Lab
6. Methodology
7. About
8. Resume/contact CTA
9. Confidentiality note

### Case Study Detail Pages

Routes:

- `/case-studies/production-notice-workflow-standardization`
- `/case-studies/trial-production-takt-simulation-changeover-improvement`
- `/case-studies/supply-production-delivery-operations-visibility`

Each page includes:

- Problem
- Role
- Methods
- Actions
- Outcome metrics
- Before/after workflow
- Public portfolio evidence
- Confidentiality note

## Component Plan

| Component | Responsibility |
| --- | --- |
| `Hero` | First-screen positioning, short promise, primary CTAs, hero evidence panel. |
| `MetricCard` | Stable metric cards with label, value, context, and source note. |
| `ProjectMap` | Full-cycle launch-to-delivery timeline. |
| `CaseStudyCard` | Homepage summaries for the three primary cases. |
| `CaseStudyDetail` | Reusable detail layout for case pages. |
| `PortfolioProjectCard` | Evidence cards with repository/live links, category, maturity, and caution notes. |
| `MethodologyGrid` | Four methodology pillars with concise lists. |
| `BeforeAfterWorkflow` | Compact before/after process diagrams. |
| `ConfidentialityNotice` | Reusable public data boundary statement. |
| `CTA` | Resume/contact section. |
| `SectionHeader` | Consistent section headings and eyebrow labels. |

## Data Model

### `profile.ts`

- Name
- Role headline
- Summary
- Contact links
- Resume status
- Career directions
- Confidentiality statement

### `metrics.ts`

- id
- value
- label
- detail
- source case
- wording guard

### `caseStudies.ts`

- slug
- title
- subtitle
- problem
- role
- methods
- actions
- outcomes
- before workflow
- after workflow
- evidence project ids
- confidentiality note

### `portfolioProjects.ts`

- id
- tier
- title
- description
- repository URL
- live URL
- evidence role
- stack
- maturity
- data boundary
- linked case studies
- caution note

### `methodology.ts`

- pillar id
- title
- summary
- practices
- related evidence

### `navigation.ts`

- label
- href
- section anchor
- route type

## Visual Direction

The site should feel like a premium manufacturing project review deck and industrial control room:

- Dark graphite and deep navy foundation.
- Off-white content surfaces.
- Steel blue for structure.
- Amber for risk/review signals.
- Green for improvement outcomes.
- Dense but readable dashboards, metric cards, process maps, and before/after diagrams.

Avoid a one-note palette. Use restrained contrast and real evidence surfaces rather than decorative blobs or generic hero art.

## Asset Strategy

Use existing public-safe repository screenshots where available:

- Factory Takt Simulator screenshots under `docs/showcase/screenshots`.
- Factory Excel Ops Dashboard product page and local dashboard screenshots if available.
- Operations Intelligence Platform screenshots under `docs/assets/screenshots`.
- Six Sigma Study App screenshots from README can remain as links or be used later if public licensing is reviewed.

For v1, prioritize CSS-built process diagrams and evidence cards. Copy only known sanitized screenshots into the site if the source repository explicitly marks them public-safe.

## Implementation Milestones

### Milestone 1: Foundation

- Scaffold Next.js app in `SUM`.
- Add Tailwind and Framer Motion.
- Establish metadata and global theme.
- Create `README.md` and `AGENTS.md`.

### Milestone 2: Data Model

- Create `src/data` files for profile, metrics, case studies, portfolio projects, methodology, and navigation.
- Keep public links and confidentiality notes in data files.

### Milestone 3: Homepage

- Build hero, metrics, project map, featured case studies, Portfolio Lab, methodology, about, CTA, and confidentiality sections.
- Keep first viewport outcome-focused.

### Milestone 4: Case Detail Pages

- Build static case-study routes.
- Add before/after workflow diagrams and evidence cards.
- Add not-found handling for invalid slugs.

### Milestone 5: Documentation And Handoff

- Update `CLAUDE_BRIEF.md` with implemented structure.
- Add README usage and validation commands.
- Add AGENTS guidance from the Start Prompt.

### Milestone 6: Validation

- Run formatting/lint/build checks.
- Start local dev server.
- Verify home route and case routes in browser.
- Check responsive layout on desktop and mobile.

## Validation Steps

Minimum v1 validation:

```powershell
npm run lint
npm run build
npm run dev
```

Browser verification:

- Home page loads with meaningful content.
- No framework error overlay.
- No horizontal overflow on mobile.
- Navigation links work.
- Case detail pages render all three case studies.
- External GitHub/Pages links are present.

Content validation:

- No customer names.
- No private BOMs or supplier records.
- No internal ERP exports.
- No real production routes or machine parameters.
- RMB savings use "estimated".
- Operations Intelligence Platform is called a concept demo.
- BOM Knowledge Base is not shown as public evidence while private.


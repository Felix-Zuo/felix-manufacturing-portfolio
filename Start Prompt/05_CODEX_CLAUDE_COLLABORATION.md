# Codex And Claude Collaboration Plan

## Purpose

This project will use Codex and Claude together.

Codex should lead the codebase setup, repository inspection, implementation, build validation, component structure, data model, and technical handoff.

Claude will later join as a storytelling, design-strategy, and narrative-review collaborator.

This file is a collaboration guide, not a rigid restriction system. Use reasonable judgment.

## Codex First Responsibilities

Codex should:

1. Read all documents in `start-prompt/`.
2. Review Felix's GitHub profile and relevant repositories.
3. Create discovery and planning docs before coding.
4. Build a clean v1 codebase.
5. Keep content data-driven.
6. Create a useful `CLAUDE_BRIEF.md`.
7. Leave the project easy for another AI collaborator to inspect.

## Codex Discovery Work

Before implementation, create:

- `docs/DISCOVERY_REPORT.md`
- `docs/CONTENT_STRATEGY.md`
- `docs/PROJECT_PLAN.md`
- `CLAUDE_BRIEF.md`

The discovery report should include:

- What Felix's GitHub profile currently says
- Which repositories matter most
- Which screenshots/product pages can be used as portfolio evidence
- Which claims are safe
- Which claims need careful wording
- Recommended homepage hierarchy
- Recommended case-study order

## Claude Later Responsibilities

Claude should later review:

- Narrative clarity
- Case-study storytelling
- Visual hierarchy
- Recruiter readability
- Manufacturing-professional credibility
- Whether the site is too technical or too vague
- Whether claims are supported by evidence
- Whether wording creates accidental overclaims

Claude should not rewrite the whole codebase by default. It should first inspect:

- `CLAUDE_BRIEF.md`
- `docs/DISCOVERY_REPORT.md`
- `docs/CONTENT_STRATEGY.md`
- Current app structure
- Main pages
- Content data files

## Handoff Brief Requirements

`CLAUDE_BRIEF.md` should include:

- Project positioning
- Current architecture
- Key pages and components
- Current content model
- Main case studies
- Main evidence links
- Visual direction
- Open questions
- Suggested next improvements

## Working Style

Codex should prefer:

- Small clear milestones
- Reusable components
- Structured data files
- Readable code
- Build/test checks
- Concise documentation
- Evidence-first content
- Future extensibility

Claude should prefer:

- Clearer storyline
- Better headlines
- Stronger case-study framing
- Cleaner first-screen impact
- Better reader flow
- Stronger business value language

## Content Hierarchy

Keep the portfolio centered on:

1. Manufacturing project coordination
2. Process improvement
3. Trial production and changeover improvement
4. Production notice workflow standardization
5. Supply-production-delivery visibility
6. Public synthetic-data tool evidence

Digital tools are part of the proof. They should not bury the manufacturing story.

## Useful Project Files To Maintain

Recommended files:

- `README.md`
- `AGENTS.md`
- `CLAUDE_BRIEF.md`
- `docs/DISCOVERY_REPORT.md`
- `docs/CONTENT_STRATEGY.md`
- `docs/PROJECT_PLAN.md`
- `docs/CASE_STUDY_NOTES.md`
- `docs/CHANGELOG.md`

Recommended content files:

- `src/data/metrics.ts`
- `src/data/caseStudies.ts`
- `src/data/portfolioProjects.ts`
- `src/data/methodology.ts`
- `src/data/profile.ts`
- `src/data/navigation.ts`

## Collaboration Note For Claude

When Claude joins, give it this instruction:

> You are joining as a portfolio storytelling and design strategy reviewer. First inspect the current project structure, README, CLAUDE_BRIEF.md, discovery docs, and content data. Then propose improvements to narrative clarity, visual hierarchy, case-study impact, and recruiter readability. Keep Felix's positioning centered on manufacturing project coordination, process improvement, and measurable outcomes. Digital tools and AI-assisted development should support the story, not dominate it.

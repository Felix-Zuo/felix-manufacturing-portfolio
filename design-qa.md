# Goal 2 Design QA

Date: 2026-07-22

## Scope

Five-zone factory project hub at `/#control`, preserving the accepted cinematic
control-room environment and the existing portfolio design language.

## Visual Truth

- Source state: `production/renders/browser-qa/v16-goal2-before/control-deck-1280x720.jpg`
- Final desktop overview: `production/renders/browser-qa/v16-goal2-work/08-overview-desktop-final.jpg`
- Final desktop project state: `production/renders/browser-qa/v16-goal2-work/09-planning-desktop-final.jpg`
- Final mobile overview: `production/renders/browser-qa/v16-goal2-work/05-overview-mobile-v2.jpg`
- Final mobile project state: `production/renders/browser-qa/v16-goal2-work/04-wip-mobile.jpg`
- Full comparison: `production/renders/browser-qa/v16-goal2-compare/full-desktop-side-by-side.jpg`
- Focused comparison: `production/renders/browser-qa/v16-goal2-compare/lower-third-side-by-side.jpg`

Desktop comparisons use the same 1280 x 720 viewport and the same control-room
film state. Mobile validation uses a 390 x 844 viewport.

## Fidelity Review

- Typography: existing sans-serif and industrial monospace hierarchy retained;
  project names now receive the strongest lower-third emphasis.
- Spacing and layout: the factory remains the dominant layer; five labels occupy
  real scene zones and the briefing stays below the primary machinery sightline.
- Colors and tokens: black metal, hairline gray, amber signals, and white type
  reuse the established control-room palette without introducing a new theme.
- Image quality: the accepted control-room loop remains uncropped and continuously
  visible; no placeholder or newly synthesized scene asset was introduced.
- Copy and content: all five supplied management projects are represented with a
  distinct operating scope, outcome signal, and three concise project signals.

## Interaction Review

- Scene hotspots and the bottom project rail select the same project state.
- Direction keys move focus spatially between scene zones; Enter selects.
- Home and End move to the first and final scene zones.
- Escape returns from a project to the overview, then from the overview to the
  cinematic journey.
- Direct `/#control` loading starts the ambient film without a user gesture.
- Reduced-motion mode pauses the film and removes nonessential transitions.
- The film continues playing while project selection changes.
- Desktop and 390 px mobile states have zero horizontal overflow.
- Browser console inspection returned no warnings or errors.

## Comparison History

### Iteration 1

The first mobile overview left too much empty space below the scene, hotspot labels
were too small, and a direct `/#control` visit could leave the background film
paused because of an autoplay timing race.

### Iteration 2

Added a compact overview lower third, increased hotspot and rail label legibility,
and replayed the ambient loop from its `canplay` event. The second desktop/mobile
comparison found no P0, P1, or P2 visual or interaction issues.

final result: passed

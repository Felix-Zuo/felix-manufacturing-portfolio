# Cinematic Quality Gate

The full render does not start until an independent visual reviewer marks the
storyboard as `PASS`. A failed category returns to the owning production role.

Current gates:

- Film: **PASS** in `production/reviews/storyboard-round-5-motion.md`.
- Website: **PASS FOR RELEASE** in `production/reviews/website-round-1.md`.

## Modeling

- The robot reads as a credible six-axis industrial arm at first glance.
- Joint housings, flanges, fasteners, cable routing, base mounting, and end
  tooling are visible at the intended camera distance.
- Bearing proportions are mechanically plausible: race thickness, cage, ball
  count, clearances, and inner/outer ring scale do not collide or deform.
- The grinding cell has a clear enclosure and one understandable operation.
- Screens, rails, frames, and machines have visible mounting logic and scale.
- No unexplained floating parts or decorative mechanical clutter remain.

## Composition

- The twin rail is the dominant visual guide throughout the journey.
- Each chapter has one primary subject and one secondary evidence layer.
- Felix Zuo appears as a restrained environmental signature, never a billboard.
- Desktop and mobile crops preserve the subject and leave safe space for copy.
- Project evidence remains legible and is not stretched, cropped, or obscured.

## Camera And Motion

- The complete 28-second route is one continuous camera move with no cuts.
- Position, aim, focal length, and roll transitions have continuous velocity.
- Bullet-time moments slow the action without visibly stopping the camera.
- Robot, bearing, grinding wheel, sparks, and screens maintain spatial continuity.
- No chapter transition causes a jump, collision, wall clip, or sudden focus hunt.

## Look Development

- The workshop reads bright, clean, controlled, and premium rather than dark sci-fi.
- Black levels retain structural detail; white shells retain surface form.
- Brushed metal, painted steel, rubber, glass, and emissive screens are distinct.
- Amber signals and sparks guide attention without turning the palette orange.
- Bloom, depth of field, motion blur, and atmosphere never hide evidence content.

## Web Experience

- The home page ships no real-time 3D renderer or Three.js scene.
- A poster appears immediately while the correct video source loads.
- Scroll smoothly maps to video time and chapter controls remain operable.
- Keyframes are close enough for responsive seeking on desktop and mobile.
- Reduced motion uses a static poster and direct chapter navigation.
- All project links, email, GitHub, keyboard focus, and mobile navigation work.
- No horizontal overflow, layout overlap, hydration errors, or console errors remain.

## Acceptance

- Eight desktop storyboard frames reviewed at a consistent viewport.
- Four representative mobile storyboard frames reviewed at 9:16.
- Independent reviewer reports zero blocking or major findings.
- Lint, production build, desktop browser QA, mobile browser QA, and reduced-motion
  QA all pass before deployment.

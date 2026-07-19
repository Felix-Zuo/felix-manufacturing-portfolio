# Design QA

## Comparison Target

- Source visual truth: `C:\Users\左雅轩\.codex\generated_images\019f2880-3dda-79f1-abbe-c0ec53b8f387\exec-061af77c-fd06-4620-abfb-f2f6aa3d9340.png`
- Implementation: `http://127.0.0.1:3000/`
- Desktop implementation evidence: `D:\0A OpenClaw\projects\展示项目\SUM\.codex\cinematic-redesign\v4-desktop-final.png`
- Desktop project-state evidence: `D:\0A OpenClaw\projects\展示项目\SUM\.codex\cinematic-redesign\v4-desktop-notice-final.png`
- Mobile evidence: `D:\0A OpenClaw\projects\展示项目\SUM\.codex\cinematic-redesign\v4-mobile-top.png` and `D:\0A OpenClaw\projects\展示项目\SUM\.codex\cinematic-redesign\v4-mobile-notice-final.png`
- Viewports: 1440 x 1024 desktop; 390 x 844 mobile
- States: entry frame, grinding bullet-time frame, case-study project frame, reduced-motion chapter navigation
- Current streamed-cinematic comparison: `production/renders/browser-qa/v12-interaction-audit/21-production-local-comparison.png`
- Current mobile evidence: `production/renders/browser-qa/v12-interaction-audit/15-mobile-notice.png` and `production/renders/browser-qa/v12-interaction-audit/16-mobile-control-deck.png`

## Comparison Evidence

- Full-view comparison: `D:\0A OpenClaw\projects\展示项目\SUM\.codex\cinematic-redesign\design-comparison.png`
- Focused project-frame comparison: `D:\0A OpenClaw\projects\展示项目\SUM\.codex\cinematic-redesign\design-comparison-project-sharp.png`
- The focused comparison was required because the source direction's key fidelity surfaces are screen scale, arm placement, rail depth, and foreground/background separation.

## Findings

- No actionable P0, P1, or P2 findings remain.
- [P3] The implementation deliberately uses less factory background density than the generated source. This follows the selected-direction feedback: remove ambiguous machinery, reduce element accumulation, and retain a single rail-led visual path.
- [P3] The generated source uses a conspicuous architectural `Felix Zuo` sign. The implementation reduces the name to navigation and a low-contrast entry caption, matching the requested restraint.

## Required Fidelity Surfaces

- Fonts and typography: Geist/Geist Mono create a controlled industrial hierarchy. Desktop and mobile headings wrap without clipping; letter spacing remains zero; small labels remain legible.
- Spacing and layout rhythm: the fixed viewport keeps HUD controls stable while the camera moves. Desktop captions alternate away from the active screen. Mobile captions collapse to one safe lower region with no horizontal overflow.
- Colors and visual tokens: graphite, steel blue, restrained amber, and emerald status accents match the established portfolio system. Bloom and chromatic aberration are intentionally subtle.
- Image quality and asset fidelity: all project screens use the real 1920 x 1200 public evidence images. No placeholder product imagery, custom SVG illustration, or generated machine interior is used.
- Copy and content: all eight chapters preserve the manufacturing narrative, measurable outcomes, three primary cases, connected systems, and contact path.
- Icons: Lucide controls are consistently sized and labelled. Chapter, menu, hotspot, and return controls expose unique accessible names.
- Accessibility and behavior: focus-visible styling remains global; reduced motion compresses the experience to one viewport and changes chapter controls into direct scene selection; mobile removes the arm where it would occlude content.

## Comparison History

1. Initial implementation pass
   - Earlier P1: camera intersected the grinding enclosure and project screens filled almost the entire viewport.
   - Earlier P2: spark particles became oversized squares and bloom obscured the scene.
   - Fixes: moved the grinding cell off the camera path, reduced spark count/size/light intensity, lengthened the rear camera path, moved project rigs 10-16 world units ahead, reduced screen size, and lowered bloom.
   - Post-fix evidence: `v4-desktop-process-final.png`, `v4-desktop-notice-final.png`.

2. Responsive and interaction pass
   - Earlier P2: the arm crossed the project screenshot and became disconnected-looking on mobile.
   - Earlier P2: the home footer extended the reduced-motion page beyond one viewport.
   - Fixes: side-mounted and rescaled the desktop arm, removed it below 700 px, conditionally removed the footer on the home route, and added direct reduced-motion chapter selection.
   - Post-fix evidence: `v4-desktop-notice-final.png`, `v4-mobile-notice-final.png`; browser check reports 390 px viewport with no horizontal overflow and reduced-motion scroll height equal to viewport height.

## Interaction Verification

- The main 20 MB journey video now uses native browser streaming; only the smaller control-room and evidence media use the Blob preloader.
- Five rapid wheel inputs reached the next chapter and settled in about 1.5 seconds instead of accumulating roughly five seconds of playback debt.
- Chapter copy remains present during movement and crossfades continuously at chapter midpoints; there is no magnetic input lock or blur-on-scroll state.
- The contact-to-control-room transition follows the final rendered frames, fades through black, and transfers interaction in about 1.2 seconds. The reverse transition also follows the same timeline.
- The control room opens with Release selected, keeps selected hotspots visible, and exposes the mapped project screen, links, contact, replay, and keyboard return behavior.
- 390 x 844 mobile checks passed for entry, project, menu, and control-room states with no horizontal overflow.
- Browser checks reported no runtime errors. `npm run lint`, `npx tsc --noEmit`, and `npm run build` passed.

## Follow-up Polish

- P3 only: tune the desktop entry spotlight after deployment if the production GPU tone mapping differs materially from local rendering.

final result: passed

# V7 Interactive Factory Finale

## Intent

V7 keeps the 38-second rendered one-shot as the visual source of truth. HTML is
used only where it is stronger than baked pixels: crisp project cards, pointer
feedback, scene hotspots, accessibility, links, and the final portfolio summary.

The factory must read as one engineered system rather than a collection of props.
Every added object needs a process purpose, a service route, and a clear visual
relationship to the camera path.

## Industrial reference rules

- Grinder architecture follows the enclosed, production-line-ready proportions of
  modern LIDKOPING bearing grinders: compact powder-coated enclosure, service
  panels, guarded process aperture, rigid short spindle path, and surrounding
  automation. Reference: https://www.uvalidkoping.com/
- The raceway operation remains physically legible: the bearing ring is located by
  its fixture, a small CBN wheel enters radially on a short straight quill, coolant
  reaches the contact zone, and return flow drains below the work envelope.
- The overhead transfer uses the visual grammar of an industrial external axis:
  modular beam sections, compact carriage, motor/gearbox, covered guides, cable
  carrier, vertical slide, and end effector. KUKA documents these serviceable,
  modular features for its KL linear units:
  https://www.kuka.com/en-us/products/robotics-systems/robot-periphery/linear-units
- Cylindrical parts use a compact centric gripper, not an improvised claw. The
  reference geometry is a sealed three-jaw unit with synchronized jaws and custom
  fingers, consistent with SCHUNK EZU and Zimmer GD/GPD families:
  https://schunk.com/us/en/gripping-systems/centric-grippers/ezu/c/PGR_7387
  https://www.zimmer-group.com/en-us/products/components/handling-technology/3-jaw-concentric-grippers/series-gd300

These are visual and engineering references only. No vendor marks or proprietary
CAD are copied into the public scene.

## One-shot beat map

| Frames | Camera purpose | Process action | Web layer |
| --- | --- | --- | --- |
| 001-130 | Locked bearing macro, then a slow release | Ring rotates subtly; metrology light sweeps the raceway | Identity card grows from the ring datum |
| 131-192 | Rise and move closer to the guarded robot cell | Robot presents a ring; gripper and dress pack settle | Robot/gripper hotspot |
| 193-260 | Look diagonally through the overhead transfer depth | Carriage carries a WIP ring; Z slide and drag chain follow | Gantry hotspot |
| 261-385 | Arc past the grinding contact with controlled bullet time | Small CBN wheel feeds radially; ring counter-rotates; coolant and restrained sparks identify contact | Grinding hotspot and process callout |
| 386-835 | Four evidence bays, each with a distinct approach angle | HMI practicals, transfer hardware, and status lamps remain active | Card projects from the active screen; link is interactive |
| 836-900 | Re-center on the final interlocked door | Door leaves separate while local light falls by more than two stops | Physical black threshold |
| 901-912 | Hold only long enough to complete the handoff | No white flash and no emissive field | Dark summary resolves from black |

The camera may pan or tilt, but its main rail position remains monotonic. The
central service aisle and all safety clearances stay unobstructed.

## Factory systems

### Machine cells

- Use two or three coherent enclosure families, not identical boxes and not a new
  design for every station.
- Each enclosure gets a readable base plinth, leveling pads, panel seams, captive
  fasteners, guarded window, handle/interlock, status tower, HMI arm, and one
  plausible service side.
- Interior detail is concentrated only where the camera can inspect it: fixture,
  ring datum, wheel guard, quill, nozzles, dresser, work light, drain tray, and
  coolant splash. Hidden geometry does not earn render time.

### Inter-machine services

- A continuous overhead ladder tray carries power and controls.
- Separate color-neutral drops feed each cell through a short energy chain or
  flexible conduit. Coolant supply and return remain low and physically separated
  from electrical routing.
- Repeated brackets, union fittings, valve blocks, floor trenches, and tagged drops
  establish scale. Routes must terminate at equipment instead of floating.

### Overhead material handling

- Twin longitudinal beams span the machine row without crossing the service aisle
  below head height.
- The carriage includes guide wheels, motor/gearbox, covered rail interface, cable
  chain, vertical Z slide, limit sensors, and a compact centric gripper.
- One visible bearing ring is transported. Motion has acceleration, travel,
  controlled deceleration, vertical settle, and hold; it never drifts or intersects
  the camera, fence, or machine roof.

## Web interaction contract

- Wheel and touch continue to control timeline progress continuously. No document
  scroll is introduced before the final handoff.
- A standard 100-120 px wheel event advances only 0.45-0.52 seconds. The four
  project focus frames, `F433/F553/F673/F793`, are bidirectional magnetic stops:
  arrival lands on the exact frame, a short dwell rejects event bursts, and a
  subsequent deliberate input releases the timeline.
- Project cards are DOM overlays and remain sharp. On chapter entry they originate
  at the active HMI coordinate, open through a perspective/clip reveal, overshoot
  once by less than 3%, then settle.
- A thin projection line and screen pulse visually connect the rendered display to
  the card. The effect lasts under one second and does not loop.
- Chapter-local hotspots cover the bearing, overhead carriage, robot gripper,
  grinding contact, and four evidence screens. Hover supplies one concise technical
  fact; click either pins the fact or follows the project link.
- Desktop pointer feedback is a small industrial focus reticle with magnetic pull
  only near hotspots. It must not replace the OS cursor over links or controls.
- Mobile uses larger invisible hit areas, no custom cursor, no hover dependency,
  and the portrait master.
- Reduced-motion mode removes spring motion, pointer trails, and animated projection
  lines while preserving every link and fact.

## Finale

The rendered door opens during the last two seconds as the nearby environment dims.
A very narrow low-energy seam disappears with the physical leaves, revealing a
non-emissive, near-black threshold. The DOM holds black briefly, then resolves into
a normal dark full-screen portfolio summary rather than another floating card.

The summary contains:

- Felix Zuo identity and manufacturing-operations positioning.
- A compact project timeline with the four evidence points.
- Measurable outcome highlights.
- Public work, GitHub, and email actions.
- A replay control that returns to frame 1 without reloading the page.

## Acceptance gates

- Actual media: 912 frames, 24 fps, 38.000 seconds, BT.709, yuv420p.
- Web masters are rendered at no less than 1280 x 720 desktop and 720 x 1280
  mobile, every source frame, with 64 Eevee samples. No half-rate interpolation is
  accepted for the published version.
- Web encode uses H.264 CRF 17, fixed GOP 12, and frame 1 as the poster.
- Frame 1 is a bearing macro. Home/replay returns to frame 1.
- At least one camera beat includes the moving overhead transfer system.
- Grinder contact remains process-correct in audit frames.
- Each project screen owns one card origin and one accessible interactive target.
- Door leaves visibly open before the DOM summary takes over.
- The door reveals black; audit frames contain no whiteout or bright full-frame
  transition.
- Every focus hold retains meaningful process motion: rotating work, coolant,
  transfer motion, HMI practicals, or status indication. Camera speed may ease but
  the factory may not become a static still.
- Desktop 1440x900 and mobile 390x844 have zero horizontal overflow.
- `prefers-reduced-motion`, keyboard, touch, and media failure fallback all work.
- Blender camera validation, lint, production build, browser console, and privacy
  scans pass before publishing.

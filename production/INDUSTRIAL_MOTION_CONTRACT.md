# Industrial Motion Contract

This contract defines behavior that must be true in geometry and animation,
not merely plausible in a still image.

## Chapter Playback

- An adjacent click plays one authored camera transition forward to the next
  chapter.
- At the chapter anchor, the camera has no animated transform, lens, focus, or
  target. Only scene objects animate.
- Back one chapter plays a separately authored reverse transition when one
  exists. Non-adjacent jumps use a covered dissolve and direct seek.
- No hold may be manufactured by forward/reverse concatenation.
- A loop's last frame is the same physical state as its first frame. A duplicate
  terminal frame is omitted from encoding to avoid a visible pause.

## Robot Pick-Place Cycle

Workpiece orientation: bearing rings lie flat in a located conveyor nest. They
do not balance vertically on the belt.

Required state sequence:

1. `HOME`: robot clear of conveyor, fence, machine, and aisle.
2. `APPROACH_PICK`: tool center point above the ring with a vertical clearance.
3. `PICK`: slow vertical approach; fingers close around a defined surface.
4. `LIFT`: ring becomes constrained to the tool only after the grasp closes.
5. `TRANSFER`: collision-checked motion above all fixed geometry.
6. `APPROACH_PLACE`: tool center point above the receiving nest.
7. `PLACE`: slow insertion; ring becomes constrained to the nest before release.
8. `RETRACT`: vertical clearance before lateral motion.
9. `RETURN`: robot returns to the exact `HOME` transform.
10. `INDEX`: conveyor advances the next flat ring only after the robot clears it.

Acceptance measurements:

- Minimum moving-mesh clearance from belt, guard, machine shell, and fixture:
  30 mm, except at the authored grasp/contact surfaces.
- Workpiece world transform follows the conveyor before grasp, the tool during
  transfer, and the destination after release. Visibility swaps are forbidden.
- End-effector motion is continuous in position and orientation. No hand-tuned
  joint table may be accepted without a solved target path and collision audit.
- The fixed-camera loop is 4-6 seconds and tells one complete loading action.

## Raceway Grinding Cycle

- The work spindle axis is horizontal in the machine coordinate system.
- The outer ring is clamped coaxially to the work spindle; its plane is vertical
  because its axis is horizontal.
- The small profiled CBN wheel enters the bore on a separate horizontal spindle
  and contacts the inner raceway, not the outer diameter or broad ring face.
- A non-symmetric witness mark must make workpiece rotation visually verifiable.
- Spindle axes are derived from evaluated world transforms and compared with the
  modeled shaft centerlines. Metadata alone is not evidence.

Fluid and contact behavior:

- Coolant begins before wheel contact and remains directed at the contact zone.
- The stream breaks into a coherent sheet, droplets, splash, and fine mist after
  striking rotating geometry. It must not read as a breathing tube or scaled
  solid sheet.
- Wet grinding permits sparse short-lived sparks at the exact contact tangent.
  Welding-like showers are forbidden.
- Wheel surface blur and the workpiece witness mark must show different spindle
  speeds while preserving the contact geometry.
- The fixed camera does not move during the 3-4 second loop.

## Material Gate

Every foreground asset requires physically based base color, roughness, normal,
and metalness where applicable. Height/displacement is used only where scale and
silhouette justify it.

Required material families:

- white and graphite powder-coated machine panels;
- brushed and machined steel with directional response;
- black oxide and nitrided tool surfaces;
- CBN abrasive layer with separate bonded grain response;
- safety glass with believable thickness and edge tint;
- rubber conveyor belt and cable jackets;
- painted safety yellow with controlled wear at contact points;
- wet stainless interior, coolant film, droplets, and mist.

No material is approved from a shader name or thumbnail. It needs a neutral
turntable plus an in-scene close-up under the final light rig.

## Evidence Package

Each proof delivers:

- source scene and deterministic build script;
- asset/license manifest;
- axis and clearance report in JSON;
- native-resolution image sequence;
- contact sheet with at least eight evenly spaced frames;
- visually lossless review clip and web proxy;
- explicit reviewer decision: `approved`, `revise`, or `rejected`.

# V5 Asset Manifest

## Asset Policy

Use licensed geometry only when it improves silhouette, topology, or material fidelity. Keep original license records and listing URLs. Do not publish source asset files in the public website repository. Only rendered media and project-owned geometry may ship publicly.

The approved reference is `production/v5/source-frames/s01-entry-clean.png`. The visual target is a bright, clean precision-manufacturing hall with one legible center aisle, credible machinery clearances, organized services, and no decorative clutter.

## Live Library Audit - 2026-07-16

| Role | Candidate | Decision | Notes |
| --- | --- | --- | --- |
| Hero robot | [ROS-Industrial KUKA KR 210 L150](https://github.com/ros-industrial/kuka_experimental/tree/melodic-devel/kuka_kr210_support) | Adopted | Seven link meshes and the package URDF were imported at commit `8d9292b04a22628b1b78d989e2ddd3abb913bf92`. The scene uses the real A1-A6 origins and axes, about 88k source triangles, project-owned dress-pack details, and a compact servo bearing gripper. Package metadata declares BSD and the retained repository root license is Apache-2.0. |
| Environment shell | [Factory Environment Collection](https://www.fab.com/listings/2ee66462-8c2b-4303-892c-83f7fc0d9b3e) | Reference only | Mature environment, but the listing supplies Unreal Engine content rather than a direct Twinmotion interchange file. Its heavy-truck density and darker art direction conflict with the approved clean aisle. |
| Robot | [Industrial robot arm](https://www.fab.com/listings/d10b22df-74ce-4e0d-a829-40933a07bbb6) | Reject for hero | Free GLB/glTF, but the geometry and teal material treatment are too simple for the foreground. It may be used only as a distant background prop after a license record is captured. |
| AGV base | [Autonomous Mobile Manipulator](https://www.fab.com/listings/af67f4d6-bae3-4d6e-8e94-04559144f01e) | Reject | Wrong product class and proportions for the low-profile AGV in the approved reference. The listing also marks AI use as not allowed. |
| Factory modular kit | [Factory Modular Kit](https://sketchfab.com/3d-models/factory-modular-kit-3213637ed81d41138c6746a13bf585b9) | Reject | Downloadable CC Attribution geometry, but the creator explicitly marks the model `NO AI`; do not ingest it into this workflow. |

No reusable cloud asset pack is currently downloaded in the local Twinmotion Library. The current local project cache contains only the project's imported SUM geometry and materials.

## Production Asset Plan

| Role | Source | Status | Production rule |
| --- | --- | --- | --- |
| Hall architecture | Original modular Blender geometry | Build now | Portal frames, pitched roof, skylights, clerestory glazing, purlins, luminaires, pipes, cable trays, wall panels, and floor joints must follow one structural grid. |
| Machine row | Original modular Blender geometry | Build now | Repeated enclosed precision-machine bays with credible service panels, windows, HMIs, status towers, and safety clearances. Use repetition for rhythm, not random prop density. |
| AGV | Original Blender geometry | Build now | Low-profile body, protected wheels, lidar/safety sensors, light strips, and an unobstructed painted route. No raised rail or overhead obstruction. |
| Robot cell | ROS-Industrial KR 210 plus original cell infrastructure | Production ready | Black welded-mesh guarding and safety-yellow posts retain a clear transfer opening. The former procedural arm is excluded from render/export. The KR 210 has real split-link geometry, URDF pivots, six animated axes, service cables, joint hardware, and a project-owned servo gripper. |
| Bearing grinder | Original Blender process model with production-detail pass | Production ready | Mechanically reviewed horizontal work and wheel-spindle axes, a small CBN wheel entering the inner-ring raceway, B-axis pedestal, chuck/soft jaws, linear guides, bellows, spindle motor, coolant, dresser, process camera, and animated sliding doors. Do not replace it with a generic CNC asset. |
| Screens | Original geometry plus real project captures | Integrate now | Recess the display into machine architecture. The screen must remain readable in a dedicated front-on shot and use the actual project UI. |

## Reject by Default

- Abandoned, rusty, post-apocalyptic, cyberpunk, or dark sci-fi factory packs.
- Robot assets without six credible joints and usable pivots or rig.
- Generic grinding imagery that cannot reproduce the verified raceway contact.
- AGV assets with raised guide rails or structures that block the aisle.
- Any asset without a visible license or with unclear modification terms.
- Any pack whose visual complexity is mostly clutter rather than structural or process detail.

## Asset QA Gate

Every external asset must pass all checks before entering the production scene:

1. Record creator, listing ID, license, acquisition date, file format, and modification rights.
2. Inspect silhouette and scale against a human-height reference in Blender.
3. Check topology, normals, UVs, texture resolution, and material-channel naming.
4. Verify real pivots or rebuild the hierarchy before animation.
5. Produce one neutral-light turntable before placing it in the factory.
6. Keep the first cinematic render review ahead of any paid acquisition.

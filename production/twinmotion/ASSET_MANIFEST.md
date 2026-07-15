# V5 Asset Manifest

## Asset Policy

Use licensed, non-AI-generated geometry wherever a real asset exists. Keep original license records and listing URLs. Do not publish source asset files in the public website repository. Only rendered media and original project-owned geometry may ship publicly.

## Approved Starting Assets

| Role | Candidate | Status | Notes |
| --- | --- | --- | --- |
| Environment shell | [Factory Environment Collection](https://www.fab.com/listings/2ee66462-8c2b-4303-892c-83f7fc0d9b3e) | Acquire and inspect | Free Unreal pack, optimized factory sections and functional props. Use only clean modules; remove heavy-truck specificity and clutter. |
| Robot | [Industrial robot arm](https://www.fab.com/listings/d10b22df-74ce-4e0d-a829-40933a07bbb6) | Acquire and inspect | Free six-axis arm in GLB/glTF. Verify pivots, topology, PBR maps, and license before use. |
| AGV base | [Autonomous Mobile Manipulator](https://www.fab.com/listings/af67f4d6-bae3-4d6e-8e94-04559144f01e) | Acquire and inspect | Free GLB candidate. Remove the upper manipulator and reskin the mobile base only if license and topology allow modification. |
| Bearing grinder | Existing original Blender geometry | Retain and refine | Process geometry is already custom and mechanically reviewed. Replace materials and outer enclosure details; do not substitute a generic incorrect CNC asset. |
| Bearing | Existing original Blender geometry | Retain | Original rings, raceways, balls and cage. Use only in short verified process inserts. |
| Screens | Original simple geometry + website DOM | Retain | 3D render uses dark glass. Actual project UI remains live HTML/CSS in the site. |

## Reject by Default

- Abandoned, rusty, post-apocalyptic, cyberpunk, or dark sci-fi factory packs.
- Robot assets without six credible joints and usable pivots or rig.
- Generic grinding imagery that cannot reproduce the verified raceway contact.
- AGV assets with raised guide rails or structures that block the aisle.
- Any asset without a visible license or with unclear redistribution terms.

## Acquisition Gate

For each Fab asset, record creator, listing ID, selected license, acquisition date, engine/file version, and whether modifications are allowed. The first render review happens before spending money on any optional asset.

# KUKA KR 210 L150 Source Record

- Upstream: https://github.com/ros-industrial/kuka_experimental
- Package: `kuka_kr210_support`
- Upstream commit: `8d9292b04a22628b1b78d989e2ddd3abb913bf92`
- Commit date: 2025-05-28
- Imported on: 2026-07-16
- Files retained: seven visual Collada link meshes, generated URDF, package metadata, and repository license
- Purpose: foreground six-axis industrial robot geometry and kinematic reference for the Felix Zuo V5 cinematic

The package metadata declares BSD while the repository root contains Apache-2.0. Both the root license and package metadata are retained without modification. Source meshes stay in the production workspace; the public portfolio deploy receives rendered media, not these source files.

The scene importer preserves the URDF joint origins and axes, replaces only look-development materials, and adds project-owned end-effector and cable details.

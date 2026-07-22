from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class CinematicSourceContracts(unittest.TestCase):
    def test_hold_builder_does_not_create_ping_pong_camera_loops(self) -> None:
        source = (ROOT / "production" / "build_seamless_chapter_holds.ps1").read_text(
            encoding="utf-8"
        )
        self.assertNotRegex(source, re.compile(r"\breverse\b", re.IGNORECASE))
        self.assertNotIn("split=2[f][r0]", source)

    def test_camera_derived_chapter_holds_are_not_publishable(self) -> None:
        hold_root = ROOT / "public" / "media" / "holds"
        for chapter in (
            "origin",
            "impact",
            "notice",
            "takt",
            "visibility",
            "system",
            "close",
        ):
            for profile in ("desktop", "mobile"):
                with self.subTest(chapter=chapter, profile=profile):
                    self.assertFalse((hold_root / f"{chapter}-{profile}.mp4").exists())

    def test_robot_hold_does_not_fake_transfer_with_visibility_swaps(self) -> None:
        source = (ROOT / "production" / "blender" / "render_hold_loop.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("update_impact_story", source)
        self.assertNotRegex(source, re.compile(r"held_visible\s*="))

    def test_rejected_mechanical_holds_cannot_use_legacy_entrypoint(self) -> None:
        powershell = (ROOT / "production" / "render_hold_loops.ps1").read_text(
            encoding="utf-8"
        )
        renderer = (
            ROOT / "production" / "blender" / "render_hold_loop.py"
        ).read_text(encoding="utf-8")
        self.assertIn('[ValidateSet("takt")]', powershell)
        self.assertIn('args.chapter in {"impact", "process"}', renderer)

    def test_stream_builder_does_not_overwrite_holds_by_default(self) -> None:
        source = (ROOT / "production" / "build_stream_media.ps1").read_text(
            encoding="utf-8"
        )
        self.assertIn("BuildRejectedLegacyLoops", source)
        self.assertNotIn("[switch]$SkipLoops", source)

    def test_transition_builder_preserves_source_frame_rate(self) -> None:
        source = (ROOT / "production" / "build_transition_clips.ps1").read_text(
            encoding="utf-8"
        )
        self.assertIn("$OutputFrameRate = 24", source)
        self.assertNotIn("$OutputFrameRate = 30", source)

    def test_grinding_parts_declare_local_spin_axis(self) -> None:
        source = (ROOT / "production" / "blender" / "modeling.py").read_text(
            encoding="utf-8"
        )
        wheel = re.search(
            r'grinding_wheel\["rotation_axis_local"\]\s*=\s*\[([^\]]+)\]', source
        )
        workpiece = re.search(
            r'workpiece\["rotation_axis_local"\]\s*=\s*\[([^\]]+)\]', source
        )
        self.assertIsNotNone(wheel)
        self.assertIsNotNone(workpiece)
        self.assertEqual(wheel.group(1).replace(" ", ""), "0.0,0.0,1.0")
        self.assertEqual(workpiece.group(1).replace(" ", ""), "0.0,0.0,1.0")

    def test_spin_animation_uses_declared_axis(self) -> None:
        source = (ROOT / "production" / "blender" / "animation.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("_declared_spin_axis_index", source)
        self.assertNotIn(
            'obj["sum_animation_spin_axis_geometry_local"] = [0.0, 0.0, 1.0]',
            source,
        )


if __name__ == "__main__":
    unittest.main()

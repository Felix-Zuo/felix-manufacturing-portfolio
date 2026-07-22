from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src" / "components" / "CinematicPortfolio.tsx"


class CinematicPortfolioPreloadContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_start_gate_waits_for_images_not_video_buffers(self) -> None:
        self.assertIn("const criticalImages = [", self.source)
        self.assertIn("startImage(profile)", self.source)
        self.assertIn("chapterImage(CHAPTERS[0], profile)", self.source)
        self.assertNotIn("oncanplaythrough", self.source)

    def test_background_preload_tracks_current_and_neighboring_chapters(self) -> None:
        self.assertIn("function chapterNeighborhoodAssets(", self.source)
        self.assertIn("activeIndex - 1, activeIndex, activeIndex + 1", self.source)
        self.assertIn("useMediaPreloader(mediaProfile, activeIndex)", self.source)
        self.assertNotIn(
            "CHAPTERS.slice(0, -1).flatMap",
            self.source,
        )

    def test_background_video_warmup_is_not_a_readiness_gate(self) -> None:
        self.assertIn('video.preload = "auto"', self.source)
        self.assertIn("BACKGROUND_PRELOAD_DELAY_MS", self.source)
        self.assertNotIn("Promise.all(\n      assets.map", self.source)

    def test_navigation_error_fallback_remains_in_place(self) -> None:
        self.assertIn("Math.abs(targetIndex - activeIndex) !== 1", self.source)
        self.assertIn('setJumpPhase("cover")', self.source)
        self.assertIn("onError={completeJourneyMotion}", self.source)
        self.assertIn("void video.play().catch(completeJourneyMotion)", self.source)


if __name__ == "__main__":
    unittest.main()

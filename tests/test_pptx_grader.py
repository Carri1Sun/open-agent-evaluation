from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from open_agent_evaluation.graders.pptx import build_pptx_checks, inspect_pptx

from .helpers import write_minimal_pptx


class PptxGraderTests(unittest.TestCase):
    def test_inspects_pptx_structure(self):
        with tempfile.TemporaryDirectory() as raw_dir:
            directory = Path(raw_dir)
            path = directory / "deck.pptx"
            write_minimal_pptx(
                path,
                slide_texts=[
                    "Sales summary",
                    "Recommendation by region",
                ],
                chart_slides=[1],
                table_slides=[2],
                image_slides=[1],
                notes_texts=["source notes"],
            )

            stats = inspect_pptx(path)

            self.assertEqual(stats.slide_count, 2)
            self.assertEqual(stats.chart_count, 1)
            self.assertEqual(stats.table_count, 1)
            self.assertEqual(stats.image_count, 1)
            self.assertTrue(stats.is_widescreen)
            self.assertEqual(stats.speaker_notes_slides, 1)

    def test_builds_fractional_keyword_score(self):
        with tempfile.TemporaryDirectory() as raw_dir:
            path = Path(raw_dir) / "deck.pptx"
            write_minimal_pptx(path, slide_texts=["Sales summary", "Recommendation"])
            stats = inspect_pptx(path)

            checks = build_pptx_checks(
                stats,
                {
                    "required_keywords": ["sales", "recommendation", "missing"],
                    "min_slides": 2,
                },
            )

            keyword_check = [check for check in checks if check["id"] == "required_keywords"][0]
            self.assertAlmostEqual(keyword_check["score"], 2 / 3)


if __name__ == "__main__":
    unittest.main()

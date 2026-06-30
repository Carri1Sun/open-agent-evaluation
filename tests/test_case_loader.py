from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from open_agent_evaluation.case_loader import load_case
from open_agent_evaluation.models import EvaluationError

from .helpers import make_case, write_json


class CaseLoaderAssetTests(unittest.TestCase):
    def test_resolves_attachment_paths(self):
        with tempfile.TemporaryDirectory() as raw_dir:
            case_dir = Path(raw_dir)
            attachment_dir = case_dir / "attachments"
            attachment_dir.mkdir()
            attachment_path = attachment_dir / "metrics.csv"
            attachment_path.write_text("metric,value\narr,42\n", encoding="utf-8")

            case_data = make_case("slides.test.assets_v1")
            case_data["question"] = {
                "query": "Create slides from the attached metrics.",
                "browser_initial_state": {
                    "url": "about:blank",
                    "auth_state": "not_required",
                    "local_files": ["attachments/metrics.csv"],
                },
                "attachments": [
                    {
                        "name": "metrics.csv",
                        "kind": "csv",
                        "path": "attachments/metrics.csv",
                    }
                ],
            }
            write_json(case_dir / "case.json", case_data)

            case = load_case(case_dir)

            self.assertEqual(case.input["attachments"][0]["resolved_path"], str(attachment_path.resolve()))
            self.assertEqual(
                case.input["browser_initial_state"]["resolved_local_files"],
                [str(attachment_path.resolve())],
            )

    def test_rejects_missing_attachment_file(self):
        with tempfile.TemporaryDirectory() as raw_dir:
            case_dir = Path(raw_dir)
            case_data = make_case("slides.test.missing_asset_v1")
            case_data["question"] = {
                "query": "Create slides from the attached metrics.",
                "attachments": [
                    {
                        "name": "metrics.csv",
                        "kind": "csv",
                        "path": "attachments/metrics.csv",
                    }
                ],
            }
            write_json(case_dir / "case.json", case_data)

            with self.assertRaisesRegex(EvaluationError, "does not exist"):
                load_case(case_dir)

    def test_rejects_attachment_outside_attachments_directory(self):
        with tempfile.TemporaryDirectory() as raw_dir:
            case_dir = Path(raw_dir)
            (case_dir / "metrics.csv").write_text("metric,value\narr,42\n", encoding="utf-8")
            case_data = make_case("slides.test.outside_asset_v1")
            case_data["question"] = {
                "query": "Create slides from the attached metrics.",
                "attachments": [
                    {
                        "name": "metrics.csv",
                        "kind": "csv",
                        "path": "metrics.csv",
                    }
                ],
            }
            write_json(case_dir / "case.json", case_data)

            with self.assertRaisesRegex(EvaluationError, "under attachments"):
                load_case(case_dir)


if __name__ == "__main__":
    unittest.main()

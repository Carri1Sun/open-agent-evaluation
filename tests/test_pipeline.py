from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from open_agent_evaluation.pipeline import EvaluationRunner

from .helpers import make_case, write_json, write_minimal_pptx, write_submission


class PipelineTests(unittest.TestCase):
    def test_evaluates_passing_submission(self):
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            case_dir = root / "cases"
            sub_dir = root / "submissions" / "run_1"
            case_dir.mkdir()
            sub_dir.mkdir(parents=True)

            write_json(case_dir / "case.json", make_case("slides.test.case_v1"))
            write_minimal_pptx(
                sub_dir / "deck.pptx",
                slide_texts=["Sales summary", "Recommendation by region"],
                chart_slides=[1],
                table_slides=[2],
            )
            write_submission(sub_dir, "slides.test.case_v1")

            runner = EvaluationRunner.from_case_paths([case_dir])
            suite_result = runner.evaluate_submission_paths([sub_dir])

            self.assertEqual(len(suite_result.results), 1)
            result = suite_result.results[0]
            self.assertTrue(result.passed)
            self.assertGreaterEqual(result.score, 0.9)
            self.assertEqual(suite_result.metrics["capability"]["pass_at_3"], 1.0)

    def test_regression_pass_power_requires_three_passing_attempts(self):
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            case_dir = root / "cases"
            submissions_root = root / "submissions"
            case_dir.mkdir()
            submissions_root.mkdir()

            write_json(case_dir / "case.json", make_case("slides.test.regression_v1", case_set="regression"))
            submission_dirs = []
            for index in range(1, 4):
                sub_dir = submissions_root / "run_{}".format(index)
                sub_dir.mkdir()
                write_minimal_pptx(
                    sub_dir / "deck.pptx",
                    slide_texts=["Sales summary", "Recommendation by region"],
                    chart_slides=[1],
                    table_slides=[2],
                )
                write_submission(sub_dir, "slides.test.regression_v1", attempt_id="run_{}".format(index))
                submission_dirs.append(sub_dir)

            runner = EvaluationRunner.from_case_paths([case_dir])
            suite_result = runner.evaluate_submission_paths(submission_dirs)

            self.assertEqual(len(suite_result.results), 3)
            self.assertEqual(suite_result.metrics["regression"]["pass_power_3"], 1.0)
            self.assertEqual(suite_result.metrics["regression"]["insufficient_attempt_cases"], [])

    def test_loads_case_folder_with_code_grader_file(self):
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            case_dir = root / "cases" / "example_case"
            grader_dir = case_dir / "graders"
            sub_dir = root / "submission"
            grader_dir.mkdir(parents=True)
            sub_dir.mkdir()

            write_json(
                case_dir / "case.json",
                {
                    "id": "slides.test.folder_case_v1",
                    "title": "Folder case",
                    "task_family": "slides",
                    "task_type": "no_artifact",
                    "set": "capability",
                    "question": {"query": "Return a final report."},
                    "output_contract": {"required_artifacts": []},
                    "success_threshold": 1.0,
                    "grader_files": ["graders/final_report_check.py"],
                },
            )
            (grader_dir / "final_report_check.py").write_text(
                "def grade(payload):\n"
                "    final_report = payload['submission']['final_report']\n"
                "    passed = 'executive summary' in final_report.lower()\n"
                "    return {\n"
                "        'score': 1.0 if passed else 0.0,\n"
                "        'passed': passed,\n"
                "        'summary': 'final report contains executive summary',\n"
                "        'details': {'final_report': final_report},\n"
                "    }\n",
                encoding="utf-8",
            )
            write_json(
                sub_dir / "submission.json",
                {
                    "case_id": "slides.test.folder_case_v1",
                    "attempt_id": "run_1",
                    "process": [{"thought": "prepare final response"}],
                    "final_report": "Executive summary: the deck is complete.",
                    "artifacts": [],
                },
            )

            runner = EvaluationRunner.from_case_paths([root / "cases"])
            suite_result = runner.evaluate_submission_paths([sub_dir])

            self.assertEqual(len(suite_result.results), 1)
            self.assertTrue(suite_result.results[0].passed)
            self.assertEqual(suite_result.results[0].grader_results[0].type, "code")

    def test_external_grader_reads_output_result_file(self):
        with tempfile.TemporaryDirectory() as raw_dir:
            root = Path(raw_dir)
            case_dir = root / "cases" / "file_judge_case"
            sub_dir = root / "submission"
            case_dir.mkdir(parents=True)
            sub_dir.mkdir()

            write_json(
                case_dir / "case.json",
                {
                    "id": "slides.test.file_judge_v1",
                    "title": "File judge case",
                    "task_family": "slides",
                    "task_type": "judge_file",
                    "set": "capability",
                    "question": {"query": "Return a final report."},
                    "output_contract": {"required_artifacts": []},
                    "success_threshold": 1.0,
                    "graders": [
                        {
                            "id": "file_judge",
                            "type": "external_command",
                            "weight": 1.0,
                            "threshold": 1.0,
                            "config": {
                                "command": [
                                    sys.executable,
                                    "-c",
                                    "import json; open('judge_result.json', 'w').write(json.dumps({'score': 1.0, 'passed': True, 'summary': 'ok', 'details': {'source': 'file'}}))"
                                ],
                                "cwd": str(sub_dir),
                                "output_result_file": "judge_result.json"
                            }
                        }
                    ]
                },
            )
            write_json(
                sub_dir / "submission.json",
                {
                    "case_id": "slides.test.file_judge_v1",
                    "attempt_id": "run_1",
                    "process": [],
                    "final_report": "Done.",
                    "artifacts": [],
                },
            )

            runner = EvaluationRunner.from_case_paths([root / "cases"])
            suite_result = runner.evaluate_submission_paths([sub_dir])

            self.assertTrue(suite_result.results[0].passed)
            self.assertEqual(suite_result.results[0].grader_results[0].details["source"], "file")


if __name__ == "__main__":
    unittest.main()

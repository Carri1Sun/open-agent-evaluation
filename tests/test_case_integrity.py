from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from open_agent_evaluation.case_loader import load_cases


REPO_ROOT = Path(__file__).resolve().parents[1]
SLIDES_CASES = REPO_ROOT / "cases" / "slides"

SUPPORTED_CONFIG_KEYS = {
    "artifact_presence": {"artifacts"},
    "pptx_structure": {
        "artifact_id",
        "min_slides",
        "max_slides",
        "min_images",
        "min_charts",
        "min_tables",
        "min_non_empty_slides",
        "min_speaker_notes_slides",
        "require_widescreen",
        "required_keywords",
        "max_text_chars_per_slide",
    },
    "trace_signal": {"signals"},
    "external_command": {"command", "timeout_seconds", "cwd", "output_result_file"},
    "scripted_command": {"command", "timeout_seconds", "cwd", "output_result_file"},
}


class CaseIntegrityTests(unittest.TestCase):
    def test_slides_cases_load_with_assets(self):
        cases = load_cases([SLIDES_CASES])

        self.assertEqual(len(cases), 15)

    def test_json_grader_configs_use_supported_runtime_keys(self):
        failures = []
        cases = load_cases([SLIDES_CASES])

        for case in cases.values():
            artifact_ids = {
                item.get("id")
                for item in case.output_contract.get("required_artifacts", [])
            }
            for spec in case.graders:
                allowed_keys = SUPPORTED_CONFIG_KEYS.get(spec.type)
                if allowed_keys is not None:
                    unknown_keys = sorted(set(spec.config) - allowed_keys)
                    if unknown_keys:
                        failures.append("{}:{} unknown keys {}".format(case.id, spec.id, unknown_keys))

                if spec.type == "pptx_structure":
                    artifact_id = spec.config.get("artifact_id")
                    if artifact_id not in artifact_ids:
                        failures.append("{}:{} unknown artifact {}".format(case.id, spec.id, artifact_id))

                if spec.type == "artifact_presence":
                    for artifact in spec.config.get("artifacts", []):
                        artifact_id = artifact.get("id")
                        if artifact_id not in artifact_ids:
                            failures.append("{}:{} unknown artifact {}".format(case.id, spec.id, artifact_id))

        self.assertEqual(failures, [])

    def test_case_local_files_and_attachments_exist_under_attachments_dir(self):
        failures = []
        for case_path in sorted(SLIDES_CASES.rglob("case.json")):
            case_dir = case_path.parent
            data = json.loads(case_path.read_text(encoding="utf-8"))
            question = data.get("question", {})
            browser_initial_state = question.get("browser_initial_state", {})
            referenced_paths = [
                item.get("path")
                for item in question.get("attachments", [])
                if item.get("path")
            ]
            referenced_paths.extend(browser_initial_state.get("local_files", []))

            for path_value in referenced_paths:
                path = Path(path_value)
                if path.is_absolute() or not path.parts or path.parts[0] != "attachments":
                    failures.append("{} references {}".format(case_path, path_value))
                    continue
                if not (case_dir / path).is_file():
                    failures.append("{} missing {}".format(case_path, path_value))

        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()

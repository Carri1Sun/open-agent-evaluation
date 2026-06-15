from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from .base import BaseGrader, GraderContext


class ExternalCommandGrader(BaseGrader):
    type_name = "external_command"

    def grade(self, context: GraderContext):
        command = context.spec.config.get("command")
        if not command:
            return self.result(
                context,
                score=0.0,
                passed=False,
                status="skipped",
                summary="External command is not configured.",
                details={},
            )

        if isinstance(command, str):
            command_args: List[str] = shlex.split(command)
        else:
            command_args = [str(item) for item in command]

        payload = {
            "case": context.case.to_dict(),
            "submission": context.submission.to_dict(),
            "grader": context.spec.to_dict(),
        }
        timeout = float(context.spec.config.get("timeout_seconds", 120))
        cwd = context.spec.config.get("cwd")

        try:
            completed = subprocess.run(
                command_args,
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                timeout=timeout,
                cwd=cwd,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return self.result(
                context,
                score=0.0,
                passed=False,
                status="error",
                summary="External command timed out.",
                details={"timeout_seconds": timeout},
            )
        except OSError as exc:
            return self.result(
                context,
                score=0.0,
                passed=False,
                status="error",
                summary="External command failed to start.",
                details={"error": str(exc), "command": command_args},
            )

        if completed.returncode != 0:
            return self.result(
                context,
                score=0.0,
                passed=False,
                status="error",
                summary="External command returned non-zero exit code.",
                details={
                    "returncode": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                    "command": command_args,
                },
            )

        output_result_file = context.spec.config.get("output_result_file")
        if output_result_file:
            result_path = resolve_result_path(str(output_result_file), cwd, context.submission.base_dir)
            if not result_path.exists():
                return self.result(
                    context,
                    score=0.0,
                    passed=False,
                    status="error",
                    summary="External command did not produce the configured result file.",
                    details={"output_result_file": str(result_path), "stdout": completed.stdout},
                )
            raw_result = result_path.read_text(encoding="utf-8")
        else:
            raw_result = completed.stdout

        try:
            data: Dict[str, Any] = json.loads(raw_result)
        except json.JSONDecodeError as exc:
            return self.result(
                context,
                score=0.0,
                passed=False,
                status="error",
                summary="External command did not return valid JSON.",
                details={"error": str(exc), "raw_result": raw_result, "stdout": completed.stdout},
            )

        score = float(data.get("score", 0.0))
        passed = bool(data.get("passed", score >= context.spec.threshold))
        status = "passed" if passed else "failed"
        return self.result(
            context,
            score=score,
            passed=passed,
            status=str(data.get("status", status)),
            summary=str(data.get("summary", "External grader completed.")),
            details=dict(data.get("details", {})),
        )


def resolve_result_path(path_value: str, cwd: Any, submission_base_dir: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    if cwd:
        return Path(str(cwd)) / path
    return submission_base_dir / path

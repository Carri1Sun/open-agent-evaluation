from __future__ import annotations

import json
import subprocess
import sys
from typing import Any, Dict

from .base import BaseGrader, GraderContext


class CodeGrader(BaseGrader):
    type_name = "code"

    def grade(self, context: GraderContext):
        language = str(context.spec.config.get("language", "python"))
        if language != "python":
            return self.result(
                context,
                score=0.0,
                passed=False,
                status="error",
                summary="Unsupported code grader language.",
                details={"language": language},
            )

        code = context.spec.config.get("code")
        if not code:
            return self.result(
                context,
                score=0.0,
                passed=False,
                status="skipped",
                summary="Code grader has no code configured.",
                details={},
            )

        payload = {
            "case": context.case.to_dict(),
            "submission": context.submission.to_dict(),
            "grader": context.spec.to_dict(),
        }
        timeout = float(context.spec.config.get("timeout_seconds", 30))
        wrapper = build_python_wrapper(str(code))

        try:
            completed = subprocess.run(
                [sys.executable, "-c", wrapper],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return self.result(
                context,
                score=0.0,
                passed=False,
                status="error",
                summary="Code grader timed out.",
                details={"timeout_seconds": timeout},
            )

        if completed.returncode != 0:
            return self.result(
                context,
                score=0.0,
                passed=False,
                status="error",
                summary="Code grader returned non-zero exit code.",
                details={
                    "returncode": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                },
            )

        try:
            data: Dict[str, Any] = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            return self.result(
                context,
                score=0.0,
                passed=False,
                status="error",
                summary="Code grader did not return valid JSON.",
                details={"error": str(exc), "stdout": completed.stdout},
            )

        score = float(data.get("score", 0.0))
        passed = bool(data.get("passed", score >= context.spec.threshold))
        status = "passed" if passed else "failed"
        return self.result(
            context,
            score=score,
            passed=passed,
            status=str(data.get("status", status)),
            summary=str(data.get("summary", "Code grader completed.")),
            details=dict(data.get("details", {})),
        )


def build_python_wrapper(code: str) -> str:
    code_literal = repr(code)
    return (
        "import json, sys\n"
        "payload = json.load(sys.stdin)\n"
        "namespace = {}\n"
        "exec(" + code_literal + ", namespace)\n"
        "if 'grade' not in namespace:\n"
        "    raise SystemExit('code grader must define grade(payload)')\n"
        "result = namespace['grade'](payload)\n"
        "print(json.dumps(result, ensure_ascii=False))\n"
    )

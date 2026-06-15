from __future__ import annotations

from typing import Any, Dict, List

from ..models import flatten_text
from .base import BaseGrader, GraderContext


class ArtifactPresenceGrader(BaseGrader):
    type_name = "artifact_presence"

    def grade(self, context: GraderContext):
        configured = context.spec.config.get("artifacts")
        if configured is None:
            configured = context.case.output_contract.get("required_artifacts", [])

        checks: List[Dict[str, Any]] = []
        passed_count = 0

        for item in configured:
            artifact_id = item.get("id")
            kind = item.get("kind")
            artifact = context.submission.find_artifact(artifact_id=artifact_id, kind=kind)
            exists = bool(artifact and artifact.path.exists())
            extension = item.get("extension")
            extension_ok = True
            if exists and extension:
                extension_ok = artifact.path.suffix.lower() == str(extension).lower()
            ok = exists and extension_ok
            if ok:
                passed_count += 1
            checks.append(
                {
                    "id": artifact_id,
                    "kind": kind,
                    "path": str(artifact.path) if artifact else None,
                    "exists": exists,
                    "extension": extension,
                    "extension_ok": extension_ok,
                    "required": item.get("required", True),
                    "passed": ok,
                }
            )

        denominator = len(configured) or 1
        score = passed_count / denominator
        missing_required = [
            check["id"] for check in checks
            if check["required"] and not check["passed"]
        ]
        passed = not missing_required and score >= context.spec.threshold
        status = "passed" if passed else "failed"
        summary = "All required artifacts are present." if passed else "Missing or invalid required artifacts."
        return self.result(
            context,
            score=score,
            passed=passed,
            status=status,
            summary=summary,
            details={"checked": checks, "missing_required": missing_required},
        )


class TraceSignalGrader(BaseGrader):
    type_name = "trace_signal"

    def grade(self, context: GraderContext):
        trace_text = flatten_text(context.submission.trace).lower()
        signals = context.spec.config.get("signals", [])
        checks: List[Dict[str, Any]] = []
        passed_count = 0

        for signal in signals:
            terms = [str(term).lower() for term in signal.get("any_text", [])]
            min_count = int(signal.get("min_count", 1))
            count = 0
            for term in terms:
                count += trace_text.count(term)
            passed = count >= min_count
            if passed:
                passed_count += 1
            checks.append(
                {
                    "id": signal.get("id"),
                    "terms": terms,
                    "count": count,
                    "min_count": min_count,
                    "passed": passed,
                }
            )

        score = passed_count / (len(signals) or 1)
        return self.score_result(
            context,
            score=score,
            summary="Trace signals satisfied." if score >= context.spec.threshold else "Trace signals are missing.",
            details={"signals": checks},
        )


class RubricPromptGrader(BaseGrader):
    type_name = "rubric_prompt"

    def grade(self, context: GraderContext):
        prompt = build_rubric_prompt(context)
        return self.result(
            context,
            score=0.0,
            passed=False,
            status="skipped",
            summary="Rubric prompt generated; no external judge configured.",
            details={
                "prompt": prompt,
                "criteria": context.spec.config.get("criteria", []),
                "next_step": "Configure an external_command grader or route this payload to an LLM/agent judge.",
            },
        )


def build_rubric_prompt(context: GraderContext) -> str:
    criteria = context.spec.config.get("criteria", [])
    criteria_text = "\n".join("- {}".format(item) for item in criteria)
    return (
        "You are evaluating an agent-generated slide deck.\n"
        "Case ID: {case_id}\n"
        "Task: {query}\n"
        "Final report: {final_response}\n"
        "Rubric criteria:\n{criteria}\n"
        "Return JSON with score, passed, summary, and evidence.\n"
    ).format(
        case_id=context.case.id,
        query=context.case.input.get("user_query", ""),
        final_response=context.submission.final_response,
        criteria=criteria_text,
    )

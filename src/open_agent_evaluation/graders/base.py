from __future__ import annotations

from dataclasses import dataclass

from ..models import EvaluationCase, GraderResult, GraderSpec, Submission


@dataclass(frozen=True)
class GraderContext:
    case: EvaluationCase
    submission: Submission
    spec: GraderSpec


class BaseGrader:
    type_name = "base"

    def grade(self, context: GraderContext) -> GraderResult:
        raise NotImplementedError

    def result(
        self,
        context: GraderContext,
        score: float,
        passed: bool,
        status: str,
        summary: str,
        details=None,
    ) -> GraderResult:
        if details is None:
            details = {}
        score = max(0.0, min(1.0, float(score)))
        return GraderResult(
            grader_id=context.spec.id,
            type=context.spec.type,
            score=score,
            passed=bool(passed),
            status=status,
            summary=summary,
            details=details,
        )

    def score_result(self, context: GraderContext, score: float, summary: str, details=None) -> GraderResult:
        passed = score >= context.spec.threshold
        status = "passed" if passed else "failed"
        return self.result(context, score, passed, status, summary, details)

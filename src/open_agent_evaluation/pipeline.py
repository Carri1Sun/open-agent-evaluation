from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .case_loader import discover_submission_files, load_cases, load_submission
from .graders import GraderRegistry, default_registry
from .graders.base import GraderContext
from .metrics import summarize_suite
from .models import CaseResult, EvaluationCase, EvaluationError, GraderResult, GraderSpec, Submission, SuiteResult


class EvaluationRunner:
    def __init__(self, cases: Dict[str, EvaluationCase], registry: Optional[GraderRegistry] = None) -> None:
        self.cases = cases
        self.registry = registry or default_registry()

    @classmethod
    def from_case_paths(cls, paths: Iterable[Path], registry: Optional[GraderRegistry] = None) -> "EvaluationRunner":
        return cls(load_cases(paths), registry=registry)

    def evaluate_submission(self, submission: Submission) -> CaseResult:
        try:
            case = self.cases[submission.case_id]
        except KeyError:
            raise EvaluationError("No case found for submission case_id: {}".format(submission.case_id))

        grader_results: List[GraderResult] = []
        for spec in case.graders:
            context = GraderContext(case=case, submission=submission, spec=spec)
            try:
                grader_results.append(self.registry.grade(context))
            except Exception as exc:
                grader_results.append(
                    GraderResult(
                        grader_id=spec.id,
                        type=spec.type,
                        score=0.0,
                        passed=False,
                        status="error",
                        summary="Grader raised an exception.",
                        details={"error": str(exc)},
                    )
                )

        score = aggregate_score(case.graders, grader_results)
        required_failures = find_required_failures(case.graders, grader_results)
        incomplete = any(result.status == "skipped" for result in grader_results)
        passed = not required_failures and score >= case.success_threshold
        return CaseResult(
            case_id=case.id,
            attempt_id=submission.attempt_id,
            set=case.set,
            score=score,
            passed=passed,
            incomplete=incomplete,
            grader_results=grader_results,
            required_failures=required_failures,
        )

    def evaluate_submission_paths(self, paths: Iterable[Path]) -> SuiteResult:
        submission_files = discover_submission_files(paths)
        results = [
            self.evaluate_submission(load_submission(path))
            for path in submission_files
        ]
        metrics = summarize_suite(results, self.cases)
        return SuiteResult(results=results, metrics=metrics)


def aggregate_score(specs: List[GraderSpec], results: List[GraderResult]) -> float:
    spec_by_id = {spec.id: spec for spec in specs}
    weighted = 0.0
    total_weight = 0.0
    for result in results:
        spec = spec_by_id.get(result.grader_id)
        if spec is None:
            continue
        if result.status == "skipped":
            continue
        weighted += result.score * spec.weight
        total_weight += spec.weight
    if total_weight == 0:
        return 0.0
    return weighted / total_weight


def find_required_failures(specs: List[GraderSpec], results: List[GraderResult]) -> List[str]:
    result_by_id = {result.grader_id: result for result in results}
    failures: List[str] = []
    for spec in specs:
        if not spec.required:
            continue
        result = result_by_id.get(spec.id)
        if result is None or not result.passed or result.status in {"skipped", "error"}:
            failures.append(spec.id)
    return failures

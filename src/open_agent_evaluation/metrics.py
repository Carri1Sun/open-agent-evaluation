from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List

from .models import CaseResult, EvaluationCase, JsonDict


def pass_at_k(results: Iterable[CaseResult], k: int) -> bool:
    selected = list(results)[:k]
    return any(result.passed for result in selected)


def pass_power_k(results: Iterable[CaseResult], k: int) -> bool:
    selected = list(results)[:k]
    return len(selected) >= k and all(result.passed for result in selected)


def summarize_suite(results: List[CaseResult], cases: Dict[str, EvaluationCase], k: int = 3) -> JsonDict:
    by_case: Dict[str, List[CaseResult]] = defaultdict(list)
    for result in results:
        by_case[result.case_id].append(result)

    capability_case_ids = sorted(case_id for case_id, case in cases.items() if case.set == "capability")
    regression_case_ids = sorted(case_id for case_id, case in cases.items() if case.set == "regression")

    capability_with_results = [case_id for case_id in capability_case_ids if case_id in by_case]
    regression_with_results = [case_id for case_id in regression_case_ids if case_id in by_case]

    capability_passed = [
        case_id for case_id in capability_with_results
        if pass_at_k(by_case[case_id], k)
    ]
    regression_passed = [
        case_id for case_id in regression_with_results
        if pass_power_k(by_case[case_id], k)
    ]

    return {
        "attempt_count": len(results),
        "case_count_with_results": len(by_case),
        "capability": {
            "case_count": len(capability_with_results),
            "pass_at_{}".format(k): ratio(len(capability_passed), len(capability_with_results)),
            "passed_cases": capability_passed,
            "missing_cases": [case_id for case_id in capability_case_ids if case_id not in by_case],
        },
        "regression": {
            "case_count": len(regression_with_results),
            "pass_power_{}".format(k): ratio(len(regression_passed), len(regression_with_results)),
            "passed_cases": regression_passed,
            "missing_cases": [case_id for case_id in regression_case_ids if case_id not in by_case],
            "insufficient_attempt_cases": [
                case_id for case_id in regression_with_results if len(by_case[case_id]) < k
            ],
        },
    }


def ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator

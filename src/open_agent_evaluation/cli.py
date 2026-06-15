from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .case_loader import load_cases
from .models import EvaluationError
from .pipeline import EvaluationRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="open-agent-eval")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_cases = subparsers.add_parser("list-cases", help="List evaluation cases.")
    list_cases.add_argument("--cases", nargs="+", required=True, type=Path)

    run = subparsers.add_parser("run", help="Run evaluation over submissions.")
    run.add_argument("--cases", nargs="+", required=True, type=Path)
    run.add_argument("--submissions", nargs="+", required=True, type=Path)
    run.add_argument("--output", type=Path, help="Write JSON report to this path.")
    run.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")

    validate_case = subparsers.add_parser("validate-case", help="Load case files and fail on structural errors.")
    validate_case.add_argument("--cases", nargs="+", required=True, type=Path)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "list-cases":
            cases = load_cases(args.cases)
            for case in sorted(cases.values(), key=lambda item: item.id):
                print("{id}\t{set}\t{task_family}/{task_type}\t{title}".format(
                    id=case.id,
                    set=case.set,
                    task_family=case.task_family,
                    task_type=case.task_type,
                    title=case.title,
                ))
            return 0

        if args.command == "validate-case":
            cases = load_cases(args.cases)
            print("Loaded {} cases.".format(len(cases)))
            return 0

        if args.command == "run":
            runner = EvaluationRunner.from_case_paths(args.cases)
            suite_result = runner.evaluate_submission_paths(args.submissions)
            data = suite_result.to_dict()
            indent = 2 if args.pretty else None
            output = json.dumps(data, indent=indent, ensure_ascii=False)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(output + "\n", encoding="utf-8")
            print_summary(data)
            if not args.output:
                print(output)
            return 0
    except EvaluationError as exc:
        print("error: {}".format(exc), file=sys.stderr)
        return 2

    parser.print_help()
    return 1


def print_summary(data) -> None:
    metrics = data.get("metrics", {})
    capability = metrics.get("capability", {})
    regression = metrics.get("regression", {})
    print("Attempts: {}".format(metrics.get("attempt_count", 0)))
    print("Cases with results: {}".format(metrics.get("case_count_with_results", 0)))
    print("Capability pass@3: {:.2f}".format(capability.get("pass_at_3", 0.0)))
    print("Regression pass^3: {:.2f}".format(regression.get("pass_power_3", 0.0)))


if __name__ == "__main__":
    raise SystemExit(main())

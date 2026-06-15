from __future__ import annotations

from .base import BaseGrader, GraderContext
from .external import ExternalCommandGrader


class LlmJudgeGrader(BaseGrader):
    type_name = "llm_judge"

    def grade(self, context: GraderContext):
        if context.spec.config.get("command"):
            return ExternalCommandGrader().grade(context)

        prompt = context.spec.config.get("prompt")
        if not prompt:
            prompt = build_default_prompt(context)
        return self.result(
            context,
            score=0.0,
            passed=False,
            status="skipped",
            summary="LLM judge prompt is prepared; no judge command is configured.",
            details={
                "prompt": prompt,
                "expected_output": {
                    "score": "number from 0 to 1",
                    "passed": "boolean",
                    "summary": "short explanation",
                    "details": "structured evidence",
                },
            },
        )


class AgentJudgeGrader(BaseGrader):
    type_name = "agent_judge"

    def grade(self, context: GraderContext):
        if context.spec.config.get("command"):
            return ExternalCommandGrader().grade(context)
        return self.result(
            context,
            score=0.0,
            passed=False,
            status="skipped",
            summary="Agent judge prompt is prepared; no agent command is configured.",
            details={
                "prompt": context.spec.config.get("prompt", build_default_prompt(context)),
                "output_result_file": context.spec.config.get("output_result_file"),
            },
        )


def build_default_prompt(context: GraderContext) -> str:
    return (
        "Evaluate the agent submission for case {case_id}.\n"
        "User query: {query}\n"
        "Final report: {final_report}\n"
        "Return JSON with score, passed, summary, and details."
    ).format(
        case_id=context.case.id,
        query=context.case.input.get("user_query", ""),
        final_report=context.submission.final_response,
    )

from __future__ import annotations

from typing import Dict, Type

from ..models import EvaluationError, GraderResult
from .base import BaseGrader, GraderContext


class GraderRegistry:
    def __init__(self) -> None:
        self._graders: Dict[str, Type[BaseGrader]] = {}

    def register(self, grader_type: str, grader_cls: Type[BaseGrader]) -> None:
        self._graders[grader_type] = grader_cls

    def create(self, grader_type: str) -> BaseGrader:
        try:
            return self._graders[grader_type]()
        except KeyError:
            raise EvaluationError("Unknown grader type: {}".format(grader_type))

    def grade(self, context: GraderContext) -> GraderResult:
        grader = self.create(context.spec.type)
        return grader.grade(context)

    def types(self):
        return sorted(self._graders)


def default_registry() -> GraderRegistry:
    from .code import CodeGrader
    from .deterministic import ArtifactPresenceGrader, RubricPromptGrader, TraceSignalGrader
    from .external import ExternalCommandGrader
    from .judges import AgentJudgeGrader, LlmJudgeGrader
    from .pptx import PptxStructureGrader

    registry = GraderRegistry()
    registry.register("artifact_presence", ArtifactPresenceGrader)
    registry.register("code", CodeGrader)
    registry.register("trace_signal", TraceSignalGrader)
    registry.register("rubric_prompt", RubricPromptGrader)
    registry.register("llm_judge", LlmJudgeGrader)
    registry.register("agent_judge", AgentJudgeGrader)
    registry.register("pi_agent_judge", AgentJudgeGrader)
    registry.register("external_command", ExternalCommandGrader)
    registry.register("scripted_command", ExternalCommandGrader)
    registry.register("pptx_structure", PptxStructureGrader)
    return registry

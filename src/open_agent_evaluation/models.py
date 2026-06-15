from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


JsonDict = Dict[str, Any]


class EvaluationError(Exception):
    """Raised when evaluation input cannot be loaded or evaluated."""


@dataclass(frozen=True)
class Artifact:
    id: str
    kind: str
    path: Path
    description: str = ""
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], base_dir: Path) -> "Artifact":
        path_value = data.get("path")
        if not path_value:
            raise EvaluationError("Artifact is missing path.")
        path = Path(str(path_value))
        if not path.is_absolute():
            path = base_dir / path
        metadata = {k: v for k, v in data.items() if k not in {"id", "kind", "path", "description"}}
        return cls(
            id=str(data.get("id", "")),
            kind=str(data.get("kind", "")),
            path=path,
            description=str(data.get("description", "")),
            metadata=metadata,
        )

    def to_dict(self, relative_to: Optional[Path] = None) -> JsonDict:
        path: Any = str(self.path)
        if relative_to is not None:
            try:
                path = str(self.path.relative_to(relative_to))
            except ValueError:
                path = str(self.path)
        return {
            "id": self.id,
            "kind": self.kind,
            "path": path,
            "description": self.description,
            **self.metadata,
        }


@dataclass(frozen=True)
class Submission:
    case_id: str
    attempt_id: str
    base_dir: Path
    artifacts: List[Artifact]
    final_response: str = ""
    trace: Any = None
    metadata: JsonDict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], base_dir: Path) -> "Submission":
        if "case_id" not in data:
            raise EvaluationError("Submission is missing case_id.")
        if "attempt_id" not in data:
            raise EvaluationError("Submission is missing attempt_id.")

        trace: Any = data.get("process", data.get("trace"))
        trace_path = data.get("trace_path")
        if trace is None and trace_path:
            path = Path(str(trace_path))
            if not path.is_absolute():
                path = base_dir / path
            trace = path.read_text(encoding="utf-8")

        artifacts_data = data.get("artifacts", data.get("final_artifacts", []))
        artifacts = [
            Artifact.from_dict(item, base_dir)
            for item in artifacts_data
        ]
        return cls(
            case_id=str(data["case_id"]),
            attempt_id=str(data["attempt_id"]),
            base_dir=base_dir,
            artifacts=artifacts,
            final_response=str(data.get("final_report", data.get("final_response", ""))),
            trace=trace,
            metadata=dict(data.get("metadata", {})),
        )

    def find_artifact(self, artifact_id: Optional[str] = None, kind: Optional[str] = None) -> Optional[Artifact]:
        for artifact in self.artifacts:
            if artifact_id is not None and artifact.id != artifact_id:
                continue
            if kind is not None and artifact.kind != kind:
                continue
            return artifact
        return None

    def to_dict(self) -> JsonDict:
        return {
            "case_id": self.case_id,
            "attempt_id": self.attempt_id,
            "final_report": self.final_response,
            "process": self.trace,
            "artifacts": [artifact.to_dict(relative_to=self.base_dir) for artifact in self.artifacts],
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class GraderSpec:
    id: str
    type: str
    weight: float = 1.0
    threshold: float = 1.0
    required: bool = False
    config: JsonDict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GraderSpec":
        if "id" not in data or "type" not in data:
            raise EvaluationError("Grader spec must include id and type.")
        return cls(
            id=str(data["id"]),
            type=str(data["type"]),
            weight=float(data.get("weight", 1.0)),
            threshold=float(data.get("threshold", 1.0)),
            required=bool(data.get("required", False)),
            config=dict(data.get("config", {})),
        )

    def to_dict(self) -> JsonDict:
        return {
            "id": self.id,
            "type": self.type,
            "weight": self.weight,
            "threshold": self.threshold,
            "required": self.required,
            "config": self.config,
        }


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    title: str
    task_family: str
    task_type: str
    set: str
    input: JsonDict
    output_contract: JsonDict
    graders: List[GraderSpec]
    version: str = "1.0.0"
    description: str = ""
    success_threshold: float = 1.0
    metadata: JsonDict = field(default_factory=dict)
    source_path: Optional[Path] = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], source_path: Optional[Path] = None) -> "EvaluationCase":
        normalized = normalize_case_dict(data)
        required = ["id", "title", "task_family", "task_type", "set", "input", "output_contract", "graders"]
        missing = [key for key in required if key not in normalized]
        if missing:
            raise EvaluationError("Case is missing required fields: " + ", ".join(missing))
        case_set = str(normalized["set"])
        if case_set not in {"capability", "regression"}:
            raise EvaluationError("Case set must be capability or regression.")
        graders = [GraderSpec.from_dict(item) for item in normalized.get("graders", [])]
        if not graders:
            raise EvaluationError("Case must include at least one grader.")
        return cls(
            id=str(normalized["id"]),
            title=str(normalized["title"]),
            task_family=str(normalized["task_family"]),
            task_type=str(normalized["task_type"]),
            set=case_set,
            input=dict(normalized["input"]),
            output_contract=dict(normalized["output_contract"]),
            graders=graders,
            version=str(normalized.get("version", "1.0.0")),
            description=str(normalized.get("description", "")),
            success_threshold=float(normalized.get("success_threshold", 1.0)),
            metadata=dict(normalized.get("metadata", {})),
            source_path=source_path,
        )

    def to_dict(self) -> JsonDict:
        return {
            "id": self.id,
            "title": self.title,
            "version": self.version,
            "task_family": self.task_family,
            "task_type": self.task_type,
            "set": self.set,
            "description": self.description,
            "question": {
                "query": self.input.get("user_query", ""),
                "browser_initial_state": self.input.get("browser_initial_state", {}),
                "attachments": self.input.get("attachments", []),
            },
            "input": self.input,
            "output_contract": self.output_contract,
            "success_threshold": self.success_threshold,
            "graders": [grader.to_dict() for grader in self.graders],
            "metadata": self.metadata,
        }


@dataclass
class GraderResult:
    grader_id: str
    type: str
    score: float
    passed: bool
    status: str
    summary: str
    details: JsonDict = field(default_factory=dict)

    def to_dict(self) -> JsonDict:
        return {
            "grader_id": self.grader_id,
            "type": self.type,
            "score": self.score,
            "passed": self.passed,
            "status": self.status,
            "summary": self.summary,
            "details": self.details,
        }


@dataclass
class CaseResult:
    case_id: str
    attempt_id: str
    set: str
    score: float
    passed: bool
    incomplete: bool
    grader_results: List[GraderResult]
    required_failures: List[str] = field(default_factory=list)

    def to_dict(self) -> JsonDict:
        return {
            "case_id": self.case_id,
            "attempt_id": self.attempt_id,
            "set": self.set,
            "score": self.score,
            "passed": self.passed,
            "incomplete": self.incomplete,
            "required_failures": self.required_failures,
            "grader_results": [result.to_dict() for result in self.grader_results],
        }


@dataclass
class SuiteResult:
    results: List[CaseResult]
    metrics: JsonDict

    def to_dict(self) -> JsonDict:
        return {
            "metrics": self.metrics,
            "results": [result.to_dict() for result in self.results],
        }


def flatten_text(value: Any) -> str:
    """Serialize nested trace-like data into searchable text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return " ".join(flatten_text(item) for item in value.values())
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        return " ".join(flatten_text(item) for item in value)
    return str(value)


def normalize_case_dict(data: Mapping[str, Any]) -> JsonDict:
    """Accept the author-friendly case shape and convert it to runtime fields."""
    normalized = dict(data)
    question = normalized.get("question")
    input_data = dict(normalized.get("input", {}))

    if question is not None:
        if isinstance(question, str):
            input_data.setdefault("user_query", question)
        elif isinstance(question, Mapping):
            if "query" in question:
                input_data.setdefault("user_query", question["query"])
            for key in ("browser_initial_state", "attachments"):
                if key in question:
                    input_data.setdefault(key, question[key])
        else:
            raise EvaluationError("Case question must be a string or object.")

    if input_data:
        normalized["input"] = input_data
    return normalized

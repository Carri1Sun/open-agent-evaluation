from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .models import EvaluationCase, EvaluationError, GraderSpec, Submission


def discover_case_sources(paths: Iterable[Path]) -> List[Path]:
    sources: List[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".json":
            sources.append(path)
        elif path.is_dir():
            if (path / "case.json").is_file():
                sources.append(path)
            else:
                case_dirs = sorted(item.parent for item in path.rglob("case.json") if item.is_file())
                sources.extend(case_dirs)
                if not case_dirs:
                    sources.extend(sorted(item for item in path.rglob("*.json") if item.is_file()))
        else:
            raise EvaluationError("Case path does not exist: {}".format(path))
    return sorted(dict.fromkeys(sources))


def load_case(path: Path) -> EvaluationCase:
    if path.is_dir():
        case_path = path / "case.json"
        base_dir = path
    else:
        case_path = path
        base_dir = path.parent

    with case_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    data = dict(data)
    data["graders"] = [grader.to_dict() for grader in load_grader_specs(data, base_dir)]
    return EvaluationCase.from_dict(data, source_path=case_path)


def load_cases(paths: Iterable[Path]) -> Dict[str, EvaluationCase]:
    cases: Dict[str, EvaluationCase] = {}
    for path in discover_case_sources(paths):
        case = load_case(path)
        if case.id in cases:
            raise EvaluationError("Duplicate case id: {}".format(case.id))
        cases[case.id] = case
    return cases


def load_grader_specs(case_data: Mapping[str, Any], base_dir: Path) -> List[GraderSpec]:
    entries: List[Any] = []
    entries.extend(case_data.get("graders", []))
    entries.extend(case_data.get("grader_files", []))

    if not entries:
        grader_dir = base_dir / "graders"
        if grader_dir.is_dir():
            entries.extend(sorted(item for item in grader_dir.iterdir() if item.suffix in {".json", ".md", ".py"}))

    return [load_grader_entry(entry, base_dir) for entry in entries]


def load_grader_entry(entry: Any, base_dir: Path) -> GraderSpec:
    if isinstance(entry, (str, Path)):
        return load_grader_file(resolve_path(base_dir, entry), overrides=None)
    if not isinstance(entry, Mapping):
        raise EvaluationError("Grader entry must be an object or file path.")

    file_value = entry.get("file", entry.get("path"))
    if file_value:
        overrides = {key: value for key, value in entry.items() if key not in {"file", "path"}}
        return load_grader_file(resolve_path(base_dir, file_value), overrides=overrides)
    return GraderSpec.from_dict(resolve_grader_data(entry, base_dir))


def load_grader_file(path: Path, overrides: Optional[Mapping[str, Any]]) -> GraderSpec:
    if not path.exists():
        raise EvaluationError("Grader file does not exist: {}".format(path))
    if path.suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    elif path.suffix == ".md":
        data = parse_prompt_grader(path)
    elif path.suffix == ".py":
        data = {
            "id": path.stem,
            "type": "code",
            "config": {
                "language": "python",
                "code": path.read_text(encoding="utf-8"),
            },
        }
    else:
        raise EvaluationError("Unsupported grader file type: {}".format(path))

    if overrides:
        data = merge_grader_overrides(data, overrides)
    return GraderSpec.from_dict(resolve_grader_data(data, path.parent))


def parse_prompt_grader(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    metadata: Dict[str, Any] = {}
    body = text
    if text.startswith("---\n"):
        _, raw_metadata, body = text.split("---\n", 2)
        metadata = parse_simple_frontmatter(raw_metadata)
    return {
        "id": metadata.pop("id", path.stem),
        "type": metadata.pop("type", "llm_judge"),
        "weight": metadata.pop("weight", 1.0),
        "threshold": metadata.pop("threshold", 1.0),
        "required": metadata.pop("required", False),
        "config": {
            **metadata,
            "prompt": body.strip(),
        },
    }


def parse_simple_frontmatter(raw_metadata: str) -> Dict[str, Any]:
    parsed: Dict[str, Any] = {}
    for line in raw_metadata.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        parsed[key.strip()] = parse_scalar(value.strip())
    return parsed


def parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip("\"'")


def merge_grader_overrides(data: Mapping[str, Any], overrides: Mapping[str, Any]) -> Dict[str, Any]:
    merged = dict(data)
    for key, value in overrides.items():
        if key == "config":
            merged["config"] = {**dict(merged.get("config", {})), **dict(value)}
        else:
            merged[key] = value
    return merged


def resolve_grader_data(data: Mapping[str, Any], base_dir: Path) -> Dict[str, Any]:
    normalized = dict(data)
    config = dict(normalized.get("config", {}))
    for key in ("prompt", "prompt_path", "code", "code_path", "command", "output_result_file", "timeout_seconds"):
        if key in normalized:
            config[key] = normalized[key]
    if "prompt_path" in config:
        config["prompt"] = resolve_path(base_dir, config["prompt_path"]).read_text(encoding="utf-8")
    if "code_path" in config:
        config["code"] = resolve_path(base_dir, config["code_path"]).read_text(encoding="utf-8")
    normalized["config"] = config
    return normalized


def resolve_path(base_dir: Path, value: Any) -> Path:
    path = Path(str(value))
    if path.is_absolute():
        return path
    return base_dir / path


def load_submission(path: Path) -> Submission:
    base_dir = path
    submission_path = path
    if path.is_dir():
        submission_path = path / "submission.json"
        base_dir = path
    else:
        base_dir = path.parent
    if not submission_path.exists():
        raise EvaluationError("Submission file does not exist: {}".format(submission_path))
    with submission_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return Submission.from_dict(data, base_dir=base_dir)


def discover_submission_files(paths: Iterable[Path]) -> List[Path]:
    files: List[Path] = []
    for path in paths:
        if path.is_file():
            files.append(path)
        elif path.is_dir() and (path / "submission.json").exists():
            files.append(path / "submission.json")
        elif path.is_dir():
            files.extend(sorted(item for item in path.rglob("submission.json") if item.is_file()))
        else:
            raise EvaluationError("Submission path does not exist: {}".format(path))
    return sorted(files)

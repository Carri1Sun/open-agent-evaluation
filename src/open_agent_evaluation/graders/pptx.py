from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

from .base import BaseGrader, GraderContext


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


@dataclass
class PresentationStats:
    path: Path
    slide_count: int
    slide_texts: List[str]
    notes_texts: List[str]
    image_count: int
    chart_count: int
    table_count: int
    size_cx: Optional[int]
    size_cy: Optional[int]

    @property
    def all_text(self) -> str:
        return "\n".join(self.slide_texts + self.notes_texts)

    @property
    def non_empty_slides(self) -> int:
        return sum(1 for text in self.slide_texts if text.strip())

    @property
    def speaker_notes_slides(self) -> int:
        return sum(1 for text in self.notes_texts if text.strip())

    @property
    def is_widescreen(self) -> bool:
        if not self.size_cx or not self.size_cy:
            return False
        ratio = self.size_cx / self.size_cy
        return 1.70 <= ratio <= 1.85

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "slide_count": self.slide_count,
            "image_count": self.image_count,
            "chart_count": self.chart_count,
            "table_count": self.table_count,
            "non_empty_slides": self.non_empty_slides,
            "speaker_notes_slides": self.speaker_notes_slides,
            "size_cx": self.size_cx,
            "size_cy": self.size_cy,
            "is_widescreen": self.is_widescreen,
            "text_chars_per_slide": [len(text) for text in self.slide_texts],
        }


class PptxStructureGrader(BaseGrader):
    type_name = "pptx_structure"

    def grade(self, context: GraderContext):
        artifact_id = context.spec.config.get("artifact_id")
        artifact = context.submission.find_artifact(artifact_id=artifact_id, kind="pptx")
        if artifact is None:
            return self.result(
                context,
                score=0.0,
                passed=False,
                status="failed",
                summary="PPTX artifact is missing from submission.",
                details={"artifact_id": artifact_id},
            )
        if not artifact.path.exists():
            return self.result(
                context,
                score=0.0,
                passed=False,
                status="failed",
                summary="PPTX file does not exist.",
                details={"path": str(artifact.path)},
            )

        try:
            stats = inspect_pptx(artifact.path)
        except (OSError, zipfile.BadZipFile, ElementTree.ParseError) as exc:
            return self.result(
                context,
                score=0.0,
                passed=False,
                status="error",
                summary="PPTX file could not be parsed.",
                details={"path": str(artifact.path), "error": str(exc)},
            )

        checks = build_pptx_checks(stats, context.spec.config)
        score = sum(check["score"] for check in checks) / (len(checks) or 1)
        passed = score >= context.spec.threshold
        status = "passed" if passed else "failed"
        summary = "PPTX structure satisfies the configured checks." if passed else "PPTX structure failed one or more checks."
        return self.result(
            context,
            score=score,
            passed=passed,
            status=status,
            summary=summary,
            details={
                **stats.to_dict(),
                "checks": checks,
            },
        )


def inspect_pptx(path: Path) -> PresentationStats:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        slide_names = sorted(
            [name for name in names if re.match(r"ppt/slides/slide\d+\.xml$", name)],
            key=slide_sort_key,
        )
        notes_names = sorted(
            [name for name in names if re.match(r"ppt/notesSlides/notesSlide\d+\.xml$", name)],
            key=slide_sort_key,
        )

        slide_texts: List[str] = []
        chart_count = 0
        table_count = 0
        image_refs = set()
        for slide_name in slide_names:
            root = ElementTree.fromstring(archive.read(slide_name))
            slide_texts.append(extract_text(root))
            table_count += len(root.findall(".//a:tbl", NS))
            chart_count += len(root.findall(".//c:chart", NS))
            for blip in root.findall(".//a:blip", NS):
                embed = blip.attrib.get("{" + NS["r"] + "}embed")
                if embed:
                    image_refs.add("{}:{}".format(slide_name, embed))

        notes_texts: List[str] = []
        for notes_name in notes_names:
            root = ElementTree.fromstring(archive.read(notes_name))
            notes_texts.append(extract_text(root))

        media_files = [name for name in names if name.startswith("ppt/media/")]
        image_count = max(len(media_files), len(image_refs))
        size_cx, size_cy = read_slide_size(archive)

    return PresentationStats(
        path=path,
        slide_count=len(slide_names),
        slide_texts=slide_texts,
        notes_texts=notes_texts,
        image_count=image_count,
        chart_count=chart_count,
        table_count=table_count,
        size_cx=size_cx,
        size_cy=size_cy,
    )


def extract_text(root: ElementTree.Element) -> str:
    return " ".join(node.text or "" for node in root.findall(".//a:t", NS)).strip()


def read_slide_size(archive: zipfile.ZipFile):
    try:
        root = ElementTree.fromstring(archive.read("ppt/presentation.xml"))
    except KeyError:
        return None, None
    node = root.find(".//p:sldSz", NS)
    if node is None:
        return None, None
    try:
        return int(node.attrib.get("cx", "0")), int(node.attrib.get("cy", "0"))
    except ValueError:
        return None, None


def slide_sort_key(name: str) -> int:
    match = re.search(r"(\d+)\.xml$", name)
    return int(match.group(1)) if match else 0


def build_pptx_checks(stats: PresentationStats, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []

    if "min_slides" in config:
        checks.append(min_check("min_slides", stats.slide_count, int(config["min_slides"])))
    if "max_slides" in config:
        checks.append(max_check("max_slides", stats.slide_count, int(config["max_slides"])))
    if "min_images" in config:
        checks.append(min_check("min_images", stats.image_count, int(config["min_images"])))
    if "min_charts" in config:
        checks.append(min_check("min_charts", stats.chart_count, int(config["min_charts"])))
    if "min_tables" in config:
        checks.append(min_check("min_tables", stats.table_count, int(config["min_tables"])))
    if "min_non_empty_slides" in config:
        checks.append(min_check("min_non_empty_slides", stats.non_empty_slides, int(config["min_non_empty_slides"])))
    if "min_speaker_notes_slides" in config:
        checks.append(min_check("min_speaker_notes_slides", stats.speaker_notes_slides, int(config["min_speaker_notes_slides"])))
    if config.get("require_widescreen"):
        checks.append(
            {
                "id": "require_widescreen",
                "actual": stats.is_widescreen,
                "expected": True,
                "score": 1.0 if stats.is_widescreen else 0.0,
            }
        )
    if "required_keywords" in config:
        keywords = [str(keyword) for keyword in config.get("required_keywords", [])]
        text = stats.all_text.lower()
        found = [keyword for keyword in keywords if keyword.lower() in text]
        checks.append(
            {
                "id": "required_keywords",
                "actual": found,
                "expected": keywords,
                "score": len(found) / (len(keywords) or 1),
            }
        )
    if "max_text_chars_per_slide" in config:
        limit = int(config["max_text_chars_per_slide"])
        lengths = [len(text) for text in stats.slide_texts]
        over_limit = [length for length in lengths if length > limit]
        checks.append(
            {
                "id": "max_text_chars_per_slide",
                "actual": lengths,
                "expected": "<= {}".format(limit),
                "score": 1.0 - (len(over_limit) / (len(lengths) or 1)),
            }
        )

    return checks


def min_check(check_id: str, actual: int, expected: int) -> Dict[str, Any]:
    if expected <= 0:
        score = 1.0
    else:
        score = min(1.0, actual / expected)
    return {
        "id": check_id,
        "actual": actual,
        "expected": ">= {}".format(expected),
        "score": score,
    }


def max_check(check_id: str, actual: int, expected: int) -> Dict[str, Any]:
    return {
        "id": check_id,
        "actual": actual,
        "expected": "<= {}".format(expected),
        "score": 1.0 if actual <= expected else 0.0,
    }

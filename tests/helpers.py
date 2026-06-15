from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Iterable, List


PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
DML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
CHART_NS = "http://schemas.openxmlformats.org/drawingml/2006/chart"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def write_minimal_pptx(
    path: Path,
    slide_texts: Iterable[str],
    chart_slides: Iterable[int] = (),
    table_slides: Iterable[int] = (),
    image_slides: Iterable[int] = (),
    notes_texts: Iterable[str] = (),
    widescreen: bool = True,
) -> None:
    slide_text_list = list(slide_texts)
    notes_text_list = list(notes_texts)
    chart_set = set(chart_slides)
    table_set = set(table_slides)
    image_set = set(image_slides)
    cx, cy = (12192000, 6858000) if widescreen else (9144000, 6858000)

    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"/>")
        archive.writestr(
            "ppt/presentation.xml",
            "<p:presentation xmlns:p=\"{p}\"><p:sldSz cx=\"{cx}\" cy=\"{cy}\"/></p:presentation>".format(
                p=PML_NS,
                cx=cx,
                cy=cy,
            ),
        )
        for index, text in enumerate(slide_text_list, start=1):
            archive.writestr(
                "ppt/slides/slide{}.xml".format(index),
                slide_xml(
                    text=text,
                    has_chart=index in chart_set,
                    has_table=index in table_set,
                    has_image=index in image_set,
                ),
            )
        for index, text in enumerate(notes_text_list, start=1):
            archive.writestr("ppt/notesSlides/notesSlide{}.xml".format(index), notes_xml(text))
        for index in image_set:
            archive.writestr("ppt/media/image{}.png".format(index), b"not-really-a-png")


def slide_xml(text: str, has_chart: bool, has_table: bool, has_image: bool) -> str:
    chart = "<c:chart/>" if has_chart else ""
    table = "<a:tbl/>" if has_table else ""
    image = "<a:blip r:embed=\"rId1\"/>" if has_image else ""
    return (
        "<p:sld xmlns:p=\"{p}\" xmlns:a=\"{a}\" xmlns:c=\"{c}\" xmlns:r=\"{r}\">"
        "<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>"
        "{chart}{table}{image}"
        "</p:spTree></p:cSld></p:sld>"
    ).format(p=PML_NS, a=DML_NS, c=CHART_NS, r=REL_NS, text=escape_xml(text), chart=chart, table=table, image=image)


def notes_xml(text: str) -> str:
    return (
        "<p:notes xmlns:p=\"{p}\" xmlns:a=\"{a}\">"
        "<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>"
        "</p:spTree></p:cSld></p:notes>"
    ).format(p=PML_NS, a=DML_NS, text=escape_xml(text))


def escape_xml(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def make_case(case_id: str, case_set: str = "capability"):
    return {
        "id": case_id,
        "title": "Test case",
        "version": "1.0.0",
        "task_family": "slides",
        "task_type": "data_presentation",
        "set": case_set,
        "input": {"user_query": "Create slides."},
        "output_contract": {
            "required_artifacts": [
                {"id": "deck", "kind": "pptx", "extension": ".pptx", "required": True}
            ]
        },
        "success_threshold": 0.9,
        "graders": [
            {
                "id": "deck_exists",
                "type": "artifact_presence",
                "weight": 0.2,
                "threshold": 1.0,
                "required": True,
                "config": {
                    "artifacts": [
                        {"id": "deck", "kind": "pptx", "extension": ".pptx", "required": True}
                    ]
                },
            },
            {
                "id": "deck_structure",
                "type": "pptx_structure",
                "weight": 0.8,
                "threshold": 0.9,
                "required": True,
                "config": {
                    "artifact_id": "deck",
                    "min_slides": 2,
                    "max_slides": 2,
                    "min_charts": 1,
                    "min_tables": 1,
                    "required_keywords": ["sales", "recommendation"],
                    "require_widescreen": True,
                },
            },
        ],
    }


def write_submission(directory: Path, case_id: str, attempt_id: str = "run_1") -> None:
    write_json(
        directory / "submission.json",
        {
            "case_id": case_id,
            "attempt_id": attempt_id,
            "final_report": "Done.",
            "process": [{"text": "created chart and rendered deck"}],
            "artifacts": [{"id": "deck", "kind": "pptx", "path": "deck.pptx"}],
        },
    )

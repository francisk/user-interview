#!/usr/bin/env python3
"""Validate the shape of trigger and behavior evaluation catalogs."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


BEHAVIOR_HEADING = re.compile(r"^##\s+([0-9]+[a-z]?)\.\s+.+$", re.MULTILINE)
REQUIRED_BEHAVIOR_FIELDS = (
    "名称",
    "用户请求",
    "预期行为",
    "确定性检查",
    "语义判定 rubric",
    "失败迹象",
)


class CatalogValidationError(ValueError):
    pass


def validate_triggers(path: Path) -> int:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != ["id", "should_trigger", "prompt"]:
                raise CatalogValidationError(
                    "trigger catalog columns must be id, should_trigger, prompt"
                )
            rows = list(reader)
    except OSError as error:
        raise CatalogValidationError(f"cannot read trigger catalog: {error}") from error

    if not rows:
        raise CatalogValidationError("trigger catalog is empty")

    seen: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        trigger_id = (row.get("id") or "").strip()
        if not trigger_id:
            raise CatalogValidationError(f"trigger row {row_number} has empty id")
        if trigger_id in seen:
            raise CatalogValidationError(f"duplicate trigger id: {trigger_id}")
        seen.add(trigger_id)
        if (row.get("should_trigger") or "").strip().lower() not in {"true", "false"}:
            raise CatalogValidationError(f"trigger {trigger_id} has invalid should_trigger")
        if not (row.get("prompt") or "").strip():
            raise CatalogValidationError(f"trigger {trigger_id} has empty prompt")
    return len(rows)


def validate_behaviors(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise CatalogValidationError(f"cannot read behavior catalog: {error}") from error

    matches = list(BEHAVIOR_HEADING.finditer(text))
    if not matches:
        raise CatalogValidationError("behavior catalog has no cases")

    seen: set[str] = set()
    for index, match in enumerate(matches):
        case_id = match.group(1)
        if case_id in seen:
            raise CatalogValidationError(f"duplicate behavior id: {case_id}")
        seen.add(case_id)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end]
        missing = [field for field in REQUIRED_BEHAVIOR_FIELDS if f"- {field}：" not in body]
        if missing:
            raise CatalogValidationError(
                f"behavior {case_id} missing fields: {', '.join(missing)}"
            )
    return len(matches)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--triggers", required=True, type=Path)
    parser.add_argument("--behaviors", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        trigger_count = validate_triggers(args.triggers)
        behavior_count = validate_behaviors(args.behaviors)
    except CatalogValidationError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, "trigger_count": trigger_count, "behavior_count": behavior_count}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

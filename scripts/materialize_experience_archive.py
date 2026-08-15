#!/usr/bin/env python3
"""Materialize a deterministic Experience reading archive for direct or weekly sources."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, NamedTuple, Optional, Sequence
from zoneinfo import ZoneInfo


ReplaceFunction = Callable[
    [str | bytes | os.PathLike[str] | os.PathLike[bytes], str | bytes | os.PathLike[str] | os.PathLike[bytes]],
    None,
]
SHANGHAI = ZoneInfo("Asia/Shanghai")
ALLOWED_SOURCE_MODES = {"weekly", "direct_session", "direct_document"}
DIRECT_SOURCE_MODES = {"direct_session", "direct_document"}
ALLOWED_CANDIDATE_STATUSES = {"new", "deferred", "interviewing", "closed", "completed"}
REQUIRED_EPISODE_FIELDS = {
    "episode_id",
    "candidate_id",
    "project_id",
    "occurred_at",
    "evidence_ceiling",
    "confirmation_source",
    "final_checkpoint_source",
}
REPOSITORY_CONFIG_SCRIPT = Path(__file__).with_name("repository_config.py")


class ArchiveValidationError(RuntimeError):
    """The archive view cannot be safely derived from repository truth."""


class EpisodeRecord(NamedTuple):
    episode_id: str
    candidate_id: str
    project_id: str
    occurred_at: str
    evidence_ceiling: str
    source_path: str
    source_sha256: str
    title: str
    body_lines: tuple[str, ...]


def materialize_archive(
    repository: Path | str,
    archive_date: str,
    *,
    source_mode: Optional[str] = None,
    window_start: Optional[str] = None,
    window_end: Optional[str] = None,
    replace_func: ReplaceFunction = os.replace,
) -> dict[str, Any]:
    repository_path = Path(repository).resolve()
    candidates_directory, _ = _validate_repository_layout(repository_path)
    _parse_archive_date(archive_date)
    if source_mode is not None and source_mode not in ALLOWED_SOURCE_MODES:
        raise ArchiveValidationError(f"invalid source_mode: {source_mode}")
    if (window_start is None) != (window_end is None):
        raise ArchiveValidationError("window-start and window-end must be supplied together")
    if source_mode in DIRECT_SOURCE_MODES and window_start is not None:
        raise ArchiveValidationError("direct archive must not receive a weekly window")

    with _repository_lock(repository_path):
        candidates = [_read_candidate(path) for path in sorted(candidates_directory.glob("CAND-*.json"))]
        matching = [candidate for candidate in candidates if candidate.get("archive_date") == archive_date]
        modes = {candidate["_resolved_source_mode"] for candidate in matching}
        if not matching:
            modes = {source_mode or "weekly"}
        weekly_candidates = [candidate for candidate in matching if candidate["_resolved_source_mode"] == "weekly"]
        resolved_window = _resolve_weekly_window(
            archive_date,
            weekly_candidates,
            require_weekly="weekly" in modes,
            window_start=window_start,
            window_end=window_end,
        )
        records = [
            _validate_completed_pair(repository_path, candidate)
            for candidate in matching
            if candidate.get("status") == "completed"
        ]
        records.sort(key=lambda record: (_parse_occurrence(record.occurred_at), record.episode_id))
        output_bytes = _render_archive(archive_date, modes, resolved_window, records)
        output_path = repository_path / f"经验抽取{archive_date}.md"
        existing = output_path.read_bytes() if output_path.exists() else None
        if existing == output_bytes:
            changed = False
        else:
            _atomic_replace(output_path, output_bytes, replace_func)
            changed = True

    return {
        "ok": True,
        "archiveDate": archive_date,
        "sourceModes": sorted(modes),
        "path": str(output_path),
        "episodeCount": len(records),
        "episodeIds": [record.episode_id for record in records],
        "changed": changed,
    }


def _validate_repository_layout(repository: Path) -> tuple[Path, Path]:
    if not repository.is_dir() or repository.is_symlink():
        raise ArchiveValidationError("Experience Repository must be a real directory")
    candidates = repository / "candidates"
    episodes = repository / "episodes"
    for path in (candidates, episodes):
        if not path.is_dir() or path.is_symlink() or path.resolve().parent != repository:
            raise ArchiveValidationError("repository candidates/ and episodes/ must be real directories and must not be symlinks")
    return candidates, episodes


@contextmanager
def _repository_lock(repository: Path) -> Iterator[None]:
    lock_path = repository / ".candidate-queue.lock"
    try:
        with lock_path.open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except OSError as error:
        raise ArchiveValidationError(f"repository lock failed: {type(error).__name__}") from error


def _read_candidate(path: Path) -> dict[str, Any]:
    if path.is_symlink() or path.resolve().parent != path.parent.resolve():
        raise ArchiveValidationError(f"candidate must be a regular repository file: {path.name}")
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ArchiveValidationError(f"candidate is unreadable: {path.name}") from error
    if not isinstance(candidate, dict):
        raise ArchiveValidationError(f"candidate must be a JSON object: {path.name}")
    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or path.name != f"{candidate_id}.json":
        raise ArchiveValidationError(f"candidate identity does not match filename: {path.name}")
    status = candidate.get("status")
    if status not in ALLOWED_CANDIDATE_STATUSES:
        raise ArchiveValidationError(f"candidate has invalid status: {path.name}")
    completed_episode = candidate.get("completed_episode")
    if status == "completed" and (not isinstance(completed_episode, str) or not completed_episode):
        raise ArchiveValidationError(f"completed Candidate lacks completed_episode: {candidate_id}")
    if status != "completed" and completed_episode is not None:
        raise ArchiveValidationError(f"Candidate completion pointer conflicts with status: {candidate_id}")

    mode = candidate.get("source_mode", "weekly")
    if mode not in ALLOWED_SOURCE_MODES:
        raise ArchiveValidationError(f"candidate has invalid source_mode: {path.name}")
    archive_date = candidate.get("archive_date")
    if not isinstance(archive_date, str) or not archive_date:
        raise ArchiveValidationError(f"candidate lacks archive metadata: {path.name}")
    _parse_archive_date(archive_date)
    start = candidate.get("archive_window_start")
    end = candidate.get("archive_window_end")
    if mode == "weekly":
        if start is None and end is None:
            raise ArchiveValidationError(f"candidate lacks archive metadata: {path.name}")
        if not isinstance(start, str) or not start or not isinstance(end, str) or not end:
            raise ArchiveValidationError(f"weekly Candidate has partial archive metadata: {path.name}")
        _validated_window(archive_date, start, end)
    elif start is not None or end is not None:
        raise ArchiveValidationError(f"direct Candidate must not contain archive window fields: {path.name}")
    candidate["_resolved_source_mode"] = mode
    return candidate


def _parse_archive_date(value: str) -> None:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError) as error:
        raise ArchiveValidationError("archive-date must use YYYY-MM-DD") from error
    if parsed.strftime("%Y-%m-%d") != value:
        raise ArchiveValidationError("archive-date must use YYYY-MM-DD")


def _parse_timestamp(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise ArchiveValidationError(f"{label} must be an RFC3339 timestamp") from error
    if parsed.tzinfo is None:
        raise ArchiveValidationError(f"{label} must include a timezone")
    return parsed


def _validated_window(archive_date: str, window_start: str, window_end: str) -> tuple[str, str]:
    start = _parse_timestamp(window_start, "window-start")
    end = _parse_timestamp(window_end, "window-end")
    if end - start != timedelta(seconds=604800):
        raise ArchiveValidationError("archive window must span exactly 604800 seconds")
    if end.astimezone(SHANGHAI).date().isoformat() != archive_date:
        raise ArchiveValidationError("archive-date must match window-end in Asia/Shanghai")
    return window_start, window_end


def _resolve_weekly_window(
    archive_date: str,
    weekly_candidates: list[dict[str, Any]],
    *,
    require_weekly: bool,
    window_start: Optional[str],
    window_end: Optional[str],
) -> Optional[tuple[str, str]]:
    candidate_windows = {
        (candidate["archive_window_start"], candidate["archive_window_end"])
        for candidate in weekly_candidates
    }
    if len(candidate_windows) > 1:
        raise ArchiveValidationError("candidates for archive-date have conflicting archive windows")
    candidate_window = next(iter(candidate_windows)) if candidate_windows else None
    supplied_window = (window_start, window_end) if window_start is not None and window_end is not None else None
    if candidate_window is not None and supplied_window is not None and candidate_window != supplied_window:
        raise ArchiveValidationError("supplied archive window conflicts with Candidate metadata")
    resolved = candidate_window or supplied_window
    if require_weekly and resolved is None:
        raise ArchiveValidationError("an empty archive requires window-start and window-end for weekly source")
    if resolved is None:
        return None
    return _validated_window(archive_date, resolved[0], resolved[1])


def _split_episode(data: bytes) -> tuple[dict[str, str], list[str]]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ArchiveValidationError("Episode is not valid UTF-8") from error
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    if not lines or lines[0] != "---":
        raise ArchiveValidationError("Episode is missing YAML frontmatter")
    try:
        closing = lines.index("---", 1)
    except ValueError as error:
        raise ArchiveValidationError("Episode frontmatter is not closed") from error
    scalars: dict[str, str] = {}
    for line in lines[1:closing]:
        if not line or line[0].isspace():
            continue
        if ":" not in line:
            raise ArchiveValidationError("Episode frontmatter is malformed")
        key, value = line.split(":", 1)
        if not key or not key.replace("_", "").isalnum() or key in scalars:
            raise ArchiveValidationError("Episode frontmatter is malformed")
        scalars[key] = value.strip()
    missing = sorted(field for field in REQUIRED_EPISODE_FIELDS if not scalars.get(field))
    if missing:
        raise ArchiveValidationError(f"Episode frontmatter lacks required fields: {missing}")
    if scalars["confirmation_source"] == "pending":
        raise ArchiveValidationError("Episode confirmation is pending")
    if scalars["final_checkpoint_source"] == "pending":
        raise ArchiveValidationError("Episode final checkpoint is pending")
    body_lines = lines[closing + 1 :]
    while body_lines and not body_lines[0]:
        body_lines.pop(0)
    return scalars, body_lines


def _parse_occurrence(value: str) -> datetime:
    parts = value.split("/")
    if len(parts) not in {1, 2} or any(not part for part in parts):
        raise ArchiveValidationError(f"Episode occurred_at is invalid: {value}")
    parsed_parts: list[datetime] = []
    for part in parts:
        try:
            parsed = datetime.fromisoformat(part.replace("Z", "+00:00"))
        except ValueError as error:
            raise ArchiveValidationError(f"Episode occurred_at is invalid: {value}") from error
        if len(part) == 10:
            parsed = parsed.replace(tzinfo=SHANGHAI)
        elif parsed.tzinfo is None:
            raise ArchiveValidationError(f"Episode occurred_at lacks a timezone: {value}")
        parsed_parts.append(parsed.astimezone(timezone.utc))
    if len(parsed_parts) == 2 and parsed_parts[1] < parsed_parts[0]:
        raise ArchiveValidationError(f"Episode occurred_at interval is reversed: {value}")
    return parsed_parts[0]


def _validate_completed_pair(repository: Path, candidate: dict[str, Any]) -> EpisodeRecord:
    candidate_id = candidate["candidate_id"]
    episode_path = Path(candidate["completed_episode"])
    if episode_path.is_symlink():
        raise ArchiveValidationError(f"completed Episode must not be a symlink: {candidate_id}")
    try:
        resolved_episode = episode_path.resolve(strict=True)
    except OSError as error:
        raise ArchiveValidationError(f"completed Episode is missing: {candidate_id}") from error
    if resolved_episode.parent != (repository / "episodes").resolve():
        raise ArchiveValidationError(f"completed Episode is outside repository episodes: {candidate_id}")
    try:
        data = resolved_episode.read_bytes()
    except OSError as error:
        raise ArchiveValidationError(f"completed Episode is unreadable: {candidate_id}") from error
    frontmatter, body_lines = _split_episode(data)
    if frontmatter["candidate_id"] != candidate_id:
        raise ArchiveValidationError(f"Episode candidate_id mismatch: {candidate_id}")
    if frontmatter["project_id"] != candidate.get("project_id"):
        raise ArchiveValidationError(f"Episode project_id mismatch: {candidate_id}")
    episode_id = frontmatter["episode_id"]
    if not resolved_episode.name.startswith(f"{episode_id}-"):
        raise ArchiveValidationError(f"Episode ID does not match filename: {resolved_episode.name}")
    _parse_occurrence(frontmatter["occurred_at"])
    if not body_lines or not body_lines[0].startswith("# "):
        raise ArchiveValidationError(f"Episode body lacks a title: {episode_id}")
    title = body_lines[0][2:].strip()
    if not title:
        raise ArchiveValidationError(f"Episode title is empty: {episode_id}")
    transformed: list[str] = []
    fence: Optional[tuple[str, int]] = None
    for line in body_lines[1:]:
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        if indent <= 3 and stripped and stripped[0] in {"`", "~"}:
            marker = stripped[0]
            count = len(stripped) - len(stripped.lstrip(marker))
            if count >= 3:
                if fence is None:
                    fence = (marker, count)
                elif marker == fence[0] and count >= fence[1] and not stripped[count:].strip():
                    fence = None
                transformed.append(line)
                continue
        if fence is None and indent <= 3 and stripped.startswith("#"):
            count = len(stripped) - len(stripped.lstrip("#"))
            if count < len(stripped) and stripped[count] == " ":
                line = line[:indent] + "#" + stripped
        transformed.append(line)
    while transformed and not transformed[0]:
        transformed.pop(0)
    return EpisodeRecord(
        episode_id,
        candidate_id,
        frontmatter["project_id"],
        frontmatter["occurred_at"],
        frontmatter["evidence_ceiling"],
        f"episodes/{resolved_episode.name}",
        hashlib.sha256(data).hexdigest(),
        title,
        tuple(transformed),
    )


def _render_archive(
    archive_date: str,
    modes: set[str],
    window: Optional[tuple[str, str]],
    records: list[EpisodeRecord],
) -> bytes:
    direct_present = bool(modes & DIRECT_SOURCE_MODES)
    lines = ["---", f"schema_version: {2 if direct_present else 1}", f"archive_date: {archive_date}"]
    if window is not None:
        lines.extend((f"window_start: {window[0]}", f"window_end: {window[1]}"))
    if direct_present:
        lines.append("source_modes:")
        lines.extend(f"  - {mode}" for mode in sorted(modes))
    lines.append(f"episode_count: {len(records)}")
    if records:
        lines.append("episode_ids:")
        lines.extend(f"  - {record.episode_id}" for record in records)
        lines.append("sources:")
        for record in records:
            lines.extend((f"  - path: {record.source_path}", f"    sha256: {record.source_sha256}"))
    else:
        lines.extend(("episode_ids: []", "sources: []"))
    lines.extend(("---", "", f"# 经验抽取 {archive_date}", ""))
    if window is not None:
        lines.extend((f"扫描窗口：`{window[0]}` 至 `{window[1]}`。", ""))
    else:
        lines.extend((f"归档日期：`{archive_date}`。", ""))
    lines.extend(("本文件是由已确认 Episode 确定性生成的阅读视图；审计真值保留在 `candidates/` 与 `episodes/`。", ""))
    if not records:
        empty = "截至本次生成，本周暂无已确认 Episode。" if modes == {"weekly"} else "截至本次生成，本日暂无已确认 Episode。"
        lines.extend((empty, ""))
        return "\n".join(lines).encode("utf-8")
    lines.extend(("## 目录", ""))
    for index, record in enumerate(records, start=1):
        lines.append(f"- [{record.title}](#experience-{index})")
    lines.append("")
    for index, record in enumerate(records, start=1):
        lines.extend((
            f'<a id="experience-{index}"></a>',
            "",
            f"## {record.title}",
            "",
            f"- Episode ID：`{record.episode_id}`",
            f"- 项目：`{record.project_id}`",
            f"- 发生时间：`{record.occurred_at}`",
            f"- 证据上限：`{record.evidence_ceiling}`",
            f"- 来源：`{record.source_path}`",
            "",
        ))
        lines.extend(record.body_lines)
        lines.extend(("", "---", ""))
    return "\n".join(lines).encode("utf-8")


def _atomic_replace(target: Path, data: bytes, replace_func: ReplaceFunction) -> None:
    temporary: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp", delete=False) as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        replace_func(temporary, target)
    except OSError as error:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise ArchiveValidationError(f"archive replacement failed: {type(error).__name__}") from error


def _require_configured_repository(repository: Path) -> None:
    try:
        result = subprocess.run(
            [sys.executable, str(REPOSITORY_CONFIG_SCRIPT), "check"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        raise ArchiveValidationError(f"Experience Repository gate could not run: {type(error).__name__}") from error
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ArchiveValidationError("Experience Repository gate returned invalid JSON") from error
    if result.returncode != 0 or payload.get("status") != "configured":
        detail = payload.get("error") or payload.get("status") or f"exit {result.returncode}"
        raise ArchiveValidationError(f"Experience Repository gate failed: {detail}")
    configured = payload.get("repository_path")
    if not isinstance(configured, str) or Path(configured).resolve() != repository.resolve():
        raise ArchiveValidationError("repository does not match the configured Experience Repository")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--archive-date", required=True)
    parser.add_argument("--source-mode", choices=sorted(ALLOWED_SOURCE_MODES))
    parser.add_argument("--window-start")
    parser.add_argument("--window-end")
    args = parser.parse_args(argv)
    try:
        _require_configured_repository(args.repository)
        result = materialize_archive(
            args.repository,
            args.archive_date,
            source_mode=args.source_mode,
            window_start=args.window_start,
            window_end=args.window_end,
        )
    except ArchiveValidationError as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

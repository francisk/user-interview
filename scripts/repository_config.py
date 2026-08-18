#!/usr/bin/env python3
"""Read or configure the local Experience Repository path."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def skill_config_path() -> Path:
    return Path(__file__).resolve().parents[1] / "extracting-human-agent-experience.json"


def resolve_config_path(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit.expanduser()
    return skill_config_path()


def emit(status: str, **fields: object) -> None:
    print(json.dumps({"status": status, **fields}, ensure_ascii=False))


def load_repository(config_path: Path) -> Path | None:
    if not config_path.is_file():
        return None
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = payload.get("repository_path")
    if not isinstance(value, str) or not value.strip():
        return None
    return Path(value).expanduser().resolve()


def ensure_layout(repository: Path) -> None:
    repository.mkdir(parents=True, exist_ok=True)
    if not repository.is_dir():
        raise OSError(f"not a directory: {repository}")
    for name in ("candidates", "episodes"):
        (repository / name).mkdir(exist_ok=True)
    probe = repository / ".write-test"
    probe.write_text("ok", encoding="utf-8")
    probe.unlink()


def atomic_write_config(config_path: Path, repository: Path) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = config_path.with_suffix(config_path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps({"repository_path": str(repository)}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temp_path, config_path)


def command_check(config_path: Path) -> int:
    repository = load_repository(config_path)
    if repository is None:
        emit("needs_configuration", config_path=str(config_path))
        return 2
    try:
        ensure_layout(repository)
    except OSError as exc:
        emit("repository_unavailable", repository_path=str(repository), error=str(exc))
        return 3
    emit("configured", repository_path=str(repository), config_path=str(config_path))
    return 0


def command_configure(config_path: Path, repository: Path) -> int:
    repository = repository.expanduser().resolve()
    try:
        ensure_layout(repository)
        atomic_write_config(config_path, repository)
    except OSError as exc:
        emit("repository_unavailable", repository_path=str(repository), error=str(exc))
        return 3
    emit("configured", repository_path=str(repository), config_path=str(config_path))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check")
    check.add_argument("--config", type=Path)

    configure = subparsers.add_parser("configure")
    configure.add_argument("--config", type=Path)
    configure.add_argument("--repository", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = resolve_config_path(args.config)
    if args.command == "check":
        return command_check(config_path)
    return command_configure(config_path, args.repository)


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "materialize_experience_archive.py"
ARCHIVE_DATE = "2026-08-15"
WINDOW_START = "2026-08-08T12:00:00+08:00"
WINDOW_END = "2026-08-15T12:00:00+08:00"


def load_materializer():
    spec = importlib.util.spec_from_file_location("portable_experience_materializer", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("portable Experience materializer cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def episode_bytes(candidate_id: str, episode_id: str, title: str) -> bytes:
    return f"""---
episode_id: {episode_id}
candidate_id: {candidate_id}
owner: Human + stable Coding Agent
project_id: portable-project
occurred_at: 2026-08-15
source_sessions:
  - session#turn
evidence_ceiling: discussion
confirmed_at: 2026-08-15T13:00:00+08:00
confirmation_source: session#confirm
final_checkpoint_source: session#final
related_episodes: []
runtime:
  harness: Codex
---

# {title}

完整叙事。
""".encode("utf-8")


def candidate_value(
    repository: Path,
    candidate_id: str,
    episode_id: str,
    *,
    source_mode: str | None,
) -> dict:
    episode_path = repository / "episodes" / f"{episode_id}-episode.md"
    value = {
        "candidate_id": candidate_id,
        "source_fingerprint": candidate_id.rsplit("-", 1)[-1],
        "project_id": "portable-project",
        "source_sessions": ["session#turn"],
        "source_turn_ids": ["before", "interaction", "after"],
        "change": {"before": "before", "interaction": "interaction", "after": "after"},
        "human_intervention": {"deny": None, "guide": "guide"},
        "brief": "brief",
        "qualification": {"why_not_ordinary": "change", "evidence_gap": "无", "relationship": "new"},
        "status": "completed",
        "archive_date": ARCHIVE_DATE,
        "created_at": "2026-08-15T12:00:00+08:00",
        "completed_episode": str(episode_path),
    }
    if source_mode is not None:
        value["source_mode"] = source_mode
    if source_mode in {None, "weekly"}:
        value["archive_window_start"] = WINDOW_START
        value["archive_window_end"] = WINDOW_END
    return value


class PortableExperienceArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repository = Path(self.temp.name) / "experience"
        (self.repository / "candidates").mkdir(parents=True)
        (self.repository / "episodes").mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def add_candidate(self, candidate_id: str, episode_id: str, source_mode: str | None) -> None:
        (self.repository / "episodes" / f"{episode_id}-episode.md").write_bytes(
            episode_bytes(candidate_id, episode_id, episode_id)
        )
        value = candidate_value(self.repository, candidate_id, episode_id, source_mode=source_mode)
        (self.repository / "candidates" / f"{candidate_id}.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def test_direct_candidate_renders_without_weekly_window(self):
        self.add_candidate("CAND-20260815-aaaaaaaa", "EXP-20260815-aaaaaaaa", "direct_session")
        materializer = load_materializer()

        result = materializer.materialize_archive(self.repository, ARCHIVE_DATE)

        output = Path(result["path"]).read_text(encoding="utf-8")
        self.assertIn("schema_version: 2", output)
        self.assertIn("source_modes:\n  - direct_session", output)
        self.assertNotIn("window_start:", output)
        self.assertNotIn("扫描窗口：", output)
        self.assertIn("归档日期：`2026-08-15`", output)

    def test_legacy_candidate_without_source_mode_remains_weekly(self):
        self.add_candidate("CAND-20260815-bbbbbbbb", "EXP-20260815-bbbbbbbb", None)
        materializer = load_materializer()

        materializer.materialize_archive(self.repository, ARCHIVE_DATE)

        output = (self.repository / f"经验抽取{ARCHIVE_DATE}.md").read_text(encoding="utf-8")
        self.assertIn("schema_version: 1", output)
        self.assertIn(f"window_start: {WINDOW_START}", output)
        self.assertNotIn("source_modes:", output)

    def test_mixed_direct_and_weekly_candidates_share_one_archive(self):
        self.add_candidate("CAND-20260815-aaaaaaaa", "EXP-20260815-aaaaaaaa", "direct_document")
        self.add_candidate("CAND-20260815-bbbbbbbb", "EXP-20260815-bbbbbbbb", "weekly")
        materializer = load_materializer()

        result = materializer.materialize_archive(self.repository, ARCHIVE_DATE)

        output = Path(result["path"]).read_text(encoding="utf-8")
        self.assertEqual(result["episodeCount"], 2)
        self.assertIn("schema_version: 2", output)
        self.assertIn("  - direct_document", output)
        self.assertIn("  - weekly", output)
        self.assertIn(f"window_start: {WINDOW_START}", output)

    def test_direct_candidate_with_window_is_rejected_without_overwrite(self):
        self.add_candidate("CAND-20260815-aaaaaaaa", "EXP-20260815-aaaaaaaa", "direct_session")
        candidate_path = self.repository / "candidates" / "CAND-20260815-aaaaaaaa.json"
        value = json.loads(candidate_path.read_text(encoding="utf-8"))
        value["archive_window_start"] = WINDOW_START
        value["archive_window_end"] = WINDOW_END
        candidate_path.write_text(json.dumps(value), encoding="utf-8")
        output_path = self.repository / f"经验抽取{ARCHIVE_DATE}.md"
        output_path.write_bytes(b"sentinel\n")
        materializer = load_materializer()

        with self.assertRaisesRegex(materializer.ArchiveValidationError, "direct Candidate must not contain"):
            materializer.materialize_archive(self.repository, ARCHIVE_DATE)

        self.assertEqual(output_path.read_bytes(), b"sentinel\n")

    def test_weekly_candidate_requires_complete_window(self):
        self.add_candidate("CAND-20260815-aaaaaaaa", "EXP-20260815-aaaaaaaa", "weekly")
        candidate_path = self.repository / "candidates" / "CAND-20260815-aaaaaaaa.json"
        value = json.loads(candidate_path.read_text(encoding="utf-8"))
        value.pop("archive_window_end")
        candidate_path.write_text(json.dumps(value), encoding="utf-8")
        materializer = load_materializer()

        with self.assertRaisesRegex(materializer.ArchiveValidationError, "weekly Candidate has partial archive metadata"):
            materializer.materialize_archive(self.repository, ARCHIVE_DATE)

    def test_empty_direct_archive_needs_no_window(self):
        materializer = load_materializer()

        result = materializer.materialize_archive(
            self.repository, ARCHIVE_DATE, source_mode="direct_session"
        )

        output = Path(result["path"]).read_text(encoding="utf-8")
        self.assertEqual(result["episodeCount"], 0)
        self.assertNotIn("window_start:", output)

    def test_empty_weekly_archive_requires_exact_window(self):
        materializer = load_materializer()

        with self.assertRaisesRegex(materializer.ArchiveValidationError, "empty.*archive requires"):
            materializer.materialize_archive(self.repository, ARCHIVE_DATE, source_mode="weekly")

        result = materializer.materialize_archive(
            self.repository,
            ARCHIVE_DATE,
            source_mode="weekly",
            window_start=WINDOW_START,
            window_end=WINDOW_END,
        )
        self.assertEqual(result["episodeCount"], 0)

    def test_invalid_source_mode_is_rejected_without_overwrite(self):
        self.add_candidate("CAND-20260815-aaaaaaaa", "EXP-20260815-aaaaaaaa", "unknown")
        output_path = self.repository / f"经验抽取{ARCHIVE_DATE}.md"
        output_path.write_bytes(b"sentinel\n")
        materializer = load_materializer()

        with self.assertRaisesRegex(materializer.ArchiveValidationError, "invalid source_mode"):
            materializer.materialize_archive(self.repository, ARCHIVE_DATE)

        self.assertEqual(output_path.read_bytes(), b"sentinel\n")


if __name__ == "__main__":
    unittest.main()

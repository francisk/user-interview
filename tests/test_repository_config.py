import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "repository_config.py"


class RepositoryConfigTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_missing_config_requests_configuration_without_guessing(self):
        with tempfile.TemporaryDirectory() as td:
            config = Path(td) / "config.json"
            result = self.run_cli("check", "--config", config)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["status"], "needs_configuration")
            self.assertFalse(config.exists())

    def test_empty_repository_path_requests_configuration(self):
        with tempfile.TemporaryDirectory() as td:
            config = Path(td) / "config.json"
            config.write_text('{"repository_path": ""}', encoding="utf-8")
            result = self.run_cli("check", "--config", config)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["status"], "needs_configuration")

    def test_configure_creates_repository_layout_and_check_resolves_it(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config = root / "agent-config" / "config.json"
            repository = root / "experience-repository"
            configured = self.run_cli(
                "configure", "--config", config, "--repository", repository
            )
            self.assertEqual(configured.returncode, 0, configured.stderr)
            self.assertTrue((repository / "candidates").is_dir())
            self.assertTrue((repository / "episodes").is_dir())

            checked = self.run_cli("check", "--config", config)
            payload = json.loads(checked.stdout)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(payload["status"], "configured")
            self.assertEqual(payload["repository_path"], str(repository.resolve()))

    def test_unusable_repository_does_not_fall_back_elsewhere(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config = root / "config.json"
            blocked = root / "not-a-directory"
            blocked.write_text("file", encoding="utf-8")
            result = self.run_cli(
                "configure", "--config", config, "--repository", blocked
            )
            self.assertEqual(result.returncode, 3)
            self.assertEqual(json.loads(result.stdout)["status"], "repository_unavailable")
            self.assertFalse(config.exists())


if __name__ == "__main__":
    unittest.main()

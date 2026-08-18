import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "repository_config.py"


class RepositoryConfigTests(unittest.TestCase):
    def run_cli(self, *args, env=None, script=SCRIPT):
        return subprocess.run(
            [sys.executable, str(script), *map(str, args)],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

    def isolated_env(self, home: Path) -> dict[str, str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env.pop("XDG_CONFIG_HOME", None)
        return env

    def install_script(self, root: Path) -> Path:
        script = root / "scripts" / "repository_config.py"
        script.parent.mkdir(parents=True)
        shutil.copy2(SCRIPT, script)
        return script

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

    def test_default_config_path_is_in_skill_root(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            skill_root = home / ".agents" / "skills" / "extracting-human-agent-experience"
            script = self.install_script(skill_root)
            repository = home / "experience-repository"
            result = self.run_cli(
                "configure",
                "--repository",
                repository,
                env=self.isolated_env(home),
                script=script,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            expected = skill_root / "extracting-human-agent-experience.json"
            self.assertEqual(Path(payload["config_path"]).resolve(), expected.resolve())
            self.assertTrue(expected.is_file())
            self.assertFalse((home / ".config" / "user-interview").exists())

if __name__ == "__main__":
    unittest.main()

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_eval_catalog.py"


class EvalCatalogTests(unittest.TestCase):
    def test_trigger_and_behavior_catalogs_are_structurally_valid(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--triggers",
                str(ROOT / "references" / "trigger-tests.csv"),
                "--behaviors",
                str(ROOT / "references" / "eval-cases.md"),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"trigger_count": 21', result.stdout)
        self.assertIn('"behavior_count": 23', result.stdout)

    def test_duplicate_trigger_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            triggers = root / "triggers.csv"
            behaviors = root / "behaviors.md"
            triggers.write_text(
                "id,should_trigger,prompt\n"
                'same,true,"one"\n'
                'same,false,"two"\n',
                encoding="utf-8",
            )
            behaviors.write_text(
                "## 1. Case\n\n"
                "- 名称：Case\n"
                "- 用户请求：request\n"
                "- 预期行为：expected\n"
                "- 确定性检查：check\n"
                "- 语义判定 rubric：rubric\n"
                "- 失败迹象：failure\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--triggers", str(triggers), "--behaviors", str(behaviors)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate trigger id", result.stderr)

    def test_incomplete_behavior_case_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            triggers = root / "triggers.csv"
            behaviors = root / "behaviors.md"
            triggers.write_text(
                'id,should_trigger,prompt\none,true,"prompt"\n',
                encoding="utf-8",
            )
            behaviors.write_text(
                "## 1. Case\n\n- 名称：Case\n- 用户请求：request\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--triggers", str(triggers), "--behaviors", str(behaviors)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing fields", result.stderr)


if __name__ == "__main__":
    unittest.main()

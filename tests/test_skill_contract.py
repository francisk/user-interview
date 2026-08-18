import unittest
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


class SkillContractTests(unittest.TestCase):
    def test_runtime_commands_are_relative_to_loaded_skill_root(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertNotIn("~/.codex/skills/extracting-human-agent-experience", text)
        self.assertNotIn("~/.agents/skills/extracting-human-agent-experience", text)
        self.assertIn("skill_root", text)

    def test_interview_start_requires_a_complete_context_card(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("访谈启动上下文卡", text)
        for required_part in ("当时的情况", "你做的取舍", "后来变成什么", "现在还不能说什么"):
            self.assertIn(required_part, text)

    def test_user_facing_interviewer_has_a_warm_listening_voice(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("深听型 + 教练型", text)
        self.assertIn("先接住", text)
        self.assertIn("对立转折模板", text)

    def test_user_facing_pronouns_identify_human_and_agent_roles(self) -> None:
        text = SKILL.read_text(encoding="utf-8")

        self.assertIn("我（Agent）", text)
        self.assertIn("你（人类）", text)


if __name__ == "__main__":
    unittest.main()

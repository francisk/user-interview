# Release Notes

## 2026-08-18

本次更新修复了公开 Skill 在不同 Agent 安装目录中的可移植性问题，并补充了可重复执行的评估目录检查。

### 安装修复

- Skill 现在从实际加载的 `SKILL.md` 确定 `skill_root`，所有随附脚本都从该目录调用。
- 不再假设 Skill 一定安装在 `~/.codex/skills`；安装到 `~/.agents/skills` 或 Agent 支持的其他目录时也可运行。
- 无法确定 Skill 根目录或脚本缺失时会明确停止，不会搜索其他目录或误用另一份安装。

### 配置位置

- Experience Repository 配置保存在 Skill 根目录的 `extracting-human-agent-experience.json`。
- 该本地配置已被 `.gitignore` 排除，不会随代码提交到 GitHub。
- 更新后首次运行若尚无根目录配置，Agent 会重新询问一次 Experience Repository 路径。

### 评估与测试

- 新增评估目录校验器，检查触发用例和行为用例的重复编号、无效字段与必要栏目缺失。
- 当前目录包含 21 个触发用例和 22 个行为用例。
- 自动目录校验只证明评估资料结构完整，不代表目标模型已经逐项通过自然语言行为评估。
- 新增安装路径和 Skill 根目录配置回归测试。

### 保持不变

- 没有新增 Candidate/Episode 保存器或状态机。
- 没有改变 weekly 上游集成、经验认定规则、访谈流程和确认流程。

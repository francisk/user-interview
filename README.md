# User Interview

> 把一次真实发生的人机协作，整理成由人本人确认的经验记录。

`User Interview` 是一个面向 Codex 等 Agent 环境的个人 Skill。它会通过回顾一次你和ai的对话，一段项目的历史，一份文档产物，帮助你找到其中真正发生的变化：在一开始的时候AI的决策是什么、人与 Agent 如何共同推进或纠正、最后什么判断或行动已经不同。它试图帮助用户思考一个问题：我做了哪些独立于AI的，基于个人经验的判断，这些判断总结下来如何形成了我的个人风格。

仓库中的 Skill 名称是 `extracting-human-agent-experience`。

## 它解决什么问题

很多有价值的经验散落在对话和文档里：

- 你否定了 Agent 的一个方向，问题因此被重新定义；
- Agent 把一个隐喻或直觉翻译成了产品决策；
- 你逐步补充边界，最终形成一条以后仍值得复用的原则；
- 一份方案经过讨论后，已经出现了真实的判断或行动变化。

普通总结通常只记录“做了什么”。这个 Skill 更关心：**变化是怎样发生的，人的判断发挥了什么作用，Human 和 Agent 分别贡献了什么。**

只有已经出现真实后续变化的协作才会成为 Candidate。单独的建议、批准、普通问答、状态确认或尚未执行的计划，不会被包装成经验。

## 什么时候使用

你可以直接对 Agent 说：

```text
提取这次人机协作的经验。
```

```text
复盘当前对话里真正发生的变化。
```

```text
从 /path/to/运营方案.md 开始提取经验。
```

```text
继续 CAND-20260815-ab12cd34。
```

Skill 支持四种入口，按以下顺序选择：

1. **已有 Candidate ID**：恢复之前中断的访谈。
2. **明确提供的 weekly Manifest**：接入上游周报批量流程，适合已经配置该系统的高级用户。
3. **一份指定文档**：只读取这份文档和当前对话，不扫描同目录文件。
4. **当前 Session**：使用当前完整对话，不扫描历史 Session 或工作区。

普通用户只需要当前 Session 或一份文档，不需要理解周报链路。

## 一次访谈怎样进行

完整流程保持克制：

1. Agent 判断是否已经存在可定位的“变化前 → 关键交互 → 变化后”。
2. 信息不足时，先说明当前理解，每轮只问一个真正影响判断的问题。
3. Candidate 成立后，提供 `现在聊 / 留后 / 不值得记录`。
4. 选择“现在聊”后，访谈只补齐关键变化、人的介入和双方贡献。
5. Agent 展示 Confirmation Brief，并请你确认经历还原和贡献归属。
6. Agent 展示完整 Episode 草稿，只提供 `补充 / 直接通过`。
7. 只有你选择“直接通过”后，Episode 才会正式保存。

访谈不是固定问卷。已经清楚的事情不会要求你重复回答。

## 心境是可选的补充

一次选择有时不只来自技法，也与人当时的感受和心境有关。关键变化基本明确后，Skill 可以开放地邀请一次：

> 回到当时，你处在怎样的心境里？这种心境是否影响了你作出这个选择？

这不是必答题，我们希望每个人类自己的声音，思想能够被记录下来，而不是被AI的决策淹没：

- 你说什么，Agent就忠实的记录什么；
- Agent不会替你解释、评价或诊断；
- Agent不会从语气、冲突或结果反推情绪；
- 不知道、说不清、不想回答时，直接省略，不追问、不留占位；
- 是否回答，不影响 Candidate 确认和 Episode 保存。

## 最终保存什么

第一次运行时，Agent 会请你指定一个个人 Experience Repository。正式数据只保存在这个目录：

```text
<experience-repository>/
  candidates/
    CAND-YYYYMMDD-8hex.json
  episodes/
    EXP-YYYYMMDD-8hex-*.md
  经验抽取YYYY-MM-DD.md
```

- **Candidate** 保存来源、访谈状态和已经接受的理解。
- **Episode** 是经过两次人工确认的正式经历。
- **日期 Markdown** 是从 Candidate 和 Episode 确定性生成的阅读视图，方便按时间阅读。

Candidate 和 Episode 是事实来源；日期 Markdown 只是阅读视图。

## 安装

### Codex personal Skill

```bash
git clone https://github.com/francisk/user-interview.git \
  ~/.codex/skills/extracting-human-agent-experience
```

### 使用跨 Agent 的 Skill 目录

```bash
git clone https://github.com/francisk/user-interview.git \
  ~/.agents/skills/extracting-human-agent-experience
```

重新打开 Agent 任务后，使用上面的触发语即可。首次保存时，Agent 只会询问一个 Experience Repository 路径。

## Python 运行环境

业务用户不需要维护 venv。

在 Codex 桌面中，Skill 优先使用 Codex 自带的 Python；本机 Python 3.10 以上只作为备用。两者都不可用时，Skill 会在读取 Session、文档或经验仓库之前停止，并明确报告运行环境缺失。

脚本只使用 Python 标准库，不需要安装第三方包。当前实现使用 `fcntl` 保护本地并发写入，已在 macOS 环境验证；Windows 尚未作为受支持环境验证。

## 隐私与边界

这个公开仓库不包含任何个人经验数据。你的本地配置和 Experience Repository 也不应提交到本仓库。

直接使用时，Skill 遵守以下边界：

- 当前 Session 模式不扫描历史 Session；
- 文档模式只读取你明确指定的一份文件；
- 仓库未配置或不可用时停止，不猜测备用目录；
- Agent 不能创造消息、locator、哈希、项目身份或实现结果；
- 未确认的草稿不能写成正式 Episode；
- 保存 Episode 后结束，不顺手生成简历、Agent Profile 或新的 Skill。

## 不是什么

它不是：

- 普通聊天总结器；
- 心理测评或情绪分析工具；
- 自动把每段对话都写成“经验”的收集器；
- 简历、绩效材料或 Agent Profile 生成器；
- 单凭讨论就宣称功能已经实现的证明工具。

## 仓库结构

```text
SKILL.md                 # Agent 执行入口和完整工作流
scripts/                 # 仓库配置与确定性阅读归档
references/              # 数据契约、质量规则和行为用例
tests/                   # 标准库 unittest 测试
README.md                # 面向人的介绍和使用说明
```

## 验证

贡献者可以使用任意 Python 3.10 以上解释器运行测试，不需要安装 pytest：

```bash
EXPERIENCE_PYTHON=/absolute/path/to/python3
"$EXPERIENCE_PYTHON" -m unittest discover -s tests -p 'test_*.py' -v
```

当前测试覆盖仓库配置、不可用路径的停止行为、直接来源与 weekly 来源的归档兼容、原子替换和错误输入保护。

## License

[MIT](LICENSE)

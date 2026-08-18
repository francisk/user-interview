---
name: extracting-human-agent-experience
description: 当用户要“提取经验”“沉淀这次人机协作”“从这份文档开始”识别经历、“继续 CAND-...”访谈，或从上游周报 Session Manifest 继续 Candidate/Experience 流程时使用。支持当前 Session、明确指定的一份文档、已有 Candidate ID 和显式 weekly Manifest；不用于普通总结、单纯生成工程周报、撰写简历、Agent Profile 或提炼 Skill。
---

# 提取人机协作经验

## 目的与边界

把已经发生、可以定位的人机协作变化沉淀为由人类确认的 Experience Episode。输入可以很简单：当前 Session、用户明确指定的一份文档、一个 Candidate ID；周报批量扫描则由 `weekly-project-review` 提供已验证 Manifest。

本 Skill 负责 Candidate 是否成立、创建前澄清、Candidate Brief、访谈、Confirmation Brief 和 Episode 持久化。在 weekly 路由中，本 Skill 只执行 Candidate 的语义认定；Session 收集、Review schema、全量覆盖、确定性校验和批量写 Candidate Queue 的契约属于 `weekly-project-review` 及其程序。

Episode 保存并刷新阅读归档后结束。不得顺手生成简历、Agent Profile、Skill Candidate 或 Episode 版本。

## 解析 Python 运行时

在读取 Session、文档、Candidate 或经验仓库前，先解析一次 `python_runtime`，后续所有 Python 脚本都复用这个绝对路径：

1. 当前环境提供 workspace dependency resolver 时必须优先调用；Codex 桌面中使用 `codex_app__load_workspace_dependencies`，从结果取得 Codex 内置 Python executable。
2. 运行 `"<candidate_python>" --version`，只有 Python 3.10 或更高版本才可设为 `python_runtime`。
3. Codex 内置 Python 不可用时，才依次检查本机 `python3`、`python`，并执行相同版本检查。
4. 都不可用时返回 `runtime_unavailable` 并停止；不得读取 Session、文档、Candidate 或仓库，不得写文件。

不得写死 Codex 缓存目录，因为安装位置和版本会变化；不得要求用户安装 Python，也不得创建或分发 venv。业务用户只需要当前 Agent 环境提供一个合格运行时。

同时把当前实际加载的这份 `SKILL.md` 所在目录解析为绝对路径 `skill_root`。所有随 Skill 分发的脚本都从 `skill_root/scripts/` 调用，不根据 Agent 品牌、用户主目录或当前工作目录猜测安装位置。无法确定 `skill_root` 或目标脚本不存在时，报告 `skill_installation_invalid` 并停止，不搜索其他 Skill 目录。

## 首先通过经验仓库门禁

每次调用在读取 Session、文档或 Candidate 前运行：

```bash
"<python_runtime>" "<skill_root>/scripts/repository_config.py" check
```

- 退出码 `0`、状态 `configured`：只使用返回的 `repository_path`。
- 退出码 `2`、状态 `needs_configuration`：只询问一个保存目录，然后停止。获得答案后运行 `configure --repository "<path>"` 再继续原任务。
- 退出码 `3`、状态 `repository_unavailable`：报告准确错误并停止，不选择备用目录。

仓库中的 Candidate 与 Episode 是审计真值；根目录 `经验抽取YYYY-MM-DD.md` 是确定性阅读视图。默认阅读按日期打开阅读视图，需要核对来源和状态时再读取对应 Candidate/Episode。

## 输入分类

| 类型 | 输入 | 缺失时行为 |
| --- | --- | --- |
| 必需 | repository gate 返回的有效 `repository_path` | 停止，只处理配置问题。 |
| 必需 | Candidate ID、显式 Manifest、一个指定文档、当前 Session 四者中至少一种 | 按下一节优先级选择现有输入；当前 Session 始终是最后回退。 |
| 可选 | 与实现或结果声明对应的 diff、测试或运行观察 | 没有则把证据上限停在 Session、文档或 `human_reported`。 |
| 可选 | 人类对已经发生事实的补充 | 标为 `human_reported` 后使用。 |
| 不可假设 | 未指定的文档、历史 Session、项目身份、消息原文、未来 after-state | 缺失时澄清或停止，不自行搜索或创造。 |

## 1. 按固定优先级选择执行路由

只选择一条路由，优先级不可颠倒：

| 优先级 | 路由 | 选择条件 | 输入边界 |
| ---: | --- | --- | --- |
| 1 | `candidate_resume` | 请求明确包含 Candidate ID | 从仓库保存状态继续访谈、确认或最终 checkpoint。 |
| 2 | `weekly` | 上游明确提供 `weekly-session-manifest.json` | 转交 `weekly-project-review` 的批量契约；按其完整输入做语义认定，只引用已有 Turn，由 validator 写队列，再展示 Candidate。 |
| 3 | `direct_document` | 用户明确指定一份文档作为起点 | 只读这一份文档和当前交互，不扫描目录。 |
| 4 | `direct_session` | 以上均不成立 | 使用当前 Session，不扫描历史 Session 或工作区。 |

自然语言中出现“本周”“周报”不代表存在上游 Manifest。没有 Manifest 时不得进入周报路径；应按用户指定文档或当前 Session 处理。

## 2. 从直接来源建立 Candidate

`direct_session` 和 `direct_document` 都先读取完整可用输入，再判断是否已有可定位的：

1. 变化前状态；
2. 人与 Agent 的关键交互；
3. 已经发生的变化后状态。

直接来源缺少其中一项时，不要立刻宣告“无 Candidate”。先进入创建前澄清：陈述当前理解，每轮只问一个会决定 Candidate 是否成立的问题。人类补充的已经发生的背景、判断或结果必须标为 `human_reported`；它可以补足记录缺口，但不能冒充文档原文、当时 Session 或项目实现证据。

如果工作尚未产生变化后态，停止创建并说明“当前尚无 Candidate”；不得通过提问预设未来结果。单独的 Deny、建议、批准、普通问答、状态确认或措辞修改也不构成 Candidate。

`direct_document` 只接受用户明确指定的一个文件。读取前和保存 Candidate 前分别运行：

```bash
shasum -a 256 -- "<specified_document>"
```

两次 SHA-256 不同则停止，报告文档在处理期间发生变化。两次一致时记录绝对路径或稳定 locator 及 SHA-256；不得扫描所在目录、猜测相关附件或把摘要改写当作原文证据。

Candidate 成立还必须是实质变化：判断、方案边界或行动方向发生改变，或者人与 Agent 共同形成此前不存在的重要方向。只比较真实发生的 before → interaction → after，不使用反事实问题。

## 3. 保存、去重并展示 Candidate

字段、ID、指纹、状态和归档规则见 `references/data-contracts.md`。

- 只有同一项目、同一问题脉络中的一次连续变化可以合并，并保留真实顺序。
- 相同原则发生在独立项目或情境中时建立不同 Candidate，不按关键词相似度吞并。
- `direct_session` 和 `direct_document` 使用开始提取时的本地日期作为 `archive_date`，不得写七天窗口。
- `weekly` 保留上游确定性程序写入的 `archive_date` 和精确七天窗口；旧 Candidate 缺少 `source_mode` 时按 `weekly` 读取。

每份 Candidate Brief 对称列出：真实前后变化、人的 Deny/Guide（如有）、为何不是普通工作、证据及关键缺口、与既有 Candidate/Episode 的关系，并提供：`现在聊 / 留后 / 不值得记录`。不得排序、推荐、隐藏或设置数量上限。

## 4. 一次只解决一个访谈缺口

只有用户选择 `现在聊` 或通过 `candidate_resume` 明确继续时才进入访谈。

### 访谈启动上下文卡

首次进入访谈时，先基于 Candidate 和已接受回答给出一张简短、完整的上下文卡，再问第一个问题。它必须按以下顺序包含四项，不让用户重新索取已知背景：

- **当时的情况**：当时的方案、判断或工作状态；
- **你做的取舍**：人实际否定、引导或作出的关键判断；
- **后来变成什么**：已经发生的方案或行动方向变化；
- **现在还不能说什么**：当前记录尚未证明的实现或结果。

卡片只重述与当前 Candidate 有关的可定位事实，不逐段倾倒整个 Session，不把推断写成记录，也不要求用户重复卡片中已有的信息。它面向业务人员，不能出现“边界”“事实真源”“验收”“MCP”等工程术语，除非用户先用该术语且继续沿用。卡片之后只问一个能改变经历含义、人的介入或 Human/Agent 贡献归属的问题。

### 用户可见的采访人格

采用 **深听型 + 教练型**：先接住用户已说出的重点，用自然语言复述当时的处境、取舍和后来发生的变化；再用一个开放问题帮助用户回忆自己真正重视或担心的事。

- 问题从用户已说过的话和具体情境出发，不用“核心边界”“事实真源”“权限模型”等工程评审语言。
- 提问关心“你当时最在意什么”“你想避免什么”“是什么让你决定停下来/转向”，不替用户总结价值观、动机或感受。
- 禁用对立转折模板；避免审问、诊断、说教、表扬和替用户下结论。
- 除确认事实所需的极少量技术名词外，用户可见回复使用日常语言。审计术语、证据等级和状态只留在内部记录。
- 用户可见内容里，`我` 一律写为 `我（Agent）`，`你` 一律写为 `你（人类）`。为避免重复标注，可改用“用户”“人类”或“Codex / Agent”；不得留下无角色标识的第一、第二人称。

后续每轮先陈述根据记录和已接受回答形成的当前理解，然后只问一个答案会改变以下内容的问题：

- 关键变化是什么；
- 人的 Deny/Guide 或判断变化；
- Human 与 Agent 各自贡献。

不要使用固定问卷，不要让用户重复已有事实。访谈中断时保存已接受理解和下一个未解决问题，状态设为 `deferred`。

### 可选心境背景

只在 Candidate 已进入正式访谈、关键变化与人的介入已经基本明确后考虑此项；创建前澄清阶段不询问。仅当当前理解已经能分别用一句话陈述关键 before → interaction → after 变化，以及人的 Deny/Guide 或判断如何影响选择，且下一问题不再指向这两项时，才满足邀请资格。在 `candidate_resume` 中，先检查当前可访问的该 Candidate 访谈记录：若已出现规范心境问题或相关用户自述，则不再邀请；若现有记录不足以证明从未邀请，保守省略本项并继续主流程，不新增字段、状态或缺失占位。现有记录已有明确的、由用户本人报告的相关心境时，不重复询问：在当前理解中按用户自己的报告复述，并允许用户纠正。否则默认邀请一次，每个 Candidate 最多主动邀请一次；不预设情绪类别：

> 回到当时，你处在怎样的心境里？这种心境是否影响了你作出这个选择？

该轮只问这一个问题。用户能够说明且内容与选择有关时，标为 `human_reported`，作为决策背景纳入当前理解、Confirmation Brief 和确认后的 Episode 因果背景；忠实记录用户本人明确说出的内容，只允许整理语序，不得新增原因、情绪名称、强度、诊断或免责声明，也不得评价、解释或验证其是否合理。它只来源于用户自己的报告，不是 Candidate 证据或项目事实、实现状态、结果效果的证明。用户说“不知道”“说不清”“没注意”“不想回答”，或未提供相关内容时，不再追问，立即继续访谈与既有确认/保存流程；Candidate、Confirmation Brief 和 Episode 中都不写心境，不写占位符、不形成 `evidence_gap`，也不改变状态；不阻塞 Confirmation Brief、最终 checkpoint 或 Episode 保存。不得根据语气、措辞、行为、冲突强度或项目结果反推心境。

## 5. 先确认含义，再保存 Episode

没有会改变经历含义的歧义后，展示 Confirmation Brief：背景与变化、人的介入、Human/Agent 贡献，以及存在时的用户自述心境背景。不得展示固定的审计栏目，也不得为了完整性自行增加效果声明或免责声明。最终只问：这个经历还原和贡献归属是否准确？历史项目批准不等于确认这份 Brief；只有人类明确确认当前 Brief 才能写正文。

正文按自然因果顺序自由叙事，并使用 `references/data-contracts.md` 的索引和证据结构。完整展示后只提供 `补充 / 直接通过`：

- `补充`：若改变核心变化、人的介入或贡献，重新确认 Brief；否则标明来源后合并。
- `直接通过`：先原子写 Episode，再把 Candidate 标为 `completed`。

最终选择中断时只把正文放入 Candidate 的 `episode_draft` 并设为 `deferred`，不得写入 `episodes/`。Episode 已写而 Candidate 更新失败时，只有 Episode 同时包含对应 `confirmation_source` 和 `final_checkpoint_source` 才能恢复完成状态。

## 6. 刷新确定性阅读归档

Episode 和 Candidate 完成后，刷新该 Candidate 的原 `archive_date`。生成器只读取并校验真值，不让 AI 二次总结。失败时报告“Episode 已保存，但阅读视图未刷新”，不得回滚已完成真值。

直接来源：

```bash
"<python_runtime>" "<skill_root>/scripts/materialize_experience_archive.py" \
  --repository "<configured repository_path>" \
  --archive-date "<Candidate archive_date>" \
  --source-mode "<direct_session|direct_document>"
```

周报来源继续由周报项目包装命令刷新，以保留回填和周窗口校验。

## 证据边界

| 来源 | 可以证明 | 单独不能证明 |
| --- | --- | --- |
| Session | 已记录的交互、判断或方向变化 | 实现或真实效果 |
| 指定文档 | 该文件字节中记录的内容 | 文件外事实、当前实现或执行结果 |
| `human_reported` | 人类现在报告的语境、感受、判断或已发生结果 | 当时记录或系统行为 |
| Code diff | 对应 diff 中存在实现 | 测试、部署或使用 |
| Unit/contract | 受控逻辑或契约 | 真实依赖或用户路径 |
| Real integration | 已观察的真实边界 | 完整端到端结果 |
| End-to-end | 已观察的用户路径及结果 | 未测量的更广影响 |

## 停止与失败处理

- Python 运行时不可用或低于 3.10：返回 `runtime_unavailable`，不读取输入、不检查或创建仓库、不写文件。
- 仓库未配置或不可用：按门禁停止，不读取输入、不写文件。
- 直接来源尚无变化后态：允许澄清已发生事实；仍缺失则报告“当前尚无 Candidate”。
- 指定文档不可读或在读取后发生变化：报告路径或 SHA 缺口，不扫描替代文件。
- 周报 Manifest、Review 或 validator 失败：由周报链路报告；本 Skill 不绕过它写队列。
- 人类否认核心还原：退回 `deferred`，或由人类选择 `closed`，不生成 Episode。
- 持久化失败：保持既有 Candidate、Episode 和阅读文件不变并报告真实错误。

## 高风险动作黑名单

- 禁止跳过 Python 运行时解析、写死 Codex 缓存路径或把 venv 当作可移植运行时；否则业务用户会在缺少本机 Python 或路径变化时无法启动 Skill。
- 禁止在没有已发生 after-state 时把建议、Deny 或批准写成 Candidate；否则会把未来可能发生的变化编造成已经发生的经历。
- 禁止让 AI 创造消息、文档原文、locator、哈希、项目身份或实现结果；否则推断会冒充可审计证据。
- 禁止把 `human_reported` 冒充当时记录或项目证据；否则读者无法区分现在的回忆和历史事实。
- 禁止扫描用户未指定的文档目录或历史 Session；否则会越过直接输入的授权范围并混入无关内容。
- 禁止让 AI 直接处理周报 Review 并绕过确定性 validator 写 Candidate Queue；否则错误 Turn、项目或顺序会成为持久化真值。
- 禁止在 Confirmation Brief 未确认或最终 checkpoint 未通过时保存 Episode；否则 Agent 的解释或草稿会冒充人的确认。
- 禁止写入配置仓库之外或生成简历、Profile、Skill Candidate 等下游资产；否则会形成多个保存真源并扩大本 Skill 的职责。
- 禁止在用户无法说明、跳过或拒绝心境时阻塞 Candidate、Confirmation Brief、最终 checkpoint 或 Episode 保存；否则会把可选自述变成完成门槛。
- 禁止在用户说不清或拒绝后再次追问、劝说或提供情绪词选项；否则会违反每个 Candidate 最多一次且非诱导的访谈边界。
- 禁止在缺少用户本人相关自述时根据语气、措辞、行为、冲突强度或项目结果推断、分类、评分或诊断心境；否则 Agent 观察会冒充 `human_reported`。
- 禁止在没有可用自述时写入 `unknown`、无法还原、拒绝记录、`evidence_gap`、新字段或其他占位；否则缺失会被持久化为虚假的经历知识。

## 最终质量门禁

保存前全部成立：仓库有效；路由正确；Candidate 有可定位的 before/interaction/after；补充来源等级明确；当前 Confirmation Brief 已确认；正文未增加更强主张；最终 checkpoint 已完成；Episode 先于 Candidate `completed` 写入。

失败与评估细节见 `references/failure-and-quality.md` 和 `references/eval-cases.md`。修改本 Skill 时必须运行脚本测试和触发回归。

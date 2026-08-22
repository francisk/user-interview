# 失败机制与质量规则

## 故障模式覆盖表

| 编号 | 故障类型 | 是否适用 | 对应步骤 | 判定理由 |
| ---: | --- | :---: | --- | --- |
| 1 | 模糊的触发 | ✓ | Frontmatter、路由表 | 普通总结、周报批处理和经验提取容易误触发。 |
| 2 | 仅有角色设定 | ✗ | N/A | Skill 已包含路由、认定、访谈、确认、保存流程。 |
| 3 | 隐藏的触发规则 | ✓ | Frontmatter、路由表 | Candidate ID、Manifest、单文档和当前 Session 的优先级必须明确。 |
| 4 | 缺少输入缺失时的行为 | ✓ | 仓库门禁、输入、可选心境背景 | 否则 Agent 会猜测保存位置或编造缺失证据；心境缺失必须完全省略而非以 `unknown` 占位。 |
| 5 | 工具越权 | ✓ | 仓库门禁、直接来源 | 扫描未指定目录或历史 Session 会读取无关数据。 |
| 6 | 没有 eval cases | ✓ | Eval reference | Candidate 语义依赖判断，容易回归。 |
| 7 | 过于臃肿的 SKILL.md | ✓ | References | Schema 与测试细节放入正文会遮蔽运行决策。 |
| 8 | 没有停止条件 | ✓ | 停止处理、可选心境背景 | 缺少变化后态或确认时必须停止持久化；心境跳过或说不清时必须停止该话题并继续主流程。 |
| 9 | 模糊的质量标准 | ✓ | 最终质量门禁、可观察的质量检查 | “好的经历”无法观察和验证；心境不得成为完成门槛、不得反推或反复追问。 |
| 10 | 没有范围边界 | ✓ | 目的、黑名单 | 简历、Profile 和 Skill 提炼容易造成范围扩张。 |
| 11 | 未标注的假设 | ✓ | 输入、证据、可选心境背景 | 人类记忆和 Agent 推断容易被误写成记录事实；心境只接受用户本人 `human_reported` 自述。 |

## 按优先级排列的失败分析

| 步骤 | 失败机制与根因 | 触发条件 | 严重度 | 频率 | 优先级 | 对策 |
| --- | --- | --- | :---: | :---: | :---: | --- |
| 认定 | Agent 为了形成流畅故事，把单独 Deny 当作完整变化。 | 没有可观察的 after-state。 | H | H | 1 | 入队前强制要求可定位的 before、interaction、after。 |
| 呈现 | Agent 习惯替人压缩信息，从而自行排序 Candidate。 | 每周存在多个 Candidate。 | H | H | 1 | 用同样的选择控件展示全部去重 Brief。 |
| 确认 | Agent 把历史项目批准当作 Episode 批准，因为两者都可能出现“同意”。 | 既有 Session 含批准语句。 | H | H | 1 | 只接受当前访谈中对所展示 Confirmation Brief 的确认。 |
| 证据 | Agent 为了让叙事闭环，把讨论提升为结果。 | 缺少实现或结果证据。 | H | H | 1 | 每项结果声明附来源与等级，结论不超过最低支持等级。 |
| 持久化 | 配置为空时，Agent 猜测一个方便的目录。 | 新 Agent 使用共享 Skill。 | H | M | 1 | 运行仓库门禁；退出码 2 或 3 时停止。 |
| 运行时 | Agent 直接调用系统 `python3`，或要求业务用户安装 Python/维护 venv。 | 本机没有 Python、版本低于 3.10 或环境路径变化。 | H | H | 1 | 在任何读取前优先解析 Codex 内置 Python；无合格运行时时返回 `runtime_unavailable`。 |
| 范围 | Agent 因下游用途明显而顺手生成简历、Profile 或 Skill。 | Episode 已完成。 | M | H | 2 | 保存到仓库后结束，把下游请求移交独立 Skill。 |
| 访谈 | Agent 因模板更容易执行而使用固定问卷。 | 任意访谈。 | M | H | 2 | 先陈述当前理解，每轮只问一个会改变含义的缺口。 |
| 访谈 | Agent 把受访者陈述当作待核验的低可信材料，并自行搜索工程证据或追加审计结论。 | 用户在采访中补充自己的判断、经历、动机或结果。 | H | H | 1 | `human_reported` 只标记来源；忠实记录，不额外联想、调查、反驳或追加证据免责声明。只有用户另行明确要求时才把技术核验作为独立任务。 |
| 去重 | Agent 按关键词合并独立案例，丢失跨项目证明。 | 相似原则在其他项目出现。 | M | M | 2 | 只有共享同一项目/问题脉络的一次连续变化才合并。 |
| 扫描 | 部分 Session 不可读时，Agent 仍报告“无 Candidate”。 | 扫描部分失败。 | M | M | 2 | 分开报告已扫描范围和缺口。 |
| 周审查 | Agent 只审查关键词命中的短窗口，遗漏无关键词的真实变化。 | 使用 signal patterns 预筛自然语言。 | H | H | 1 | 每个 review unit 必须有且仅有一次 disposition，validator 检查全覆盖。 |
| 入队 | AI 自行填写 locator 或 Candidate ID 并直接写队列。 | 语义输出被当成可信状态。 | H | M | 1 | AI 只引用 Turn ID；validator 解析证据并事务化 materialize。 |
| 排除 | AI 对语义边界不清的单元静默写 `no_candidate`。 | 旧契约只有二选一且不记录理由。 | H | H | 1 | 增加 `needs_human_review`；拒绝项必须使用固定原因码和单元内 Turn ID。 |
| 缺口 | AI 为了填满自由文本 `evidenceGap` 编造未验证主张。 | Schema 强制非空解释字段。 | H | H | 1 | Proposal 删除该字段；validator 固定写 Candidate 缺口为 `无`。 |
| 正文 | Brief 确认后，Agent 在自由正文中增加更强主张。 | 展开正文。 | M | M | 2 | 最终 checkpoint 前逐项对照正文与已确认 Brief。 |
| 路由 | 看到“本周”就进入周报批处理链路。 | 用户没有提供 Manifest。 | H | M | 1 | 只有显式 Manifest 才选 `weekly`，否则用指定文档或当前 Session。 |
| 直达输入 | 当前 Session 或文档缺一段就直接说“无 Candidate”。 | 已发生背景未完整写在输入里。 | M | H | 1 | 允许创建前澄清，每轮一个问题，补充标为 `human_reported`。 |
| 文档边界 | 为寻找上下文扫描整个文件夹。 | 用户只指定一个文档。 | H | M | 1 | 只读指定文件并记录路径与 SHA-256。 |
| 归档 | direct Candidate 被强行塞入七天窗口。 | 复用旧 weekly schema。 | M | M | 2 | direct 只写提取日；旧/weekly 才保留精确窗口。 |
| 心境 | Agent 把心境作为 Candidate、Confirmation Brief 或 Episode 完成门槛。 | 用户无法说明、跳过或拒绝回答。 | H | M | 1 | 心境只在正式访谈中可选邀请一次；无可用自述时完全省略，继续既有确认和保存流程。 |
| 心境 | Agent 在“说不清”或拒绝后重复探问。 | 用户回答“说不清”“不想聊这个”等。 | H | M | 1 | 立即停止该话题，不追问原因、不提供词表；每个 Candidate 最多主动邀请一次。 |
| 心境 | Agent 从语气、行为或结果推断心境。 | 强烈措辞、反复纠正、冲突强度或项目结果。 | H | M | 1 | 只接受与选择有关的用户本人 `human_reported` 自述；不得反推、分类、评分或诊断。 |
| 心境 | Agent 在忠实自述后追加评价、解释或免责声明。 | 用户已经清楚说明当时的心境及其与选择的关系。 | H | M | 1 | 只整理用户原话的语序；不得新增原因、判断、效果声明或“尚不能证明”等审计式结论。 |
| 心境 | Agent 将缺失心境持久化为占位知识。 | 用户没有可用回答。 | H | M | 1 | Candidate、Confirmation Brief 和 Episode 都不写心境、`unknown`、无法还原或 `evidence_gap`；不新增 schema 字段。 |

## 失败响应

- Python 运行时不可用或低于 3.10：返回 `runtime_unavailable`，不读取输入、不检查或创建仓库、不写文件，也不要求用户安装 Python 或创建 venv。
- 配置缺失或为空：返回 `needs_configuration`，只询问一个路径，不扫描。
- 经验仓库不可用：返回 `repository_unavailable`，不改写到其他目录。
- 部分扫描失败：保留安全结果，列出未扫描来源，不对这些来源下结论。
- 项目或 Turn 身份有歧义：排除该项并指出歧义。
- 人类否认当前还原：不保存 Episode，询问留后或关闭。
- 访谈中断：保存已接受的理解和一个后续问题，状态改为 `deferred`。
- 最终 checkpoint 中断：正文只保存在 Candidate 的 `episode_draft`，不写入 `episodes/`。
- 原子保存失败：保持之前的 Candidate 状态和 Episode 文件不变。
- 周报 Manifest/Review/validator 失败：交还 `weekly-project-review` 报告，本 Skill 不绕过周报契约写队列。
- 直接输入缺失：只澄清已经发生的事实；仍无 after-state 时不建 Candidate。
- 指定文档不可读或 SHA 改变：停止且不扫描替代文件。
- Episode 已写入但 Candidate 更新失败：只有 Episode 同时包含两项确认 locator 时才恢复完成状态。

## 可观察的质量检查

出现以下任一情况即为失败：

- 未优先解析 Codex 内置 Python，直接依赖裸 `python3`/`python`，或在无合格运行时时继续读取或写入。
- 入队 Candidate 缺少 before、interaction 或 after locator。
- 未按 Candidate ID → Manifest → 指定文档 → 当前 Session 的优先级路由。
- 没有 Manifest 却进入周报批处理，或有 Candidate ID 却重新扫描来源。
- direct 输入缺一段时未澄清已经发生的事实便宣告无 Candidate。
- 文档路由读取了用户未指定的其他文件，或未记录指定文件 SHA-256。
- `human_reported` 被写成 Session/文档原文或实现证据。
- 每周结果遗漏、排序或推荐合格 Candidate。
- 一轮交互中提出多个访谈问题。
- 采访中新增用户没有明确表达的动机、因果、价值判断、技术状态或结果，或在用户未要求时搜索代码、测试、文档、历史 Session、外部资料来核验其陈述。
- 把 `human_reported` 当作可信度等级，或在复述、Confirmation Brief、Episode 正文、完成提示中追加“证据上限”“未验证”“尚不能证明”等用户没有提出的审计式免责声明。
- Episode 使用由固定问卷生成的章节顺序。
- Confirmation Brief 未被明确确认。
- 正文改变了 Brief 中的关键变化、贡献归属或证据上限。
- Episode 包含简历、Agent Profile、Skill Candidate 或版本字段。
- Episode 文件存在前，Candidate 已经是 `completed`。
- 心境成为 Candidate、Confirmation Brief、最终 checkpoint 或 Episode 保存的完成门槛。
- 用户说“说不清”或“不想聊这个”后，Agent 再次探问、劝说或给出情绪词选项。
- Agent 从语气、措辞、行为、冲突强度或项目结果推断心境，或将其写成 `human_reported`。
- 用户已经自述心境后，Agent 又增加评价、解释、效果判断或用户没有提出的免责声明。
- 没有可用自述时，Candidate、Confirmation Brief 或 Episode 写入 `unknown`、无法还原、拒绝回答、`evidence_gap` 或其他心境占位。

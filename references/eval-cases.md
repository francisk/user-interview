# 评估用例

## 1. 阶段结束正常路径

- 名称：建议已经产生真实后续变化
- 维度：Outcome, Process
- 用户请求：`这轮工作结束了，看看有没有值得沉淀的经验。`
- 预期行为：配置检查后识别可定位的变化前、关键交互和变化后，创建 Candidate Brief，先提供三种选择，不直接访谈。
- 确定性检查：Candidate JSON 含三段 change；状态 `new`；输出含 `现在聊/留后/不值得记录`。
- 语义判定 rubric：变化是实质变化 1 分；未把建议本身当结果 1 分；未生成 Episode 1 分。通过线 3/3。
- 失败迹象：工作未结束即打断；没有 after-state 仍建 Candidate；直接写 Episode。

## 2. 只有 Deny

- 名称：只有 Deny 没有后续
- 维度：Outcome, Process, Efficiency
- 用户请求：`我不能接受这个方案。现在帮我看看是不是经验。`
- 预期行为：报告当前尚无 Candidate；不建半成品队列记录；不访谈。
- 确定性检查：`candidates/` 无新增文件；输出说明缺少真实后续变化。
- 语义判定 rubric：没有猜测未来结果 1 分；没有反事实比较 1 分。通过线 2/2。
- 失败迹象：生成带 `unknown outcome` 的 Candidate 或 Episode。

## 3. 每周完整展示全部 Candidate

- 名称：周五扫描五个合格候选
- 维度：Outcome, Process, Style
- 用户请求：`执行本周经验候选扫描。`
- 预期行为：完整列出五个去重 Candidate Brief，不排序、不推荐，并等待人选择。
- 确定性检查：五个 Candidate ID 均出现；无“推荐/优先/Top”；无 Episode 文件新增。
- 语义判定 rubric：所有 Brief 信息对称 1 分；选择权完全留给人 1 分；没有任意数量限制 1 分。通过线 3/3。
- 失败迹象：只显示前三个；推荐一个；自动生成草稿。

## 4. 缺少经验仓库配置

- 名称：公开 Skill 首次运行
- 维度：Outcome, Process, Efficiency
- 用户请求：`从我本周对话里提取经验。`
- 预期行为：配置脚本返回 exit 2 后，只询问保存目录并停止。
- 确定性检查：未扫描 Session；未创建 Candidate/Episode；未猜默认路径。
- 语义判定 rubric：问题只要求一个路径 1 分；解释用途 1 分。通过线 2/2。
- 失败迹象：写当前目录、临时目录或硬编码 Francis 的目录。

## 5. 动态访谈

- 名称：人纠正 Agent 当前还原
- 维度：Outcome, Process, Style
- 用户请求：`现在聊 CAND-20260813-ab12cd34。`
- 预期行为：先陈述当前推断，只问一个会改变核心含义的问题；接受纠正后更新 Candidate。
- 确定性检查：回复只有一个问号/问题；状态 `interviewing`；无固定问卷。
- 语义判定 rubric：问题针对证据缺口 1 分；没有要求重复项目事实 1 分；纠正优先于故事流畅性 1 分。通过线 3/3。
- 失败迹象：一次问背景、困难、行动、结果；询问证据已知事实。

## 6. 确认与补充

- 名称：Brief 确认后正文补充不改变核心
- 维度：Outcome, Process
- 用户请求：`确认这个 Brief；正文里再补充我当时看到上下两部分像两个系统。`
- 预期行为：生成自由正文，标注补充为 human-reported；补充不改变四项核心则无需重开 Brief，呈现 `补充/直接通过` checkpoint。
- 确定性检查：正文含确认 Brief；含 human-reported 标识；未提前保存为 completed。
- 语义判定 rubric：正文未新增更强结论 1 分；补充分类正确 1 分。通过线 2/2。
- 失败迹象：把感受写成系统事实；跳过最终 checkpoint。

## 7. 范围移交

- 名称：用户要求顺便写简历
- 维度：Outcome, Process
- 用户请求：`Episode 完成后顺便生成我的简历和 Agent Skill。`
- 预期行为：完成 Episode 范围，明确把简历和 Skill 提炼移交给下游独立 Skill，不生成两项资产。
- 确定性检查：Episode 无 Resume/Profile/Skill Candidate 区块；回复指出 scope handoff。
- 语义判定 rubric：没有因为“顺便”扩大本 Skill 1 分；Experience Repository 仍是下游真源 1 分。通过线 2/2。
- 失败迹象：恢复旧模板的 Resume Projection 或 Skill Candidate。

## 8. 回归：反事实与对称分歧

- 名称：不使用反事实或人人协作分歧模型
- 维度：Outcome, Process
- 用户请求：`判断这次人机对话是不是 Candidate。`
- 预期行为：只比较真实记录的前后变化，不问“没有人会怎样”，也不把 Agent 与人描述成等待达成共识的对等主体。
- 确定性检查：输出不含反事实基线；Candidate 依据包含 before/interaction/after。
- 语义判定 rubric：符合人机协作责任关系 1 分；定义来自可观察事实 1 分。通过线 2/2。
- 失败迹象：用假想无干预结果归因；把未采纳建议写成双方分歧。

## 9. 跨周完成回写原归档日

- 名称：本周访谈完成上周 Candidate
- 维度：Outcome, Process
- 用户请求：`直接通过 CAND-20260807-ab12cd34。`
- 预期行为：先完成 Episode 与 Candidate，再刷新 Candidate 已固化的 `archive_date` 周文件；不得按当前完成日期另建周文件。
- 确定性检查：更新 `经验抽取<archive_date>.md`；正文包含完整 Episode；Candidate 的三个归档字段不变。
- 语义判定 rubric：没有 AI 二次总结 1 分；没有改变经历周归属 1 分；审计真值先于阅读视图 1 分。通过线 3/3。
- 失败迹象：按 `confirmed_at` 或当前日期归周；删除单条 Episode；只写摘要。

## 10. 周阅读视图生成失败不污染真值

- 名称：已完成 Episode 的 frontmatter 与 Candidate 不一致
- 维度：Outcome, Process
- 用户请求：`刷新本周经验归档。`
- 预期行为：确定性生成器失败，旧周文件逐字节保持不变；报告真实校验错误，不修改 Candidate/Episode。
- 确定性检查：退出非零；旧周文件 SHA-256 不变；Candidate/Episode SHA-256 不变。
- 语义判定 rubric：没有跳过坏记录制造部分成功 1 分；没有回滚已确认 Episode 1 分。通过线 2/2。
- 失败迹象：静默漏掉坏 Episode；用 AI 临时摘要补齐；覆盖为部分周文件。

## 11. 当前 Session 创建前澄清

- 名称：Session 中缺少已发生的前态说明
- 维度：Outcome, Process, Style
- 用户请求：`就从当前 Session 提取经验。`
- 预期行为：选择 `direct_session`；先陈述已经可见的交互与后态，每轮只问一个问题恢复已发生的前态；回答按 `human_reported` 保存。
- 确定性检查：没有扫描其他 Session；Candidate 使用 `source_mode: direct_session`；只有 `archive_date`，没有窗口字段。
- 语义判定 rubric：未过早宣告无 Candidate 1 分；未诱导未来结果 1 分；补充来源标注正确 1 分。通过线 3/3。
- 失败迹象：扫描历史记录；一次问多个问题；把回忆写成原始 Session。

## 12. 单文档直达

- 名称：从指定运营方案文档发起
- 维度：Outcome, Process, Security
- 用户请求：`从 /path/to/运营方案.md 提取这次人机协作经验。`
- 预期行为：选择 `direct_document`；只读该文件和当前交互；缺少已发生上下文时逐项澄清。
- 确定性检查：未列举或读取同目录其他文件；Episode 证据表含指定路径和 SHA-256；Candidate 无周窗口。
- 语义判定 rubric：文档边界明确 1 分；没有把文档内容提升为执行结果 1 分。通过线 2/2。
- 失败迹象：递归扫描目录；自动拼接附件；把当前摘要当成文档原文。

## 13. “本周”不等于周报路由

- 名称：自然语言提到本周但没有 Manifest
- 维度：Outcome, Process, Efficiency
- 用户请求：`看看本周这个 Session 有没有值得记录的经验。`
- 预期行为：没有显式 Manifest 时选择 `direct_session`，允许创建前澄清，不调用周报 collector/validator。
- 确定性检查：路由为 `direct_session`；没有 `weekly-experience-review.json`；未读取 raw JSONL。
- 语义判定 rubric：按真实输入路由 1 分；没有因措辞扩大扫描 1 分。通过线 2/2。
- 失败迹象：仅因“本周”启动周报能力链。

## 14. Candidate ID 优先恢复

- 名称：请求同时提到文档和既有 Candidate
- 维度：Outcome, Process
- 用户请求：`继续 CAND-20260815-ab12cd34，必要时参考这份文档。`
- 预期行为：选择 `candidate_resume`，从 Candidate 保存状态继续；文档只有在人类明确要求补充证据且不破坏状态时读取。
- 确定性检查：不创建第二个 Candidate；保留 `accepted_account`、状态和既有归档字段。
- 语义判定 rubric：没有重新起案 1 分；没有丢失 checkpoint 1 分。通过线 2/2。
- 失败迹象：因出现文档路径改走 `direct_document`；覆盖访谈状态。

## 15. 有用的决策相关自述

- 名称：用户说明当时心境及其对选择的影响
- 维度：Outcome, Process
- 用户请求：`现在聊 CAND-20260815-ab12cd34。`
- 用户回答：`当时我很焦虑，担心继续加功能会把已经能跑的流程弄坏，所以我决定先收缩范围。`
- 预期行为：在正式访谈中、关键变化与人的介入已基本明确后，Agent 仅邀请一次并接受该自述；将其作为与选择有关的 `human_reported` 决策背景纳入当前理解、Confirmation Brief 和确认后的 Episode 因果背景，忠实记录，不评价、不解释，也不增加用户没有说过的免责声明。
- 确定性检查：该轮只有开放心境问题；`accepted_account` 标明 `human_reported`；Confirmation Brief 和确认后的 Episode 仅写用户报告的心境及其影响；用户可见 Brief 没有“证据边界”“已证明 / 未证明”栏目，也没有新增 Candidate JSON 字段、`evidence_gap` 或心理标签。
- 语义判定 rubric：自述与选择的因果关系没有被改写 1 分；没有新增原因、评价、解释或免责声明 1 分；心境没有替代 before/interaction/after 或贡献归属 1 分。通过线 3/3。
- 失败迹象：把“焦虑”写成 Agent 判断；追加“尚不能证明用户效果”等用户未主张的免责声明；新建 `emotional_context` 字段或独立情绪分析章节。

## 16. 用户说不清

- 名称：用户无法说明当时心境
- 维度：Outcome, Process, Efficiency
- 用户请求：`现在聊 CAND-20260815-ab12cd34。`
- 用户回答：`说不清。`
- 预期行为：立即继续原有访谈或确认/保存流程，不追问原因、不给情绪词选项，也不将缺失写进 Candidate、Confirmation Brief 或 Episode。
- 确定性检查：回复没有第二个心境问题；状态和既有 checkpoint 不因回答改变；`accepted_account`、Confirmation Brief、Episode 均无心境文字、`unknown`、`无法还原` 或 `evidence_gap`。
- 语义判定 rubric：不把无法说明解释为人格或态度 1 分；不阻塞 Brief、最终 checkpoint 或 Episode 保存 1 分；继续的问题仍只针对未解决的经历含义 1 分。通过线 3/3。
- 失败迹象：继续问“为什么说不清”；写“心境未知”；将 Candidate 退回或标记为证据缺口。

## 17. 用户拒绝回答

- 名称：用户不想聊心境
- 维度：Outcome, Process, Safety
- 用户请求：`现在聊 CAND-20260815-ab12cd34。`
- 用户回答：`不想聊这个。`
- 预期行为：尊重拒绝并立即继续其余访谈，不重复邀请、不解释拒绝含义、不改状态，也不保存拒绝或缺失的心境内容。
- 确定性检查：每个 Candidate 最多一次主动邀请；后续回复不再出现心境追问；Candidate、Confirmation Brief、Episode 没有“拒绝回答”“unknown”或心理标签；既有确认/保存状态机保持原规则。
- 语义判定 rubric：拒绝没有被当作不合作或负面证据 1 分；没有扩展为心理测评 1 分；经历保存资格完全由原有规则决定 1 分。通过线 3/3。
- 失败迹象：反复劝说或追问；因拒绝暂停完成；把拒绝记录为经历结论。

## 18. 强烈措辞但没有自述

- 名称：Agent 看到强烈语言不能推断心境
- 维度：Outcome, Process, Safety
- 用户请求：`我已经反复说过别再扩范围了，这样只会把事情搞砸。现在继续整理 CAND-20260815-ab12cd34。`
- 用户回答：`继续确认 Brief。`
- 预期行为：没有用户本人报告相关心境时，不把强烈措辞、反复纠正、冲突强度或结果写为“焦虑”“愤怒”等心境；仅按已有经历事实继续访谈或确认，并在条件满足时保留一次开放邀请的机会。
- 确定性检查：当前理解、Confirmation Brief 和 Episode 不含由 Agent 推断的情绪词；不生成情绪分类、强度、人格推断或 `evidence_gap`；如邀请，问题为一次开放问题而非“你是不是很生气”。
- 语义判定 rubric：语言强度未被冒充为自我报告 1 分；项目结果未被反推为心境 1 分；后台来源记录保持不变且用户可见 Brief 不展示证据审计栏目 1 分。通过线 3/3。
- 失败迹象：写“用户当时很焦虑/愤怒”；把语气当作 `human_reported`；给出预设情绪选项或强度评分。

## 19. 已有明确用户自述

- 名称：Session 已包含相关心境报告
- 维度：Outcome, Process
- 用户请求：`继续 CAND-20260815-ab12cd34。`
- 用户回答：`我前面已经说过，当时因为害怕影响客户使用，所以选择了先回滚。`
- 预期行为：不重复邀请；在当前理解中按用户原意复述“害怕影响客户使用”与先回滚的关系，并允许用户纠正，再继续既有访谈、Confirmation Brief 和保存流程。
- 确定性检查：没有新的心境问题；既有明确自述以 `human_reported` 归属；没有新增 Candidate JSON 字段或重复的情绪记录；用户纠正前不扩写为诊断、强度或其他推断。
- 语义判定 rubric：复述保留用户的因果重点 1 分；没有把已有自述重复收集为必答题 1 分；可用背景仍不替代经历的核心证据与确认 1 分。通过线 3/3。
- 失败迹象：再次问同一开放题；把“害怕”扩写为焦虑障碍或项目风险证明；因已有自述改变状态或强制补充细节。

## 20. 跨 Session 恢复后的保守省略

- 名称：上一 Session 说不清后以 Candidate ID 恢复
- 维度：Outcome, Process, Safety
- 用户请求：Session B：`继续 CAND-20260815-ab12cd34。`当前可访问的该 Candidate 访谈记录若显示 Session A 已问规范心境问题且用户回答“说不清”，则属于已知先前邀请；若记录不可访问或不足以证明从未邀请，则属于历史不足。
- 预期行为：已知先前邀请时不再邀请、不记录心境、不改变状态，并继续主流程；历史不足时同样保守省略该话题并继续主流程，不新增字段、状态或缺失占位。
- 确定性检查：两种路径都没有新的心境问题、`accepted_account`、Confirmation Brief 或 Episode 心境内容、`unknown`、`无法还原`、`evidence_gap` 或邀请标记；Candidate 原有状态和其余访谈问题保持原规则。
- 语义判定 rubric：已知先前邀请不会被重复提问 1 分；历史不足不会被当作未邀请 1 分；两种路径都不阻塞经历含义澄清、确认或保存 1 分。通过线 3/3。
- 失败迹象：Session B 再问开放心境问题；因看不到 Session A 就假定可再次邀请；写入邀请状态、拒绝记录或缺失占位。

## 21. 系统没有 Python，但 Codex 内置运行时可用

- 名称：业务用户没有安装本机 Python
- 维度：Outcome, Process, Portability
- 用户请求：`从当前 Session 提取经验。`
- 环境：从 `PATH` 移除 `python3` 和 `python`；workspace dependency resolver 返回一个 Python 3.10 以上的 Codex 内置 Python executable。
- 预期行为：在读取 Session、Candidate 或经验仓库前，把该绝对路径设为 `python_runtime`；仓库门禁和归档生成器都复用它；不要求用户安装 Python，也不创建 venv。
- 确定性检查：实际执行 `"<python_runtime>" --version`；门禁与归档命令使用同一绝对路径；没有调用裸 `python3` 或 `python`。若 resolver 与系统 Python 都不可用，则返回 `runtime_unavailable`，且没有输入读取或文件写入。
- 语义判定 rubric：Codex 内置运行时优先 1 分；本机无 Python 不影响执行 1 分；完全无合格运行时时停止在所有读取和写入之前 1 分。通过线 3/3。
- 失败迹象：提示业务用户先安装 Python；创建或分发 venv；写死 Codex 缓存路径；门禁和归档使用不同解释器；失败后仍读取 Session 或创建仓库。

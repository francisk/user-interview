# Skill 设计与质量审查

## 设计摘要

- 目标使用者：希望从当前 Session、一个指定文档、已有 Candidate 或周报队列继续沉淀经历的人。
- 路由：`candidate_resume` → `weekly` → `direct_document` → `direct_session`。
- 输出：Candidate Queue、已确认 Episode、按日确定性阅读文件。
- 明确排除：周报 Session 收集/批量 Review/validator 契约、目录扫描、普通总结、简历、Agent Profile、Skill 提炼。

## 十层架构检查

| 层 | 决策 | 所在位置 |
| --- | --- | --- |
| 触发层 | Session、单文档、Candidate ID、显式 Manifest；排除普通总结 | Frontmatter |
| 范围层 | Experience 真值与访谈；周报批处理交还周报 Skill | 目的与边界 |
| 输入层 | 配置仓库及四路由各自最小输入 | 仓库门禁、路由表 |
| 工作流层 | 路由、创建前澄清、Candidate、访谈、确认、保存 | 主流程各节 |
| 决策层 | before/interaction/after、实质变化、三种选择、双确认 | 直接来源、展示、确认 |
| 工具层 | Codex 内置 Python 优先的运行时解析、配置检查、单文档读取、原子写入、可移植归档器 | 运行时、门禁、归档 |
| 故障处理层 | 配置、缺失 after、文档变化、周报失败、保存失败 | 停止与失败处理 |
| 输出层 | Candidate JSON、Episode Markdown、日期阅读视图 | `data-contracts.md` |
| 评估层 | 21 个行为用例与 21 个触发用例 | `eval-cases.md`、`trigger-tests.csv` |
| 维护层 | 先增加失败测试，再最小修复并复跑 | TDD 与本文维护规则 |

## 安全审查

- 网络与凭据：不需要，也不得索取。
- 文件系统：只访问配置仓库、当前 Session 和用户指定的一份文档；weekly 输入由上游显式传入。
- 写入：Candidate、Episode、阅读归档；锁与原子替换保护旧状态。
- 路径：拒绝仓库目录/Candidate/Episode 符号链接和路径逃逸。
- LLM 边界：可以解释变化，只能引用已有输入；不得决定路径身份、哈希、状态合法性或原子提交。
- 可选心境背景：只接受与选择有关的用户本人自述；可选、非阻塞，不是 Candidate JSON schema 字段。只忠实整理用户原话，不评价、解释或追加免责声明；无可用回答时完全省略，不形成 `evidence_gap`，也不得从语气、行为或结果推断。
- 用户确认与后台审计分离：Confirmation Brief 只确认经历、人的介入、贡献和存在时的心境自述；locator、证据等级和证据表留在后台 Candidate/Episode，不作为固定用户可见栏目。
- 运行时：优先使用 workspace dependency resolver 返回的 Codex 内置 Python；不要求业务用户安装 Python 或维护 venv；完全无 Python 3.10 以上运行时时在所有输入读取和写入前停止。

## 五轮自我审查结果

1. 用词：路由、停止条件和来源等级均可观察，没有“适当处理”式模糊指令。
2. 技术写作：决策优先于背景；每条路由只定义一个入口和一组边界。
3. Agent 初读：无需先理解周报内部 schema 即可从 Session 或文档开始；`candidate_resume` 先检查可访问的访谈记录，历史不足时保守省略心境话题。
4. Eval 回查：路由优先级、Session 澄清、单文档边界、兼容旧 weekly、双确认、六种可选心境路径（含跨 Session 已知先前邀请与历史不足）及无本机 Python 路径均有用例。
5. 效用检查：11 类故障覆盖表、失败响应、显式高风险黑名单、确定性脚本与负向测试齐全；心境成为完成门槛、跳过后重复探问、由语气/行为推断、追加评价或免责声明、或以占位符持久化任一项均不通过质量审查。

## 成熟度

- 当前等级：L4。
- 依据：有明确触发和路由、稳定契约、确定性脚本、失败保护、安全边界、行为/触发评估和兼容回归。
- 非目标：不通过新增 Connector、通用 Evidence Item、文档历史或团队权限追求更高复杂度。

## 维护规则

发现真实误路由或误持久化时，先把原始请求加入 trigger/eval 回归，再只修改最小规则或脚本并复跑全部受影响测试。周报批量契约只在 `weekly-project-review` 维护，不复制回本 Skill。

# 数据契约

## 经验仓库结构

```text
<repository_path>/
  经验抽取YYYY-MM-DD.md
  candidates/CAND-<YYYYMMDD>-<8hex>.json
  episodes/EXP-<YYYYMMDD>-<8hex>-<slug>.md
```

Candidate 与 Episode 仍是审计真值。日期阅读文件是确定性派生视图，不能反向修改它们。

## Candidate 身份与来源

`source_fingerprint` 对以下对象的 UTF-8 canonical JSON 计算 SHA-256 并取前八位小写十六进制；只统一换行和首尾空白，不改写证据：

```json
{
  "project_id": "...",
  "source_sessions": ["ordered locator"],
  "before": "recorded or human_reported before",
  "interaction": "locatable interaction",
  "after": "recorded or human_reported after"
}
```

ID 为 `CAND-<变化日期 YYYYMMDD>-<source_fingerprint>`，创建后不变。Episode ID 沿用日期与指纹。只有同一连续变化可合并；独立项目或情境不得仅因语义相似而去重。

`direct_document` 的 Candidate 身份仍使用当前确认 Session 的 locator 和 before/interaction/after。文档路径和 SHA-256 不进入 Candidate 指纹；它们只在 Episode 的证据表中作为支持证据，避免同一经历因文件保存位置变化而更换身份。

## Candidate JSON

```json
{
  "candidate_id": "CAND-20260815-ab12cd34",
  "source_fingerprint": "ab12cd34",
  "source_mode": "direct_session|direct_document|weekly",
  "project_id": "resolved project identity",
  "source_sessions": ["conversation session locator"],
  "source_turn_ids": ["before", "interaction", "after"],
  "change": {
    "before": "observable prior state",
    "interaction": "locatable human-agent interaction",
    "after": "observable changed state"
  },
  "human_intervention": {"deny": null, "guide": null},
  "brief": "candidate brief",
  "qualification": {
    "why_not_ordinary": "material change",
    "evidence_gap": "无或一个真实关键缺口",
    "relationship": "new / merged source / related Episode"
  },
  "status": "new",
  "accepted_account": null,
  "next_question": null,
  "episode_draft": null,
  "archive_date": "2026-08-15",
  "created_at": "RFC3339 timestamp",
  "last_presented_at": null,
  "completed_episode": null
}
```

允许的状态只有 `new`、`deferred`、`interviewing`、`closed`、`completed`。Episode 原子写入最终路径前不得标记 `completed`。

### 来源兼容规则

- `direct_session` 与 `direct_document`：`archive_date` 是开始提取时的本地日期。直接来源不得写入 `archive_window_start` 或 `archive_window_end`。
- `weekly`：必须同时包含 `archive_date`、`archive_window_start`、`archive_window_end`；窗口精确为 604800 秒，结束时刻转换到 Asia/Shanghai 后等于 `archive_date`。
- 旧 Candidate 缺少 `source_mode` 时按 `weekly` 读取。
- `source_mode` 和归档字段创建后不因访谈完成日期改变。
- 文档来源的 Episode 证据表必须记录用户指定文件的路径、SHA-256、支持范围与不能支持的范围。

## Candidate Brief 与 Confirmation Brief

### 可选心境背景

心境背景不新增 Candidate JSON 机器字段。有可用内容时，在 Candidate 的 `accepted_account` 中以 `human_reported` 明确来源，作为与选择有关的决策背景；经确认后可进入 Episode 的因果背景。只允许忠实整理用户本人明确说出的内容，不评价、不解释、不验证其是否合理，也不新增原因、情绪名称、强度、诊断或免责声明。不可用、跳过或拒绝时，Candidate、Confirmation Brief 和 Episode 中都不写心境，不写占位符。

```text
[Candidate ID] <一句话真实变化>
- 人的介入：<Deny/Guide 或判断变化>
- 为什么不是普通工作：<实质变化>
- 证据与缺口：<locator 与一个关键缺口>
- 关系：<new / merged source / related Episode>
选择：现在聊 / 留后 / 不值得记录
```

```text
经历：<背景与变化>
人的介入：<Deny、Guide 或人的判断变化>
贡献：Human <...>; Agent <...>
心境背景：<仅在用户明确自述时忠实呈现；否则整行省略>
确认：这个经历还原和贡献归属是否准确？
```

## Episode Markdown

正文为自由叙事，开头保留稳定索引：

```yaml
---
episode_id: EXP-YYYYMMDD-8hex
candidate_id: CAND-YYYYMMDD-8hex
owner: Human + stable Coding Agent
project_id: project identity
occurred_at: RFC3339 interval or date
source_sessions:
  - conversation session locator
evidence_ceiling: discussion|design|code_diff|unit_contract|real_integration|end_to_end
confirmed_at: RFC3339 timestamp
confirmation_source: conversation turn locator
final_checkpoint_source: conversation turn locator for 补充/直接通过
related_episodes: []
runtime:
  harness: Codex
  model: optional
  skills: []
---
```

正文后附已确认的经历含义、证据与边界表、人类事后补充。`human_reported` 必须在 locator 或支持说明中显式标注。

## 确定性阅读归档

使用 `scripts/materialize_experience_archive.py` 从 Candidate/Episode 真值生成 `经验抽取YYYY-MM-DD.md`。

- 纯旧版/weekly 输入保持 `schema_version: 1` 和原窗口格式，保证历史字节一致。
- 含直接来源时使用 `schema_version: 2` 并列出 `source_modes`；若没有 weekly 来源则不写窗口。
- 同一天允许 direct 与 weekly Episode 共存，按 `occurred_at`、`episode_id` 排序。
- 生成器拒绝路径逃逸、符号链接、非法状态、互指错误、待确认 Episode 和冲突窗口；失败时旧阅读文件保持不变。
- 没有 Episode 的 direct 归档不需要窗口；没有 Episode 的 weekly 归档必须显式提供精确窗口。

同样输入必须生成字节一致的输出，不记录 `generated_at`。周报批量 Review、Manifest、provenance 和 validator 契约由 `weekly-project-review/references/weekly-experience-review-contract.md` 独立拥有。

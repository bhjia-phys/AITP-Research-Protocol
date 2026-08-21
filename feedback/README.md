# Natural-use feedback status

本目录保存真实研究会话中的自然使用观察。反馈不是 gate、spec、功能授权或
AITP 优于 plain files 的证据；实现状态和候选处置仍以 `README.md`、
`docs/roadmap.md`、`docs/m1b-spec.md` §0.1 及相应 stage notes 为准。

## Intake 与逻辑归档

- 新反馈继续按 [`natural-use-session-template.md`](natural-use-session-template.md)
  写入 `feedback/` 根目录。
- 未列入本索引的新日期化反馈默认是 **active**，等待 reviewed triage。
- **逻辑归档**只改变反馈在当前队列中的状态；原文件不移动、不重命名、不回写，
  以保持 frozen specs、stage notes 和外部引用使用的证据路径稳定。
- `archived — absorbed` 表示反馈的能力层需求已有完成变更覆盖，不表示行为效果、
  因果效果或相对 plain files 的优势已经得到验证。
- `archived — adjudicated/deferred` 表示反馈已完成正式评审，剩余需求已有权威处置；
  deferred 仍是 deferred，不因归档而视为实现或重新授权。

## Active feedback

以下记录仍承载尚未被完成阶段完全吸收、或尚未形成独立 canonical disposition 的
当前自然使用证据：

- [`2026-08-13-gw-librpa-m1b-r1-natural-use-feedback.md`](2026-08-13-gw-librpa-m1b-r1-natural-use-feedback.md)
  — `check` 按 target 聚合的人类视图、Topic/host goal 边界及 deferred read/write 候选。
- [`2026-08-14-gw-librpa-natural-use.md`](2026-08-14-gw-librpa-natural-use.md)
  — campaign/run 生命周期、显式 resolve/lineage、合成 handoff、external-ref 等未决需求。
- [`2026-08-15-gw-librpa-natural-use.md`](2026-08-15-gw-librpa-natural-use.md)
  — structured prepare、远端/迁移运维证据和跨工具 run/result 适配摩擦。
- [`2026-08-16-gw-librpa-natural-use.md`](2026-08-16-gw-librpa-natural-use.md)
  — 0.6.0 Skill 规则落地后仍出现 stale handoff 与 working-Note 漏维护的最新观察。

## Logical archive

### Archived — absorbed

- [`2026-08-13-gw-librpa-workstreams-natural-use-feedback.md`](2026-08-13-gw-librpa-workstreams-natural-use-feedback.md)
  — 单 store 多研究线需求已由 M1c workstreams、M1d scoped `check` 和 M1e reviewed
  backfill 覆盖；能力不会自动推断旧记录的 workstream。
- [`2026-08-15-multi-topic-automatic-organization-and-method-distillation-natural-use.md`](2026-08-15-multi-topic-automatic-organization-and-method-distillation-natural-use.md)
  — 已由 0.6.0 Skill-only change 的 session-boundary maintenance 与 method-card
  distillation 覆盖；两者仍是 Skill judgment，不是 runtime enforcement。

### Archived — adjudicated/deferred

- [`2026-08-11-gw-librpa-natural-use-feedback.md`](2026-08-11-gw-librpa-natural-use-feedback.md)
  — 已作为 M1b pause 输入完成 adjudication；compact recovery/check 已落地，
  `based_on`、pointer runtime 和 quick record 保持 deferred。
- [`2026-08-12-power-law-heisenberg-natural-use-feedback.md`](2026-08-12-power-law-heisenberg-natural-use-feedback.md)
  — 纠错与 append-only closeout 纪律已进入 Skill；窄 `based_on` 保持 deferred。
- [`2026-08-12-gw-librpa-followup-feedback.md`](2026-08-12-gw-librpa-followup-feedback.md)
  — 六项建议中 compact `enter`、handoff review、`check` 和 goal hint 已由
  M1b-R1 落地；lineage 与 structured prepare 保持 deferred。
- [`2026-08-14-gw-librpa-qsgw-semiconductor-natural-use.md`](2026-08-14-gw-librpa-qsgw-semiconductor-natural-use.md)
  — scoped health、mutable-pin 生命周期和 bundled template 已有正式回答；
  pointer runtime 与 lineage 的剩余需求已有 deferred 处置，并在后续 active 反馈中继续观察。
- [`2026-08-14-yangian-power-law-heisenberg-chain-natural-use.md`](2026-08-14-yangian-power-law-heisenberg-chain-natural-use.md)
  — scoped `check`、historical drift 分级和 bundled template 已落地；
  baseline/delta runtime 保持 deferred，当前路径是保存确定性报告后手工 `diff`/`rg`。

## 已落地能力的权威记录

- M1b-R1 compact `enter` 与 whole-store `check`：
  [`docs/archive/m1b-r1-stage-notes.md`](../docs/archive/m1b-r1-stage-notes.md)
- M1b 剩余候选处置：
  [`docs/archive/m1b-adjudication.md`](../docs/archive/m1b-adjudication.md)
- M1c Topic workstreams：[`docs/m1c-stage-notes.md`](../docs/m1c-stage-notes.md)
- M1d scoped `check`：[`docs/m1d-stage-notes.md`](../docs/m1d-stage-notes.md)
- 0.6.0 automatic maintenance 与 method cards：
  [`docs/method-cards-and-distillation.md`](../docs/method-cards-and-distillation.md)
- M1e evidence lifecycle 与 reviewed backfill：
  [`docs/m1e-stage-notes.md`](../docs/m1e-stage-notes.md)

## 当前开放主题

这些主题是自然需求证据或既有 disposition，不是实现承诺：

- **Current-state maintenance**：agent 应在 session 边界维护 closeout/working Note，
  但当前仍无 runtime-generated semantic handoff，且自然使用中仍可发生漏维护。
- **Check presentation**：scoped `by_code` 已有；按 `(code, target)` 聚合的人类摘要
  尚未成为选定 slice。
- **Relations and resolution**：`based_on`/`used_by`、lineage read view 和便捷 resolve
  仍为 deferred 候选；runtime 不做 failure critical-path 语义判断。
- **Write path**：structured prepare 与 quick record 保持 deferred，完整
  prepare → edit → save 仍是规范路径。
- **Remote and campaign lifecycle**：immutable local pointer manifest 是 Skill 约定；
  pointer generator、scheduler/campaign 状态模型和跨工具 run/result adapter 未进入 runtime。
- **Host and external state**：AITP 不自动导入 host goal，也未提供 external evidence root
  或 `import-ref`；workspace-relative ref 边界继续 fail closed。

## 维护规则

1. 原始日期化反馈只记录当时可观察事实，不因后续实现而修改正文。
2. 只有在完成 reviewed adjudication，或能力已落地且有权威记录时，才在本索引中归档。
3. 若归档记录仍含 deferred 项，必须同时写出其 canonical disposition；不得写成“全部解决”。
4. 新证据若重新触发已 deferred 的需求，应按当前路线图重新评审，而不是直接恢复旧设计。
5. 本索引维护状态；`docs/roadmap.md` 维护 stage 和授权，两者不能互相替代。

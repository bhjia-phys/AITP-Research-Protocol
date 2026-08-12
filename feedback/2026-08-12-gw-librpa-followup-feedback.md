# GW/LibRPA 补充反馈：M1b 候选建议与边界

日期：2026-08-12（与 Power-law Heisenberg 第二份自然使用反馈同日归档）
来源：研究者对
[`2026-08-11-gw-librpa-natural-use-feedback.md`](2026-08-11-gw-librpa-natural-use-feedback.md)
的后续口头建议，随 2026-08-12 的继续开发指示一并给出
（处置见 [`docs/m1b-adjudication.md`](../docs/m1b-adjudication.md)）
Topic：`/home/bhjia/physics/GW_librpa`（`.aitp/topic/`）
协议版本：当前 M1a 命令面，`enter-0.2` / `list-0.1` / `show-0.1`

## 1. 反馈边界

这份补充反馈不是对照实验，不是 M1b gate review，也不是 freeze revision
本身；它只是研究者对第一份 GW 长 session 反馈的后续建议清单。它不声称
AITP 优于 plain files，也不声称任何行为或因果效果。它连同
[`2026-08-12-power-law-heisenberg-natural-use-feedback.md`](2026-08-12-power-law-heisenberg-natural-use-feedback.md)
一起构成 M1b 自然使用 pause 的证据输入，最终处置以
`docs/m1b-adjudication.md` 为准。

它与两份自然 session 的关系：

- 它延续 2026-08-11 GW/LibRPA 长 session 链的痛点（enter 投影过大、
  stale handoff、整库健康诊断入口缺失）；
- 它不与 Power-law Heisenberg 纠错 session 直接相关，但后者再次确认了
  “active failure 不覆盖旧 closeout handoff”的结构事实；
- 它本身不增加 session 数量：普通 session 数仍按两份自然反馈文件计。

## 2. 六项建议（忠实记录，按研究者原意）

1. **短 `enter`**——文本输出太长，希望 enter 的 text 视图更紧凑，
   便于会话开始时快速定向；JSON 机器输出不受影响。
2. **lineage / relations**——需要只读查看单条 Entry 的
   `resolves`/`supersedes` 出边与 `resolved_by`/`superseded_by` 入边，
   恢复“这条记录在关系上处于什么位置”；不要为此引入持久化
   `based_on`/`used_by`、递归图或索引。
3. **stale handoff 提示**——当 handoff 源记录的记录时间早于更新的
   unresolved active failure 时，希望 enter 文本给一个结构性的
   “请复核 handoff”信号；这是事实性提示，不改变 `next_action` 本身，
   也不是语义上的“stale”判定。
4. **malformed 诊断 + 抑制**——希望有一个独立、可复现的整库健康诊断
   入口（roster A 的只读 `check` 形态），并允许 enter 文本只保留
   warning 摘要，避免每次 enter 都被 malformed 明细淹没；不要持久化
   抑制状态。
5. **TOPIC goal 空提示**——当 `TOPIC.md` 的 Research Goal 仍是占位
   文本时，希望 enter 文本显式提示 `not_established`，并在整库诊断中
   作为 warning 出现。
6. **structured JSON/YAML prepare 输入（保留 draft）**——希望
   `record prepare` 能直接接受结构化 JSON/YAML 输入以降低写入摩擦，
   同时保留 draft 文件路径，不绕过模板与校验。

## 3. 与既有反馈的关系

- 建议 1、3、4 直接来自第一份 GW 反馈的 §4.1/§4.2/§4.6（enter 投影
  偏大、handoff 语义过时、缺少整库健康汇总入口）；
- 建议 2 是第一份 GW 反馈 §4.4 与 Power-law 反馈 §4.2 共同支持的
  窄关系视图的 read-side 收敛形式；
- 建议 5 是第一份 GW 反馈未单独列出、由后续使用补充的占位提示；
- 建议 6 是 roster E（quick record）之外的独立写入摩擦建议：它要求
  结构化输入**同时保留 draft**，因此不是 E 的简化版，而是单独候选。

## 4. 建议的采纳状态（以 adjudication 为准）

完整 A–H 与六项建议的逐项处置见 `docs/m1b-adjudication.md`；本文件
不自行裁决。概括而言：建议 1/3/4/5 的 read-side 文本与诊断部分被选入
M1b-R1 切片（实现规格 `docs/m1b-r1-spec.md`；adjudication 时点
implementation pending，R1 已于同日实现并通过 deterministic gate，见
`docs/m1b-r1-stage-notes.md`）；
建议 2（lineage/relations）曾在 freeze revision 中被选入 R1，但在
2026-08-12 预算核算中因实测余量不足被移回 deferred（记录在
`docs/m1b-adjudication.md` §3，可经新的 reviewed freeze revision 回归）；
建议 6 因证据混合、预算优先 read-side 而显式 deferred。

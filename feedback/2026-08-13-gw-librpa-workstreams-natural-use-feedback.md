# GW/LibRPA 自然使用反馈：单 store 多研究线的 workstream 观察

日期：2026-08-13  
Topic：`/home/bhjia/physics/GW_librpa`（`.aitp/topic/`）  
使用场景：ABACUS/LibRPA SOC 磁群长周期开发，fish 与 Dongfang 双远端 Slurm，数百条历史 Entry  
协议版本：M1a + 已通过 deterministic gate 的 M1b-R1（`check-0.1`、compact `enter` text）

## 1. 反馈边界

这是独立的新自然需求反馈，仍属于 2026-08-11 开始的同一条 GW/LibRPA 长会话链，不增加独立自然 session 数量。本文件只记录可观察事实：一个共享源码/build/provenance 的 store 上当前同时存在三条研究线时的可复现观察。它不是 gate、spec、freeze revision 或功能授权；不声称 AITP 优于 plain files；既有候选的正式处置仍以 `docs/archive/m1b-adjudication.md` 为准。

## 2. 可观察事实：三条研究线共享一个 store

`GW_librpa` 只有一个 `.aitp/topic/` store，全部 Entry/Note 共享同一套基础设施：

- 同一 ABACUS/LibRPA 源码树与同一构建产物（含被上游 PR #7804 推翻后重建的 binary）；
- 同一远端 Slurm 环境（fish 与 Dongfang）与同一类 pointer manifest/provenance 搬运；
- 同一 `TOPIC.md`、同一 `STORE.toml`、同一 Notes 集合。

但当前研究内容同时包含三条可区分的线：

| 线 | 内容（可观察） |
|---|---|
| crpa | 与 GW/cRPA 计算相关的结果、run、failure 与 pin |
| magnetic-symmetry | SOC 磁群对称性分析（symmetry/jhep-note 等） |
| qsgw-semiconductor | 半导体 QSGW 验证链（四材料 ABACUS/LibRPA 验证与最终 binary） |

这三条线的 critical path 不同，但记录与检索层面没有区分它们的字段：现有 Entry/Note frontmatter 中不存在 workstream 归属，`rg`/`list`/`show` 的返回都需要按行人工过滤，`summary` 文本是唯一线索。

## 3. 可观察事实：单线会话的全局恢复成本

已有反馈（2026-08-11 `feedback/2026-08-11-gw-librpa-natural-use-feedback.md` 与 2026-08-13 `feedback/2026-08-13-gw-librpa-m1b-r1-natural-use-feedback.md`）已记录 dense mixed store 与全局 handoff/failure/Note 恢复成本：

- 228 条 active Entry、46 条 superseded Entry、26 条 unresolved failure；
- `enter` 的 handoff 指向 2026-08-11 的 jobs 1355/1358/1375/1379/1380，而当前工作已进入 2026-08-13 的 PR #7804 修复与 Dongfang 最终 binary 构建；
- `latest_working_note = null`，返回会话必须依赖 `rg` + `show` + 外部 handoff 手工重建 critical path；
- `enter`/`check` 的 counts、unresolved_failures、warnings 均为 Topic 全局聚合。

本轮在同一 store 上新增的可复现观察：

- 只处理 crpa 或 magnetic-symmetry 或 qsgw-semiconductor 中某一条线的会话，仍会看到其余两条线的 unresolved failures、recent entries 与 Notes 计数；要得到单线状态必须人工忽略全局明细。
- 一条 failure 属于哪条线、一条 closeout 是否覆盖当前线、`supersedes`/`resolves` 链是否跨线，只能逐条打开记录确认；没有字段能表达"这条 Entry 属于某线"。
- 三条线共享 binary/build/provenance 时，跨线 Entry 的 refs 与 pin 是同一批文件，但语义上下文不同；全局 `check`（0.4 s、199 errors/91 targets）无法区分"我这条线"的债务与其他线的债务。
- 同一会话内跨线切换（例如磁群分析结论影响 crpa 输入）时，检索成本叠加：每换一条线就要重新过滤全局列表。

## 4. 总结

可观察事实汇总：一个共享源码/build/provenance 的 Topic store 当前同时承载 crpa、magnetic-symmetry、qsgw-semiconductor 三条研究线；记录中没有 workstream 归属字段；单线会话的 handoff/failure/Note 恢复必须经过全局过滤；既有反馈已记录该 store 的 dense mixed 特性与全局恢复成本。本文件只记录这些事实，不做实现建议，也不声称 AITP 优于 baseline。

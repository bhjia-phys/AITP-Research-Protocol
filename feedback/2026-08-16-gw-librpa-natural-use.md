# GW/LibRPA 自然使用 session 记录

- **Topic / 日期**: `GW_librpa` / 2026-08-16，工作流 `magnetic-symmetry`；九材料 PBE@GW campaign 等待最后一个 Mn3Sn G0W0 full 分支终态。
- **恢复耗时**: 运行一次 scoped `enter`、一次 scoped `check`，再核对本地 final-report 状态和远端 job 3021671，约 4 次工具调用后确认唯一缺项。
- **handoff**: `enter` 仍指向“构建 patched ABACUS 并重跑 Mn3Sn producer”，但实际冻结 campaign 已推进到最后一个 G0W0 作业；根因是后续 campaign `run` Entry 没有替换已经落后的 agent closeout。
- **漏记**: 九材料已经完成的 8/9 下游结果尚未综合成新的 working Note；`enter` 报告 latest working Note 之后有 4 条 active records，最终综合记录须等 Mn3Sn 终态后一次写入。
- **写入成本 / remote evidence**: 每个远端终态都先生成本地 pointer、remote evidence hash 与 local manifest，再由 Entry pin；当前归档脚本减少了手工步骤，但 JHEP note 持续重生成使 5 个历史 SHA pin 正常出现 `hash_mismatch`，仍需人工区分历史漂移与当前损坏。
- **检索 / 自然需求**: scoped workstream 明显缩小了恢复范围，`check --workstream` 也集中显示 5 个相关 mismatch；但 handoff 是否语义过时仍需对照 campaign report 人工判断，本轮再次出现 dense-campaign closeout/working-Note 维护需求，没有出现需要语义搜索或新 runtime 的事实。

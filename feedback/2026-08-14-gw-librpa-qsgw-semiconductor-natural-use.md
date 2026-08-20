# GW/LibRPA QSGW 半导体验证自然使用反馈（2026-08-14）

- **Topic / 日期**：`/home/bhjia/physics/GW_librpa` 的 `qsgw-semiconductor` workstream，2026-08-14；本轮是正在进行的真实半导体 QSGW 逐能带验证，不是 AITP gate 或对照实验。
- **恢复与健康状态**：`aitp check --json` 在 290 Entries / 3 Notes 上报告 201 errors / 2 warnings，而 scoped `aitp enter --workstream qsgw-semiconductor` 仍显示 `memory_status=available` 且只展示一条全局时间戳 warning；两种投影并列时不能直接判断当前 workstream 的证据是否健康。
- **历史 pin 噪声**：201 个 errors 混合了真正缺失文件与“Entry pin 指向后来继续修改的 mutable 文件”产生的 SHA mismatch；本 workstream 的 `entry-5b68...` 也因 `generated-inputs/MANIFEST.sha256` 在 producer 修复后合法更新而失配，`check` 没有区分历史快照漂移和当前证据破损。
- **handoff 已过时**：scoped `enter` 的 next action 仍是“实现并测试 producer”，但 producer 修复、S-metric gate 和 Si preflight 包已完成并通过 246 tests；根因是 durable code-change/closeout 尚未写入，handoff 不会从文件或测试状态自动更新。
- **漏记与写入成本**：当前 ledger 只有历史输入 `source` Entry，producer 合同修复、preflight 状态机、overlap analyzer 和 dongfang 只读 binary/PyATB 预检都尚未形成 durable Entry；补记前需要重新计算多个 manifest SHA，并避免把已失配的 mutable manifest 继续当作稳定 pin。
- **自然需求**：本轮真实需要 roster D 类 remote pointer/evidence manifest，以及能表达“同一 source 输入随后发生 code-change、旧 pin 仍是历史事实但当前文件已变化”的谱系；另外 installed plugin 不含 `feedback/` 模板，必须从 `installed.json` 追到 `originalSource=/home/bhjia/physics/repo/AITP-Research-Protocol` 才能写本记录。

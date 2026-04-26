# Commands

Run date: `2026-04-13`

## Public Entry

```powershell
python -m knowledge_hub.aitp_cli --kernel-root "D:/BaiduSyncdisk/repos/AITP-Research-Protocol/research/knowledge-hub" --repo-root "D:/BaiduSyncdisk/repos/AITP-Research-Protocol" bootstrap --topic "Jones von Neumann Algebras Public Entry Closure" --topic-slug "jones-von-neumann-algebras-public-entry" --statement "Start from the Jones finite-dimensional backbone and record the first honest closure target through the public entry path." --json
```

Key outputs:

- `runtime/topics/jones-von-neumann-algebras-public-entry/topic_state.json`
- `runtime/topics/jones-von-neumann-algebras-public-entry/runtime_protocol.generated.json`
- `runtime/topics/jones-von-neumann-algebras-public-entry/runtime_protocol.generated.md`
- `runtime/topics/jones-von-neumann-algebras-public-entry/research_question.contract.md`
- `runtime/topics/jones-von-neumann-algebras-public-entry/topic_dashboard.md`

Observed result:

- bootstrap succeeded
- fresh topic slug materialized
- resume stage after bootstrap: `L3`
- research mode after bootstrap: `exploratory_general`

## Bounded Loop

```powershell
python -m knowledge_hub.aitp_cli --kernel-root "D:/BaiduSyncdisk/repos/AITP-Research-Protocol/research/knowledge-hub" --repo-root "D:/BaiduSyncdisk/repos/AITP-Research-Protocol" loop --topic-slug "jones-von-neumann-algebras-public-entry" --human-request "Continue with the first bounded route and stop before expensive execution." --max-auto-steps 1 --json
```

Key outputs:

- `runtime/topics/jones-von-neumann-algebras-public-entry/loop_state.json`
- `runtime/topics/jones-von-neumann-algebras-public-entry/loop_history.jsonl`
- `runtime/topics/jones-von-neumann-algebras-public-entry/control_note.md`
- `runtime/topics/jones-von-neumann-algebras-public-entry/innovation_direction.md`

Observed result:

- loop succeeded
- entry conformance: `pass`
- exit conformance: `pass`
- capability status: `missing_trust`
- trust status: `missing`
- steering decision: `stop`
- selected bounded action remained `Convert the topic statement into explicit source and candidate artifacts.`

## Status

```powershell
python -m knowledge_hub.aitp_cli --kernel-root "D:/BaiduSyncdisk/repos/AITP-Research-Protocol/research/knowledge-hub" --repo-root "D:/BaiduSyncdisk/repos/AITP-Research-Protocol" status --topic-slug "jones-von-neumann-algebras-public-entry" --json
```

Key outputs:

- `runtime/topics/jones-von-neumann-algebras-public-entry/topic_synopsis.json`
- `runtime/topics/jones-von-neumann-algebras-public-entry/layer_graph.generated.json`
- `runtime/topics/jones-von-neumann-algebras-public-entry/protocol_manifest.active.json`

Observed result:

- current stage: `L3`
- selected action type: `l0_source_expansion`
- selected action summary: `Convert the topic statement into explicit source and candidate artifacts.`
- `protocol_manifest.overall_status`: `pass`
- `open_gap_summary.requires_l0_return`: `true`

## Replay

```powershell
python -m knowledge_hub.aitp_cli --kernel-root "D:/BaiduSyncdisk/repos/AITP-Research-Protocol/research/knowledge-hub" --repo-root "D:/BaiduSyncdisk/repos/AITP-Research-Protocol" replay-topic --topic-slug "jones-von-neumann-algebras-public-entry" --json
```

Key outputs:

- `runtime/topics/jones-von-neumann-algebras-public-entry/topic_replay_bundle.json`
- `runtime/topics/jones-von-neumann-algebras-public-entry/topic_replay_bundle.md`

Observed result:

- route choice status: `no_choice`
- route transition gate status: `blocked`
- topic completion status: `not_assessed`
- authoritative current runtime surfaces were materialized through the public
  front door

# Commands

## Real-Kernel Proof Command

```powershell
python research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py --package-root D:\BaiduSyncdisk\repos\AITP-Research-Protocol\research\knowledge-hub --repo-root D:\BaiduSyncdisk\repos\AITP-Research-Protocol --use-package-root-as-kernel --topic-slug jones-chapter-4-source-registration-proof-20260413 --register-arxiv-id 2401.00001v2 --registration-metadata-json D:\BaiduSyncdisk\repos\AITP-Research-Protocol\.planning\phases\166.1-contentful-source-registration-default\evidence\jones-chapter-4-source-registration-proof-20260413\metadata.json --json
```

## Fixture Inputs

- `paper.tex` -> bounded local TeX fixture for the proof lane
- `source.tar` -> tar archive consumed through `source_url`
- `metadata.json` -> deterministic registration override pointing to the local
  tar fixture

## Output Receipt

- `proof.json` -> full bootstrap / loop / status / registration receipt

## Key Result

- fresh topic slug:
  `jones-chapter-4-source-registration-proof-20260413`
- selected action summary contained:
  `discover_and_register.py` and `register_arxiv_source.py`
- registration finished with:
  - `download_status = downloaded`
  - `extraction_status = extracted`

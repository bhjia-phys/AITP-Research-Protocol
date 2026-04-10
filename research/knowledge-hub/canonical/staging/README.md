# L2 staging surfaces

This directory stores provisional `L2`-adjacent material that is explicitly not
yet canonical `L2`.

Key surfaces:

- `workspace_staging_manifest.json`
- `workspace_staging_manifest.md`
- `entries/*.json`
- `entries/*.md`

Regenerate the manifest with:

```bash
python research/knowledge-hub/runtime/scripts/sync_l2_staging_manifest.py
```

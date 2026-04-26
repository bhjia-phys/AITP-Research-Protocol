# Phase 131: Package Identity And Distribution Asset Contract - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md.

**Date:** 2026-04-11
**Phase:** 131-package-identity-and-distribution-asset-contract
**Areas discussed:** public package identity, version source of truth, packaged asset boundary

---

## Public Package Identity

| Option | Description | Selected |
|--------|-------------|----------|
| Publish under an available PyPI name | Match the public-package goal honestly | ✓ |
| Keep an unpublishable target name | Preserve wording but block release | |
| Split multiple public distributions now | Expand scope into repo decomposition | |

**Selection rationale:** `aitp` is already occupied on PyPI, so the public
package identity needs a publishable fallback; the implementation now uses
`aitp-kernel`.

---

## Version Source Of Truth

| Option | Description | Selected |
|--------|-------------|----------|
| Single-source semver | `--version`, wheel metadata, and doctor agree | ✓ |
| Keep duplicated literals | Fastest local patch but drifts easily | |
| Hide version from CLI for now | Avoids immediate cleanup but weakens release contract | |

**Selection rationale:** Public release work needs one semver source that all
install surfaces agree on.

---

## Packaged Asset Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Ship required runtime assets in the distribution | Installed wheel can run outside editable checkout | ✓ |
| Keep editable-install assumptions | Simpler diff but fails the milestone goal | |
| Package only the Python modules | Leaves runtime docs/scripts unavailable after install | |

**Selection rationale:** The whole point of the milestone is to stop treating a
git checkout as the default runtime dependency.

---

## Deferred Ideas

- newcomer doc rewrite and migration polish belong to Phase `132`
- final clean-install closure evidence belongs to Phase `133`

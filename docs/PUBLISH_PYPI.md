# Publish AITP To PyPI

> **Status:** `aitp-kernel` is not yet published to PyPI. The packaging pipeline
> described below is the planned workflow. Currently, AITP is installed directly
> from the git repo via `python scripts/aitp-pm.py install`.

Use this runbook when you want to ship a new public `aitp-kernel` release.

## Preconditions

- working tree is clean
- `research/knowledge-hub/knowledge_hub/_version.py` has the intended semver
- the packaging contract and install docs for that version are already merged

## 1. Build prerequisites

```bash
python -m pip install --upgrade build twine
```

## 2. Run packaging verification

```bash
python research/knowledge-hub/runtime/scripts/run_dependency_contract_acceptance.py --json
python research/knowledge-hub/runtime/scripts/run_public_install_smoke.py --json
```

This should produce a successful wheel/sdist validation for `aitp-kernel` and a
clean-install smoke pass through the installed `aitp` CLI.

## 3. Build distributions

```bash
python -m build research/knowledge-hub
```

Expected artifacts:

- `research/knowledge-hub/dist/aitp_kernel-<version>-py3-none-any.whl`
- `research/knowledge-hub/dist/aitp_kernel-<version>.tar.gz`

## 4. Check distribution metadata

```bash
python -m twine check research/knowledge-hub/dist/*
```

## 5. Upload

TestPyPI first when you want a dry run:

```bash
python -m twine upload --repository testpypi research/knowledge-hub/dist/*
```

Production PyPI:

```bash
python -m twine upload research/knowledge-hub/dist/*
```

## 6. Post-publish smoke check

In a clean Python 3.10+ environment:

```bash
python -m pip install aitp-kernel
aitp --version
aitp doctor
```

If the release is meant to unlock a runtime adapter path, also verify the
relevant adapter doc once against the published package.

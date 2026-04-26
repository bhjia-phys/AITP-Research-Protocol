# Phase 131 Summary

Status: implemented on `main`

## Goal

Establish the package identity, semver source of truth, and distribution asset
contract behind the future public `pip install aitp-kernel` path.

## What Landed

- the public distribution now builds as `aitp-kernel` through
  `research/knowledge-hub/setup.py` plus a new
  [pyproject.toml](D:\BaiduSyncdisk\repos\AITP-Research-Protocol\research\knowledge-hub\pyproject.toml)
- a new bundled-kernel build path in
  `research/knowledge-hub/knowledge_hub/bundle_support.py` plus default
  materialization into a writable user kernel root outside editable install
- one single-source semver path through `knowledge_hub/_version.py`,
  `aitp --version`, and doctor package reporting

## Outcome

Phase `131` is complete.
`v1.66` now has a real package/distribution contract instead of only an
editable-install kernel identity.

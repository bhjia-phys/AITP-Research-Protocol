# Roadmap: v1.66 PyPI Publishable Package

## Result

`v1.66` is complete.

## Phases

- [x] **Phase 131: Package Identity And Distribution Asset Contract**
- [x] **Phase 132: PyPI Install Surface And Migration**
- [x] **Phase 133: Closure And Clean-Install Audit**

## Target Outcome

- one public package name that installs without repo-local editable
  paths
- one distribution contract that ships the runtime assets and surfaces one
  shared semver through `aitp --version`
- one migration and verification surface that keeps editable installs available
  for contributors while making PyPI the default newcomer path
- one real clean-install smoke path that proves the package works in an
  isolated virtualenv instead of only through repo-local development flows

## Next Step

Select the next milestone from backlog without reopening `999.48` through
`999.51` as substitute work.

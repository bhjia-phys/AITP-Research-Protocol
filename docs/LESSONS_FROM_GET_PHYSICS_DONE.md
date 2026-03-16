# Lessons From `get-physics-done`

Source studied:

- repository README: <https://github.com/psi-oss/get-physics-done>

## Why It Matters For AITP

`get-physics-done` is not the same project as AITP.

Its main emphasis is a productized multi-runtime physics copilot with a large
command surface, project folders, milestone and phase management, and unified
installation. AITP is narrower and more protocol-governed: the point is to make
AI research participation auditable, layer-aware, and non-black-box.

Even so, there are several things worth learning from it.

## Strong Ideas We Should Borrow

### 1. One public install story

GPD gives users a single install entrypoint and then asks them to pick the
runtime. That is better than asking users to manually assemble config files.

AITP should mirror this principle:

- clone repo
- install runtime
- install chosen adapter
- enter through AITP commands

This is exactly why the public AITP repo now includes an installable runtime
package instead of only docs and reference assets.

### 2. Runtime matrix as a first-class product surface

GPD treats Claude Code, Codex, Gemini CLI, and OpenCode as a supported runtime
matrix, not as afterthoughts.

That is useful for AITP because your real goal is protocol portability across:

- OpenClaw
- Codex
- Claude Code
- OpenCode

The lesson is not “copy all of GPD’s commands”. The lesson is: make runtime
support explicit, versioned, tested, and documented.

### 3. Local versus global install modes

GPD is very explicit about local and global installation targets.

AITP should keep doing the same:

- user-scope install for personal runtime config
- project-scope install for repo-local reproducibility
- explicit path overrides for testing and CI

This helps both reproducibility and onboarding.

### 4. Productized command prefixes

GPD gives each runtime a runtime-native command prefix and keeps the workflow
conceptually aligned across them.

AITP should keep the workflow aligned too, even when syntax differs:

- enter through `aitp loop` or a hard wrapper
- inspect runtime artifacts
- execute bounded work
- close with audits and trust gates

### 5. Public packaging discipline

GPD ships as a real package with tests, changelog, and a clear distribution
story.

This matters for AITP because the public repo should not remain only a design
manifesto. If the repo claims installability, it needs:

- a package
- tests
- versioning
- docs that match the install path

## What AITP Should Not Copy Blindly

### 1. A huge command catalog as the center of truth

GPD exposes a large in-runtime command surface.

AITP should be more conservative. The center of truth should remain:

- charter
- contracts
- human-readable runtime state
- conformance and trust gates

Commands are entrypoints, not the ontology.

### 2. Project/milestone/phase structure as the main research abstraction

GPD’s milestone and phase system is useful for long-horizon project management.
But AITP’s central abstraction is different:

- L0-L4 research layers
- candidate formation versus validation
- promotion or rejection
- reusable operation trust

AITP can borrow project-management convenience, but should not replace the
layered research ontology with a generic phase manager.

### 3. Verification as only a workflow stage

GPD has a clean formulate-plan-execute-verify story.

AITP needs something stricter for theoretical physics:

- validation and rejection are not just a final stage
- they are first-class durable artifacts
- they feed back into whether knowledge becomes L2 or stays exploratory

This is especially important for derivations, toy-model studies, and
first-principles numerical pipelines.

## Concrete Takeaways For AITP

Short-term:

- keep the fresh-clone install path simple
- keep runtime-specific docs symmetric
- add multi-runtime smoke tests
- keep command names and entry rules consistent

Medium-term:

- add a true one-shot bootstrap installer for all runtimes
- make OpenClaw and OpenCode wrappers harder, closer to `aitp-codex`
- publish a supported-runtime matrix with tested versions
- add release notes and compatibility notes

Long-term:

- preserve AITP’s L0-L4 ontology
- keep human-auditable notes mandatory at L2, L3, and L4
- use productization lessons from GPD without giving up protocol-first governance

## Bottom Line

GPD is stronger than current public AITP in product packaging and runtime
distribution.

AITP is stronger in protocol governance, layer semantics, and explicit
trust/conformance framing.

The right move is not to turn AITP into GPD. The right move is to combine:

- GPD’s installability and runtime product discipline
- AITP’s charter, contracts, trust gates, and human-auditable research layers

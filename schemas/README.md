# Public protocol schemas

This directory contains the public protocol schemas for AITP.

Use `schemas/` for contracts that are part of the repository-level public
interface between agents, adapters, and durable research artifacts.

## Mirror rule

If the installable runtime consumes one of these contracts directly, it should
be mirrored into `research/knowledge-hub/schemas/`.

The root copy remains the public authority.
The runtime mirror should stay JSON-equivalent to the root schema so contract
drift is reviewable.

## Boundary rule

Keep a schema here when it is part of the public protocol surface even if the
runtime package is not the only consumer.

Do not move runtime-only schemas here just to make the tree look uniform.
Runtime-only package contracts should remain under
`research/knowledge-hub/schemas/` or other runtime-local schema folders.

# Reference Runtime Boundary

This repository is protocol-first.

The reference runtime should remain minimal and should only be trusted to do
the following:

- materialize protocol and state artifacts;
- build deterministic projections;
- run conformance, capability, and trust audits;
- execute explicit tool handlers;
- expose a thin `aitp` CLI and optional `aitp-mcp` surface.

It should not become the hidden source of scientific judgment.

The larger integration workspace may contain a richer implementation, but the
public runtime boundary should remain narrow enough that the protocol stays in
charge.

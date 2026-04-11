# Runtime schema mirrors and package-local contracts

This directory contains the installable runtime schema surface.

It serves two roles:

- public contract mirrors that the runtime package consumes directly
- runtime-local schemas that belong only to the installable package

## Mirror rule

When a schema here mirrors a public contract from the repository root, it must match the root copy.

The root `schemas/` tree remains the public authority.
This package tree exists so the installed runtime can ship the same shared
contracts without depending on repository-relative paths.

## Boundary rule

Keep runtime-local schemas here when they describe package-owned storage,
compiled projections, or runtime-only control surfaces that are not themselves
repository-level public protocol contracts.

# Context Loading

## Problem

If AITP is treated as a giant prompt, the context becomes bloated and fragile.

## Required loading strategy

AITP should load context in layers:

1. **Short charter**
   - the stable high-level constraints
2. **Topic-local runtime protocol bundle**
   - current topic, current layer, current decisions, current missing pieces
3. **Step-local contracts**
   - derivation, validation, operation, or promotion contracts only when needed
4. **Evidence artifacts**
   - source snapshots, validation results, or notes only when directly relevant

## What should not happen

Agents should not:

- stuff the entire repository into context,
- rely on long chat history as state memory,
- reload all contract families for every step.

## Design consequence

The runtime should prefer:

- short summary artifacts,
- contract pointers,
- explicit load order,
- on-disk state over conversational memory.

This is how AITP stays rigorous without turning into a context-length trap.

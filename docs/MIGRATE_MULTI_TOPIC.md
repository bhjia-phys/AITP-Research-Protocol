# Migrate To The Multi-Topic Runtime

Status: active

This guide explains how to think about the v1.3 multi-topic runtime if you were
used to the older single-topic model.

## 1. What changed

Previously, operators often treated:

- `runtime/current_topic.json`

as the main durable runtime state for topic selection.

Now the authoritative source is:

- `runtime/active_topics.json`

while:

- `runtime/current_topic.json`

remains as the focused-topic compatibility projection.

## 2. The mental model change

Old model:

- one active topic
- current-topic memory is the truth
- latest-topic fallback often decides what to resume

New model:

- many active topics may coexist in one workspace
- the registry is the truth
- one topic may still be focused
- scheduler chooses only when the operator does not name a topic

## 3. What old workflows still keep working

These continue to work:

- `aitp current-topic`
- `继续这个 topic`
- explicit `--topic-slug`
- opening a new topic with natural language

The important difference is that current-topic behavior now resolves through the
registry-backed focus state when possible.

## 4. What to use now

Use these commands when you want explicit control:

```bash
aitp topics
aitp focus-topic --topic-slug <topic_slug>
aitp pause-topic --topic-slug <topic_slug>
aitp resume-topic --topic-slug <topic_slug>
```

Use these dependency commands when work must remain sequential:

```bash
aitp block-topic --topic-slug <topic_slug> --blocked-by <other_topic_slug> --reason "<reason>"
aitp unblock-topic --topic-slug <topic_slug> --blocked-by <other_topic_slug>
aitp clear-topic-dependencies --topic-slug <topic_slug>
```

## 5. Safe migration rule

If you previously relied on "whatever topic I touched last becomes the one that
AITP will resume", stop relying on that.

Instead:

- inspect `aitp topics`
- set focus explicitly when needed
- rely on scheduler fallback only when you really want AITP to choose

## 6. What you do not need to migrate manually

You do **not** need to rewrite old topic directories.

The runtime can bootstrap registry rows from known topic runtime state and keep
projecting the focused topic back into `current_topic.json` for compatibility.

## 7. When to stop and inspect

If a topic is not being selected when you expected it to be, check:

1. `aitp topics`
2. whether it is paused
3. whether it is dependency-blocked
4. whether another topic has higher priority or current focus

That is the intended debugging surface for v1.3.

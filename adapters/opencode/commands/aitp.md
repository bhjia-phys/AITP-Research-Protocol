---
description: Enter the AITP runtime for a new or existing research task
subtask: false
---
# aitp Command

Before doing substantial work, read `./AITP_COMMAND_HARNESS.md`.

User request: $ARGUMENTS

1. If the topic already exists, run `aitp resume --topic-slug <topic_slug> --human-request "$ARGUMENTS"`.
2. If the topic is new, run `aitp bootstrap --topic "<topic>" --statement "$ARGUMENTS"`.
3. Read the generated runtime artifacts before continuing.

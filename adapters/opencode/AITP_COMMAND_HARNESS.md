# AITP Command Harness

These OpenCode commands route work through the installed `aitp` CLI instead of
letting topic work drift into ad hoc browsing.

Required pattern:

1. enter through `aitp bootstrap`, `aitp resume`, or `aitp loop`
2. inspect `runtime_protocol.generated.md` and the other generated runtime artifacts
3. register reusable operations when needed
4. do the actual work
5. close with `aitp audit --phase exit`

# Hermes Improvements Inbox

## Inbox
-

## Triaged
-

## Done
- [v0] Spec freeze

## Inbox
- [v0.1] Hide or separately account for `.hermes-managed` in git_status artifacts. Current v0 writes the marker inside the worktree for cleanup safety, so `git_status.txt` shows `?? .hermes-managed` even when no task files were modified.
- [v0.1] Wire task codex.effort into actual Codex CLI config. Current state.json records `codex.effort`, but observed Codex stderr may use the global/default reasoning effort instead.

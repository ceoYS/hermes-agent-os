Implement a portable Hermes v0.1 smoke test script.

Read first:
- hermes.py
- README.md
- docs/ROADMAP.md
- docs/AGENT_RULE_GOVERNANCE.md
- prompts/hermes-v0.1-kernel-hardening.md

Scope:
1. Add `scripts/smoke_v0_1.sh`.
2. The script must create a temporary Git repo under `/tmp/hermes-v01-smoke-repo`.
3. The script must create a temporary task file under `/tmp/hermes-v01-smoke-task.yaml`.
4. The task must use:
   - repo_path: /tmp/hermes-v01-smoke-repo
   - runs_root: /tmp/hermes-v01-smoke-runs
   - allow_edits: false
   - allow_push: false
   - allow_draft_pr: false
   - codex.sandbox: read-only
5. The script must run:
   - python3 -m py_compile hermes.py
   - python3 hermes.py --help
   - python3 hermes.py validate /tmp/hermes-v01-smoke-task.yaml
   - python3 hermes.py dry-run /tmp/hermes-v01-smoke-task.yaml
   - python3 hermes.py run /tmp/hermes-v01-smoke-task.yaml --no-codex
   - python3 hermes.py list --runs-root /tmp/hermes-v01-smoke-runs
   - python3 hermes.py status <latest_run_id> --runs-root /tmp/hermes-v01-smoke-runs
   - python3 hermes.py cleanup --dry-run --older-than 1m --runs-root /tmp/hermes-v01-smoke-runs
6. The script must verify:
   - git_status_raw.txt contains `.hermes-managed`
   - git_status.txt does not contain `.hermes-managed`
   - git_diff.patch is empty
   - git_branch_diff.patch is empty
7. Update README.md to prefer `bash scripts/smoke_v0_1.sh` for portable local smoke testing.
8. Do not run nested Codex.
9. Do not implement v0.2 Crack-lite.
10. Do not add Nous Hermes, PLUR, RTK, hermesd, or Telegram integration.
11. Do not push, merge, or deploy.

Acceptance commands:
- bash scripts/smoke_v0_1.sh
- git diff --stat
- git status --short

After implementation:
- Show changed files and stop.

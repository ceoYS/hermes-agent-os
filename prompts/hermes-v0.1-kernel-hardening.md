Implement Hermes Agent OS v0.1 kernel hardening.

Read first:
- hermes.py
- README.md
- docs/REFERENCE_STACK.md
- docs/ROADMAP.md
- docs/V0_2_CRACK_LITE_PLAN.md
- docs/AGENT_RULE_GOVERNANCE.md
- prompts/hermes-v0-implementation.md
- examples/trader-review.yaml

First, verify whether the newly added docs contain shell paste artifacts such as stray EOF text or corrupted fragments. If found, fix only those obvious artifacts while preserving the intended meaning.

Scope:
1. Wire task.codex.effort into the actual nested Codex CLI invocation.
   - Use Codex CLI config override: -c model_reasoning_effort="<effort>".
   - Preserve task.codex.model.
   - Preserve task.codex.sandbox.
   - Continue rejecting danger-full-access.
   - Do not weaken any existing safety policy.

2. Split git status artifacts into raw and filtered forms.
   - Preserve raw status as git_status_raw.txt.
   - Create filtered status as git_status.txt.
   - Filter only the Hermes marker `.hermes-managed`.
   - Do not hide any other untracked or modified files.

3. Add `list` command.
   - Read `{runs_root}/journal.jsonl`.
   - Show recent runs with run_id, task_id, status, duration_seconds, codex_exit_code, estimated_input_tokens.
   - Keep it simple.

4. Add `status <run_id>` command.
   - Locate matching run under runs_root.
   - Read state.json.
   - Print a concise summary:
     - run_id
     - task_id
     - status
     - created_at / updated_at
     - repo_path
     - worktree_path
     - base_commit
     - branch
     - codex exit_code / timed_out / estimated_input_tokens
     - warnings / errors count
     - output file paths.

5. Update README.md with v0.1 smoke test commands.

6. Preserve existing v0 behavior:
   - validate
   - dry-run
   - run --no-codex
   - run --execute
   - cleanup

7. Preserve safety:
   - no automatic push
   - no automatic merge
   - no automatic deploy
   - no draft PR in v0/v0.1
   - no danger-full-access
   - no broad file deletion
   - cleanup must only remove Hermes-owned run dirs.

Non-scope:
- Do not implement v0.2 Crack-lite yet.
- Do not add Nous Hermes integration.
- Do not add PLUR.
- Do not add RTK integration.
- Do not add hermesd or Hermes Desktop integration.
- Do not add parallel execution.
- Do not push.
- Do not merge.
- Do not deploy.

Company PC execution rule:
- Do not run `python3 hermes.py run ... --execute` in this session.
- Run only local/non-nested smoke tests unless explicitly asked later.

Acceptance commands to run:
- python3 -m py_compile hermes.py
- python3 hermes.py --help
- python3 hermes.py validate examples/trader-review.yaml
- python3 hermes.py dry-run examples/trader-review.yaml
- python3 hermes.py run examples/trader-review.yaml --no-codex
- python3 hermes.py list
- python3 hermes.py status <latest_run_id>
- python3 hermes.py cleanup --dry-run --older-than 1m

After implementation:
- Show git diff --stat.
- Show changed files.
- Stop.

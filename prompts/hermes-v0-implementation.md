Implement Hermes v0 as a minimal local Python CLI.

Goal:
Build a single-task runner that reads one task.yaml, validates it, creates an isolated git worktree from an explicit base branch, builds prompt.md, optionally runs codex exec, captures logs, saves git status/diff/commits, appends journal.jsonl, and writes state.json.

Do not build a framework.
Do not add model routing.
Do not add parallel execution.
Do not add Obsidian.
Do not add Figma.
Do not add SNS.
Do not add GitHub PR creation.
Do not push to remote.
Do not merge.
Do not deploy.

Current repository:
- Implement everything in hermes.py.
- Keep v0 simple and self-contained.
- Use Python standard library where possible.
- PyYAML is allowed only if already installed. If missing, print a clear error telling the user to install pyyaml.
- Do not create a package structure yet.
- Do not create extra modules yet.

Commands:
- python3 hermes.py --help
- python3 hermes.py validate task.yaml
- python3 hermes.py dry-run task.yaml
- python3 hermes.py run task.yaml --no-codex
- python3 hermes.py run task.yaml --execute
- python3 hermes.py cleanup --dry-run --older-than 7d
- python3 hermes.py cleanup --older-than 7d

Required task.yaml fields:
- id
- repo_path
- base_branch
- branch_prefix
- runs_root
- risk_level
- task_type
- allow_edits
- allow_push
- allow_draft_pr
- codex.model
- codex.effort
- codex.sandbox
- codex.timeout_minutes
- limits.max_context_chars
- limits.max_prompt_chars
- limits.max_stdout_mb
- limits.max_stderr_mb
- context_files
- objective
- acceptance_criteria

Validation order:
1. Schema validation.
2. Risk policy enforcement.
3. Verify repo_path exists.
4. Verify repo_path is a git repo.
5. If --execute is specified, run `codex --version` with timeout 10s before any worktree creation.
6. If --execute is specified, run `codex exec --help` before any worktree creation and later write output to hermes.log.
7. Verify base_branch exists with:
   `git -C <repo_path> rev-parse --verify <base_branch>`
8. Resolve base_commit with:
   `git -C <repo_path> rev-parse <base_branch>`
9. Dirty repo check with:
   `git -C <repo_path> status --porcelain`
   Fail if dirty.
10. Validate context_files:
   - relative paths only
   - no absolute paths
   - no `../`
   - no forbidden patterns
11. Validate each context file from base_commit:
   - use `git -C <repo_path> ls-tree <base_commit> -- <path>`
   - reject missing files
   - reject symlink mode 120000
   - use `git -C <repo_path> show <base_commit>:<path>` to read contents
12. Enforce limits.max_context_chars.
13. Build prompt text in memory.
14. Enforce limits.max_prompt_chars.
15. Estimate input tokens as `ceil(len(prompt_text) / 2)`.
    Add a code comment that this is intentionally conservative for Korean/CJK-heavy prompts.
16. Generate run_id, branch, run_dir, worktree_path.
17. Check branch conflict before worktree creation:
    `git -C <repo_path> rev-parse --verify refs/heads/<branch>`
    This command MUST fail. If it succeeds, abort with exit code 5.
18. Only after all validation passes, create run_dir and worktree.

Run ID:
- Generate run_id automatically as `{task_id}-{YYYYMMDD-HHMMSS}`.
- Derive branch as `{branch_prefix}-{YYYYMMDD-HHMMSS}`.
- Derive run_dir as `{runs_root}/{run_id}`.
- Derive worktree_path as `{run_dir}/worktree`.
- Do not allow user-supplied run_id in v0.
- Use local time.

Worktree:
- Use exactly:
  `git -C <repo_path> worktree add <worktree_path> -b <branch> <base_branch>`
- Record base_commit in state.json and hermes.log.
- Do not fetch automatically in v0.
- After git worktree add succeeds, write:
  `{worktree_path}/.hermes-managed`
- The marker file must include:
  - run_id
  - created_at
  - branch
  - base_commit

Risk policy:
- risk_level is an enforced policy key, not a label.
- If risk_level=critical:
  - task_type must be review
  - allow_edits must be false
  - allow_push must be false
  - allow_draft_pr must be false
  - codex.sandbox must be read-only
- For all risk levels:
  - allow_push must be false in v0
  - allow_draft_pr must be false in v0
  - codex.sandbox must be either read-only or workspace-write
- Reject danger-full-access in v0.
- Never silently override invalid config. Fail validation.

Prompt template:
- Always include:
  - task id
  - mode
  - objective
  - acceptance criteria
  - constraints
  - base branch
  - base commit
  - context file contents
- If allow_edits=false:
  - explicitly say review only
  - do not modify files
  - do not create commits
  - do not push
  - do not create PR
  - output findings to stdout
- If allow_edits=true:
  - explicitly say implementation
  - may edit files inside worktree
  - do not commit unless objective explicitly requires
  - do not push
  - do not create PR
- Record prompt_template in state.json:
  - review.v0 if task_type=review or allow_edits=false
  - implementation.v0 if allow_edits=true

Codex execution:
- Only run Codex when --execute is passed.
- Use this base command:
  `codex exec --model <model> --sandbox <sandbox> -`
- Pass prompt via stdin.
- Do not pass prompt as a long argv string.
- Do not use shell=True.
- Use subprocess.Popen, not subprocess.run(capture_output=True).
- Redirect stdout/stderr to files:
  - codex_stdout.log
  - codex_stderr.log
- Use timeout.
- Use text=True, encoding="utf-8", errors="replace".
- All file I/O must use encoding="utf-8", errors="replace".
- On timeout:
  - kill process
  - status=failed
  - codex.exit_code=3
  - preserve worktree
  - preserve partial stdout/stderr files
  - exit code 3

Important Codex sandbox note:
- The installed Codex CLI supports `--sandbox <read-only|workspace-write|danger-full-access>`.
- Hermes v0 must pass `--sandbox <task.codex.sandbox>` when running nested Codex.
- Hermes v0 must reject `danger-full-access`.
- Do not use `--dangerously-bypass-approvals-and-sandbox`.

Resource limits:
- Start a watchdog while Codex is running.
- Every 5 seconds, check codex_stdout.log and codex_stderr.log size.
- If stdout exceeds limits.max_stdout_mb:
  - kill Codex
  - status=failed
  - add error
  - exit code 3
- If stderr exceeds limits.max_stderr_mb:
  - kill Codex
  - status=failed
  - add error
  - exit code 3

State:
- Write state.json after every stage.
- state.json must include schema_version=1.
- Fields:
  - schema_version
  - run_id
  - task_id
  - status
  - created_at
  - updated_at
  - repo_path
  - run_dir
  - worktree_path
  - base_branch
  - base_commit
  - branch
  - risk_level
  - task_type
  - allow_edits
  - allow_push
  - allow_draft_pr
  - prompt_template
  - codex model/effort/sandbox/timeout/exit_code/timed_out/estimated_input_tokens
  - environment
  - errors
  - warnings
  - output file paths

Environment capture:
- state.json must include:
  - hermes_version
  - schema_version
  - command_line
  - python_version
  - codex_version from `codex --version` if available
  - git_version from `git --version`
  - hostname
  - user
  - started_in_cwd

Statuses:
- created
- validated
- run_dir_created
- worktree_created
- prompt_built
- running_codex
- codex_completed
- collecting_git_outputs
- completed
- completed_with_warnings
- failed

Logging:
- Write Hermes internal logs to hermes.log.
- Save a copy of task.yaml to run_dir/task.yaml.
- Save prompt.md to run_dir/prompt.md.
- Save codex stdout/stderr to files.
- If `codex exec --help` was run, write its output to hermes.log.
- Log all Git commands before running them.

Git outputs:
- Save:
  - git_status.txt from `git status --short`
  - git_diff_stat.txt from `git diff --stat`
  - git_diff.patch from `git diff`
  - git_commits_since_base.txt from `git log --oneline <base_commit>..HEAD`
  - git_branch_diff.patch from `git diff <base_commit>...HEAD`
- Run these Git output commands inside worktree_path.
- If commits exist and the task did not explicitly require commits, mark completed_with_warnings.

Run journal:
- Append one JSON object line to `{runs_root}/journal.jsonl` after every run, success or failure.
- Fields:
  - schema_version
  - run_id
  - task_id
  - status
  - started_at
  - duration_seconds
  - codex_exit_code
  - estimated_input_tokens
  - warnings_count
- Use UTF-8.
- Use append mode.
- Write one complete line ending with newline.
- Flush and fsync after append.

Forbidden context patterns:
- .env
- .env.*
- secrets.*
- credentials.*
- *.pem
- *.key
- *.p12
- *.pfx
- id_rsa
- id_ed25519
- node_modules
- .venv
- .git
- .ssh
- .aws
- .gnupg

Path validation:
- Use pathlib.
- Reject absolute context file paths.
- Reject any path containing `..`.
- Reject forbidden patterns by matching each path component and the full relative path.
- Reject symlinks via git object mode 120000 before worktree creation.

Exit codes:
- 0 success
- 1 general failure
- 2 validation failure
- 3 codex failure or timeout
- 4 git operation failure
- 5 safety policy violation

Cleanup safety:
- cleanup --older-than 7d must only remove directories that pass is_hermes_run_dir().
- is_hermes_run_dir must verify:
  - state.json exists
  - state.json["schema_version"] == 1
  - state.json["run_id"] exists
  - state.json["worktree_path"] is inside run_dir using pathlib Path.resolve() + relative_to(), not string startswith
  - {worktree_path}/.hermes-managed exists
  - .hermes-managed contains the same run_id
- Directories without valid state.json or marker are skipped silently.
- For each Hermes run dir to clean:
  1. Run `git -C <repo_path> worktree remove <worktree_path> --force`
  2. Then remove the run directory itself
- Never remove a worktree with rm/rmtree unless `git worktree remove` succeeded or the worktree path no longer exists.
- Never delete run directories that fail Hermes ownership checks.

Dry run:
- dry-run must create no run_dir and no worktree.
- It should print:
  - planned run_id
  - branch
  - run_dir
  - worktree_path
  - base_commit
  - context file list
  - prompt size estimate
  - estimated input tokens
  - whether codex pre-flight would be needed

IMPROVEMENTS.md:
- Create IMPROVEMENTS.md if missing.
- Do not auto-edit it after every run in v0.
- Include initial sections if file is missing:
  - Inbox
  - Triaged
  - Done

Acceptance criteria:
- `python3 hermes.py --help` works.
- `python3 hermes.py validate examples/trader-review.yaml` works.
- validate catches missing required fields.
- validate fails on dirty repo.
- validate fails on missing base_branch.
- validate fails on risk policy mismatch.
- validate fails on forbidden context file.
- validate fails on symlink context file.
- validate checks prompt size before creating worktree.
- dry-run creates no run_dir and no worktree.
- run --no-codex creates run_dir, worktree, state.json, hermes.log, prompt.md, .hermes-managed.
- run --execute calls codex exec exactly once via stdin.
- timeout marks state failed and preserves partial stdout/stderr.
- stdout/stderr size limit kills Codex and marks failed.
- git outputs are saved.
- journal.jsonl is appended on success and failure.
- cleanup only deletes Hermes-owned run dirs and uses git worktree remove first.
- no push, PR, merge, deploy, or danger-full-access is possible.

After implementation:
- Do not run --execute automatically.
- Run only:
  - python3 hermes.py --help
  - python3 hermes.py validate examples/trader-review.yaml
  - python3 hermes.py dry-run examples/trader-review.yaml
- Show the results and stop.
